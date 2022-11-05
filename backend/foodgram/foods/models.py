import re

from colorfield.fields import ColorField
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

USERNAME_ME_ERROR = 'Username указан неверно! Нельзя указать username "me"'
INVALID_CHARACTER_ERR = ('Username указан неверно!'
                         'Можно использовать только латинские буквы,'
                         'цифры и @/./+/-/_')
REGEX = re.compile(r'^[\w.@+-]+\Z')


def username_validator(value):
    if value.lower() == 'me':
        raise ValidationError(
            USERNAME_ME_ERROR
        )
    if not REGEX.match(value):
        raise ValidationError(
            INVALID_CHARACTER_ERR
        )
    return value


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        unique=True,
        max_length=150,
        verbose_name='Пользователь',
        validators=[username_validator],
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        blank=True
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        blank=True
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль',
        blank=False
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self) -> str:
        return self.username


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name='Тэг')
    slug = models.SlugField(unique=True, verbose_name='Слаг')
    color = ColorField(unique=True, default='#49B64E', verbose_name='Цвет')

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=True,
                            verbose_name='Ингредиент')
    measurement_unit = models.CharField(max_length=200,
                                        verbose_name='Мера измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class IngredientsAmount(models.Model):
    name = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингрединты',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Кол-во ингредиентов'
        verbose_name_plural = 'Кол-во ингредиентов'

    def __str__(self):
        return f'{self.name} - {self.amount}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipe',
        verbose_name='Автор')
    name = models.CharField(max_length=200, verbose_name='Название рецепта')
    image = models.ImageField(
        upload_to='foods/', verbose_name='Фото блюда')
    text = models.TextField(verbose_name='Описание блюда')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    tags = models.ManyToManyField(
        Tag,
        related_name='recipe',
        verbose_name='Тэги')
    cooking_time = models.DecimalField(max_digits=2, decimal_places=0,
                                       verbose_name='Время готовки')
    ingredients = models.ManyToManyField(
        'IngredientsAmount',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор рецепта'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow_user_author'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Подписчик',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',), name='unique_favorite'),)

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class PurchaseList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_cart',
        verbose_name='Покупатель',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',), name='unique_shopping_cart')),

    def __str__(self):
        return f'{self.user} - {self.recipe}'
