from django.contrib import auth
from django.db import transaction
from django.db import models
from drf_extra_fields.fields import Base64ImageField
from foods.models import (Favorite, Follow, Ingredient, IngredientsAmount,
                          PurchaseList, Recipe, Tag, username_validator)
from rest_framework import serializers

User = auth.get_user_model()


class UserLoginSerializers(serializers.ModelSerializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
        ]

    def validate(self, data):
        email = data['email']
        password = data['password']
        user_queryset = (
            User.objects.filter(models.Q(email__iexact=email) | models.Q(
                username__iexact=email)).distinct()
        )
        if user_queryset.exists() and user_queryset.count() == 1:
            user = user_queryset.first()
            if auth.authenticate(username=user.username, password=password):
                return data
            raise serializers.ValidationError("Incorrect Password!")
        raise serializers.ValidationError("Not Valid Email!")


class ChangePasswordSerializer(serializers.Serializer):
    model = User

    """
    Serializer for password change endpoint.
    """
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class UsernameValidationMixin:

    def validate_username(self, value):
        return username_validator(value)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username',
                  'password', 'first_name', 'last_name',
                  'is_subscribed']
        extra_kwargs = {'password': {
            'write_only': True, 'min_length': 4}}

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user.id
        return Follow.objects.filter(
            user_id=current_user, author_id=obj.id).exists()

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class SpecificUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed']
        extra_kwargs = {'password': {
            'write_only': True, 'min_length': 4}}

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user.id
        return Follow.objects.filter(
            user_id=current_user, author_id=obj.id).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class IngredientAmountCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        model = IngredientsAmount
        fields = (
            'id',
            'amount',
        )


class RecipeListRetrieveSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = SpecificUserSerializer(read_only=True, many=False)
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients',
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited',
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart',
    )
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, recipe):
        """Получает список ингридиентов для рецепта.
                    Args:
                        obj (Recipe): Запрошенный рецепт.
                    Returns:
                        list: Список ингридиентов в рецепте.
                    """
        return recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=models.F('recipe__amount')
        )

    def get_is_favorited(self, recipe):
        if self.context['request'].auth is None:
            return False
        user = self.context['request'].user
        return Favorite.objects.filter(
            user=user,
            recipe=recipe,
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        if self.context['request'].auth is None:
            return False
        user = self.context['request'].user
        return PurchaseList.objects.filter(
            user=user,
            recipe=recipe,
        ).exists()


class CustomTagsSerializer(serializers.ListField):
    def to_representation(self, data):
        tags_list = self.context['request']._data['tags']
        obj = Tag.objects.filter(id__in=tags_list)
        serializer = TagSerializer(obj, many=True)
        return serializer.data


class RecipePostUpdateSerializer(serializers.ModelSerializer):
    tags = CustomTagsSerializer()
    ingredients = IngredientAmountCreateUpdateSerializer(many=True)
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )
    image = Base64ImageField(required=True)
    name = serializers.CharField(required=True)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True)
    author = SpecificUserSerializer(read_only=True, many=False)

    def validate_ingredients(self, id):
        ingredients = []
        for ingredient in id:
            ingredients.append(ingredient['id'])
        ingredients_set = set(ingredients)
        if len(ingredients_set) != len(ingredients):
            raise serializers.ValidationError('Ошибка-одинаковые ингредиенты.')
        return id

    def get_is_favorited(self, recipe):
        if self.context['request'].auth is None:
            return False
        user = self.context['request'].user
        return Favorite.objects.filter(
            user=user,
            recipe=recipe,
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        if self.context['request'].auth is None:
            return False
        user = self.context['request'].user
        return PurchaseList.objects.filter(
            user=user,
            recipe=recipe,
        ).exists()

    def add_tags(self, tags, recipe):
        for tag in tags:
            recipe.tags.add(tag)

    def add_or_edit_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            IngredientsAmount.objects.get_or_create(
                recipe=recipe,
                ingredients=ingredient['id'],
                amount=ingredient['amount']
            )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        author = self.context['request'].user
        validated_data['author'] = author
        recipe = Recipe.objects.create(**validated_data)
        self.add_tags(tags, recipe)
        self.add_or_edit_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags_list = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        super().update(instance, validated_data)
        recipe = instance
        recipe.tags.set(tags_list)
        recipe.ingredients.clear()
        self.add_or_edit_ingredients(recipe, ingredients)
        return recipe

    def to_representation(self, recipe):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeListRetrieveSerializer(recipe,
                                            context=context).data

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipePurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'author',
            'cooking_time',
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'author',
            'cooking_time',
        )


class FollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    id = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'id',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_id(self, follow_or_follow_user):
        author = follow_or_follow_user if isinstance(
            follow_or_follow_user,
            User
        ) else follow_or_follow_user.author

        return author.id

    def get_first_name(self, follow_or_follow_user):
        author = follow_or_follow_user if isinstance(
            follow_or_follow_user,
            User
        ) else follow_or_follow_user.author

        return author.first_name

    def get_last_name(self, follow_or_follow_user):
        author = follow_or_follow_user if isinstance(
            follow_or_follow_user,
            User
        ) else follow_or_follow_user.author

        return author.last_name

    def get_is_subscribed(self, follow_or_follow_user):
        current_user = self.context['request'].user.id
        return Follow.objects.filter(
            user_id=current_user, author_id=follow_or_follow_user.id
            if isinstance(
                follow_or_follow_user,
                User
            )
            else follow_or_follow_user.user.id
        ).exists()

    def get_recipes(self, follow_or_follow_user):
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        recipes = Recipe.objects.filter(
            author=follow_or_follow_user.id
            if isinstance(
                follow_or_follow_user,
                User
            )
            else follow_or_follow_user.user.id
        )

        if recipes_limit is not None:
            recipes = recipes[:int(recipes_limit)]

        serializer = RecipePurchaseSerializer(
            recipes,
            read_only=True,
            many=True,
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author_id=obj.id).count()
