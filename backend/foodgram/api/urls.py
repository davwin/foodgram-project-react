from django.urls import include, path
from knox import views as knox_views
from rest_framework import routers

from .views import (ChangePasswordView, FavoriteViewSet, FollowViewSet,
                    IngredientViewSet, RecipeViewSet, ShoppingCartViewSet,
                    SpecificUserView, TagViewSet, UserViewSet, login_api,
                    user_personal_page)

app_name = 'api'

router_v1 = routers.DefaultRouter()
router_v1.register(r'users', UserViewSet, basename='users')
router_v1.register(r'recipes', RecipeViewSet, basename='recipe')
router_v1.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart',
                   ShoppingCartViewSet, basename='purchase_list')
router_v1.register(r'recipes/(?P<recipe_id>\d+)/favorite',
                   FavoriteViewSet, basename='favorite')
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(
    r'users/subscriptions', FollowViewSet, basename='subscriptions'
    )
router_v1.register(
    r'users/(?P<user_id>\d+)/subscribe', FollowViewSet, basename='subscribe'
    )
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('users/me/', user_personal_page),
    path('users/<int:pk>/', SpecificUserView.as_view(), name='specific'),
    path('auth/token/login/', login_api),
    path('auth/token/logout/', knox_views.LogoutView.as_view()),
    path('users/set_password/', ChangePasswordView.as_view()),
    path('', include(router_v1.urls)),

]
