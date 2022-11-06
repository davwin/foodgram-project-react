from django.db import transaction
from django.db.models import Q
from drf_extra_fields.fields import Base64ImageField
from foods.models import (Favorite, Follow, Ingredient, IngredientsAmount,
                          PurchaseList, Recipe, Tag, User, username_validator)
from rest_framework import serializers


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
            User.objects.filter(Q(email__iexact=email) | Q(
                username__iexact=email)).distinct()
        )
        if user_queryset.exists() and user_queryset.count() == 1:
            user_set = user_queryset.first()
            if user_set.password == password:
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
        return User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )


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


class IngredientAmountListRetrieveSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='name.id')
    name = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )
    measurement_unit = serializers.CharField(
        source='name.measurement_unit',
        read_only=True,
    )

    class Meta:
        model = IngredientsAmount
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class IngredientAmountCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        many=False,
        read_only=False,
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
    ingredients = IngredientAmountListRetrieveSerializer(
        read_only=True,
        many=True,
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


class RecipePostUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=False,
        queryset=Tag.objects.all(),
        required=True,
    )
    ingredients = IngredientAmountCreateUpdateSerializer(
        read_only=False,
        many=True,
        required=True,
    )
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited',
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart',
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

    def add_or_edit_ingredients(self, recipe, ingredients):
        ingredient_amount = [
            IngredientsAmount(name=ingredient['name'],
                              amount=ingredient['amount'],
                              recipe=recipe.id
                              ) for ingredient in ingredients]
        ingredient_amount = IngredientsAmount.objects.bulk_create(
            ingredient_amount)
        for ingredient in ingredient_amount:
            recipe.ingredients.add(ingredient.recipe)
        recipe.save()

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        author = self.context['request'].user
        validated_data['author'] = author
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            recipe.tags.add(tag)
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


class RecipePurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class FollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user.id
        return Follow.objects.filter(
            user_id=current_user, author_id=obj.id).exists()

    def get_recipes(self, user):
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        recipes = Recipe.objects.filter(author=user)

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
