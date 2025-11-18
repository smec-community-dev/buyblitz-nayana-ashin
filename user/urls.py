

from django.contrib import admin
from django.urls import path
from user import views

urlpatterns = [

    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    # path("profile/", views.profile, name="profile"),
    path("search/", views.search, name="search"),

    path("home/",views.home,name="home"),
    path("category/", views.category, name="category"),
    path("products/", views.products, name="products"),
    path("cart/", views.cart_page, name="cart"),


path("wishlist/", views.wishlist_page, name="wishlist"),

path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),

    path("product/<slug:slug>/", views.single_view, name="single_view"),
    path("trending/", views.trending, name="trending"),

]