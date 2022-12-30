from django.contrib import auth
from django.db.models import Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from foods.models import (Favorite, Follow, Ingredient, IngredientsAmount,
                          PurchaseList, Recipe, Tag)
from knox.auth import AuthToken
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import (ChangePasswordSerializer, FollowSerializer,
                          IngredientSerializer, RecipeListRetrieveSerializer,
                          RecipePostUpdateSerializer, RecipePurchaseSerializer,
                          TagSerializer, UserLoginSerializers, UserSerializer)

User = auth.get_user_model()


@api_view(['POST'])
def login_api(request):
    serializer = UserLoginSerializers(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    user = get_object_or_404(User, email=email)
    _, token = AuthToken.objects.create(user)

    return Response({
        'auth_token': token
    })


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    lookup_field = 'id'
    search_fields = ('id',)

    @action(methods=('GET',),
            url_path='me',
            detail=False, )
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class ChangePasswordViewSet(viewsets.ModelViewSet):
    serializer_class = ChangePasswordSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.get("current_password")
        if not auth.authenticate(username=user.username, password=password):
            return Response({"current_password": ["Wrong password."]},
                            status=status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.save()
        return HttpResponse(status=204)


class SetPermissionsFiltersSearchFields(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if name:
            search_queryset = list(
                self.queryset.filter(name__istartswith=name)
            )
            count_queryset = self.queryset.filter(name__contains=name)
            search_queryset.extend(
                [i for i in count_queryset if i not in search_queryset]
            )
            self.queryset = search_queryset
        return self.queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListRetrieveSerializer
        return RecipePostUpdateSerializer

    def get_queryset(self):
        tags = self.request.query_params.getlist('tags')
        if tags:
            self.queryset = self.queryset.filter(
                tags__slug__in=tags).distinct()

        author = self.request.query_params.get('author')
        if author:
            self.queryset = self.queryset.filter(author=author)

        # Следующие фильтры только для авторизованного пользователя
        user = self.request.user
        if not user.is_anonymous:
            true_condition = ['1', 'true']
            is_in_shopping = self.request.query_params.get(
                'is_in_shopping_cart'
            )

            if is_in_shopping is not None:
                self.queryset = self.queryset.filter(
                    recipe_cart__isnull=is_in_shopping not in true_condition
                )

            is_favorited = self.request.query_params.get('is_favorited')
            if is_favorited is not None:
                self.queryset = self.queryset.filter(
                    favorite__isnull=is_favorited not in true_condition
                )

        return self.queryset

    @action(
        methods=('GET',),
        url_path='download_shopping_cart',
        detail=False,
    )
    def download_shopping_cart(self, request):
        user = request.user
        bubbba = IngredientsAmount.objects.filter(
            recipe__recipe_cart__user=user).values(
            'recipe__ingredients__name').annotate(
            purchase_amount=Sum('amount'))
        return FileResponse(
            bubbba,
            content_type="text/plain",
            as_attachment=True,
            filename="purchase_list.txt",
        )

    @action(
        methods=('POST', 'DELETE'),
        detail=True
    )
    def favorite(self, request, pk):
        user = request.user
        favorite_data = {'user': user, 'recipe_id': pk}
        try:
            favorite = Favorite.objects.get(**favorite_data)
            favorite.delete()
        except Exception:
            favorite = Favorite(**favorite_data)
            favorite.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CartAndFavoritesMixin:
    def create(self, request, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        PurchaseList.objects.create(user=request.user, recipe=recipe)
        data = self.serializer_class(recipe).data
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        cart = PurchaseList.objects.filter(user=user, recipe=recipe)
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(CartAndFavoritesMixin, viewsets.ModelViewSet):
    queryset = PurchaseList.objects.all()
    serializer_class = RecipePurchaseSerializer
    permission_classes = (IsAuthenticated,)


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, **kwargs):
        user_id = kwargs.get('user_id')
        author = get_object_or_404(User, id=user_id)
        user = request.user
        Follow.objects.create(user=user, author=author)
        data = self.serializer_class(
            author,
            context={'request': request},
            data=request.data,
            partial=True
        )
        data.is_valid(raise_exception=True)
        return Response(data.data, status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        user_id = kwargs.get('user_id')
        user = request.user
        author = get_object_or_404(User, id=user_id)
        follower = Follow.objects.filter(user=user, author=author)
        follower.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
