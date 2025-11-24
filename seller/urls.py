from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Seller authentication URLs
    path('register/', views.register_seller, name='register_seller'),
    path('login/', views.login_seller, name='login'),
    path('logout/', views.logout_seller, name='logout_seller'),
path('seller_notifications/',views.notification_page,name="notifications"),



    # Password reset flow
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='seller/password_reset.html',
             email_template_name='seller/password_reset_email.html',
             subject_template_name='seller/password_reset_subject.txt',
             success_url='/seller/password_reset/done/'
         ),
         name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='seller/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='seller/password_reset_confirm.html',
             success_url='/seller/reset/done/'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='seller/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Seller dashboard and management URLs
    path('sellerdashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('products/', views.seller_products, name='seller_products'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/update/<str:slug>/', views.update_product, name='update_product'),
    path('product/delete/<str:slug>/', views.delete_product, name='delete_product'),
    path('product/<str:slug>/', views.product_detail, name='product_detail'),
    path('orders/', views.seller_orders, name='seller_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('profile/', views.seller_profile, name='seller_profile'),
]