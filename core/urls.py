from django.urls import path
from . import views

app_name = 'admin_cz'

urlpatterns = [
    # Dashboard
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('login/', views.admin_login, name='admin_login'),

    # Products
    path('dashboard/admin/products/', views.admin_products, name='admin_products'),
    path('dashboard/admin/products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('dashboard/admin/products/<int:product_id>/approve/', views.approve_product, name='approve_product'),
    path('dashboard/admin/products/<int:product_id>/reject/', views.reject_product, name='reject_product'),
    path('dashboard/admin/products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('dashboard/admin/products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('dashboard/admin/products/<int:product_id>/details/', views.get_product_details, name='get_product_details'),

    # Orders
    path('dashboard/admin/orders/', views.admin_orders, name='admin_orders'),
    path('dashboard/admin/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('dashboard/admin/orders/<int:order_id>/resolve-dispute/', views.resolve_dispute, name='resolve_dispute'),
    path('dashboard/admin/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),

    # Categories
    path('dashboard/admin/categories/', views.admin_categories, name='admin_categories'),
    path('dashboard/admin/categories/create/', views.create_category, name='create_category'),
    path('dashboard/admin/categories/<int:category_id>/update/', views.update_category, name='update_category'),
    path('dashboard/admin/categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('dashboard/admin/categories/<int:category_id>/detail/', views.get_category_detail, name='get_category_detail'),

    # Subcategories
    path('dashboard/admin/subcategories/', views.admin_subcategories, name='admin_subcategories'),
    path('dashboard/admin/subcategories/create/', views.create_subcategory, name='create_subcategory'),
    path('dashboard/admin/subcategories/<int:subcategory_id>/update/', views.update_subcategory,
         name='update_subcategory'),
    path('dashboard/admin/subcategories/<int:subcategory_id>/delete/', views.delete_subcategory,
         name='delete_subcategory'),
    path('dashboard/admin/subcategories/<int:subcategory_id>/detail/', views.get_subcategory_detail,
         name='get_subcategory_detail'),

    # Profile
    path('dashboard/admin/profile/', views.admin_profile, name='admin_profile'),
]