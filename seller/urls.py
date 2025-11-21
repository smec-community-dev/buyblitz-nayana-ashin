from django.contrib import admin
from django.urls import path

from seller import views

urlpatterns = [
    path('sellerdashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('register/', views.register_seller, name='register_seller'),
    path('login/', views.login_seller, name='login'),
    path('products/', views.seller_products, name='seller_products'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/update/<str:slug>/', views.update_product, name='update_product'),
    path('product/delete/<str:slug>/', views.delete_product, name='delete_product'),
    path('product/<str:slug>/', views.product_detail, name='product_detail'),
    path('orders/', views.seller_orders, name='seller_orders'),
    path('order/<int:id>/', views.order_detail, name='order_detail'),
path('profile/', views.seller_profile, name='seller_profile'),
path('logout/', views.logout_seller, name='logout_seller')

]
