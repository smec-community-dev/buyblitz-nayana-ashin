

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
path('category/<str:category_name>/', views.category_products, name='category_products'),
    path('deals/', views.deals, name='deals'),
path('about/', views.about, name='about'),
path('contact/', views.contact, name='contact'),
path('trending/', views.trending, name='trending'),
path('categories/', views.categories, name='category'),
path("profile/", views.profile, name="profile"),
path('orders/', views.orders, name='orders'),






path("wishlist/", views.wishlist_page, name="wishlist"),
path('remove_from_wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
path("remove_cart/<int:id>/", views.remove_cart, name="remove_cart"),
path("add_to_wishlist/<int:product_id>/", views.add_to_wishlist, name="add_to_wishlist"),
    path("update-cart/<int:item_id>/", views.update_cart, name="update_cart"),
    path("checkout/", views.checkout_page, name="checkout_page"),

path("add_to_cart/<int:id>/", views.add_to_cart, name="add_to_cart"),
path("wishlist/toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),







    path("product/<slug:slug>/", views.single_view, name="single_view"),
    path("trending/", views.trending, name="trending"),

]