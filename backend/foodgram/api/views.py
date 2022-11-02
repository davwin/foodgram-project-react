from django.db.models import Sum
from django.http import FileResponse, Http404, HttpResponse
from knox.auth import AuthToken
from rest_framework import filters, generics, mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAuthenticated)
from rest_framework.response import Response
from rest_framework.views import APIView

from foods.models import (Favorites, Follow, Ingredient, IngredientsAmount,
                          PurchaseList, Recipe, Tag, User)

from .permissions import IsAdmin, ReadOnly
from .serializers import (ChangePasswordSerializer, FollowSerializer,
                          IngredientSerializer, RecipeListRetrieveSerializer,
                          RecipePostUpdateSerializer, RecipePurchaseSerializer,
                          SpecificUserSerializer, TagSerializer,
                          UserLoginSerializers, UserSerializer)


@api_view(['POST'])
def login_api(request):
    serializer = UserLoginSerializers(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    user = User.objects.get(email=email)
    _, token = AuthToken.objects.create(user)

    return Response({
        'auth_token': token
    })


@api_view(['GET'])
def user_personal_page(request):
    user = request.user

    if user.is_authenticated:
        if Follow.objects.filter(user=user, following=user):
            return Response({'error': 'subscirption_is_wrong'}, status=400)
        else:
            is_subscribed = "False"
        return Response({
            'email': user.email,
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_subscirbed': is_subscribed,
            })
    return Response({'error': 'not authenticted'}, status=400)


class SpecificUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return User.objects.get(id=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        user = request.user
        if user.is_authenticated:
            rev_user = self.get_object(pk)
            serializer = SpecificUserSerializer(
                rev_user, context={'request': request}
                )
            return Response(serializer.data)


class ChangePasswordView(generics.CreateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def create(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if self.object.password != serializer.data.get("current_password"):
                return Response({"current_password": ["Wrong password."]},
                                status=status.HTTP_400_BAD_REQUEST)
            self.object.password = serializer.data.get("new_password")
            self.object.save()
            return HttpResponse(status=204)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    lookup_field = 'id'
    search_fields = ('id',)


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

    def get_paginated_response(self, data):
        return Response(data)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListRetrieveSerializer
        return RecipePostUpdateSerializer

    @action(
        methods=('GET',),
        url_path='download_shopping_cart',
        detail=False,
    )
    def download_shopping_cart(self, request):
        user = request.user
        bubbba = IngredientsAmount.objects.filter(
            recipes__recipe_cart__user=user).values(
                'name__name', 'name__measurement_unit').annotate(
                    amount=Sum('amount'))
        response = FileResponse(
            bubbba,
            content_type="text/plain",
            as_attachment=True,
            filename="purchase_list.txt",
        )
        return response


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = PurchaseList.objects.all()
    serializer_class = RecipePurchaseSerializer

    def create(self, request, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        recipe = Recipe.objects.get(id=recipe_id)
        PurchaseList.objects.create(user=request.user, recipe=recipe)
        data = self.serializer_class(recipe).data
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        user = request.user
        recipe = Recipe.objects.get(id=recipe_id)
        cart = PurchaseList.objects.filter(user=user, recipe=recipe)
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorites.objects.all()
    serializer_class = RecipePurchaseSerializer

    def create(self, request, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        recipe = Recipe.objects.get(id=recipe_id)
        user = request.user
        Favorites.objects.create(user=user, recipe=recipe)
        data = self.serializer_class(recipe).data
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        user = request.user
        recipe = Recipe.objects.get(id=recipe_id)
        f_recipe = Favorites.objects.filter(user=user, recipe=recipe)
        f_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer

    def create(self, request, **kwargs):
        user_id = kwargs.get('user_id')
        author = User.objects.get(id=user_id)
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
        author = User.objects.get(id=user_id)
        follower = Follow.objects.filter(user=user, author=author)
        follower.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
