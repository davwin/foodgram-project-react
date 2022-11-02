from django.contrib import admin

from .models import Ingredient, Tag, Recipe, User, IngredientsAmount


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
    )
    search_fields = ('username',)
    empty_value_display = '-пусто-'


admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(IngredientsAmount)
