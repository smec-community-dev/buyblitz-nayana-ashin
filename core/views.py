from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, authenticate, login
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json

# Import your models
from core.models import Category, SubCategory
from user.models import Order, OrderItem, Review
from seller.models import Product


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        print(user)

        if user is not None:
            if hasattr(user, "role") and user.role == "admin":
                print("ADMIN — redirecting now")
                login(request, user)
                return redirect("admin_cz:admin_dashboard")   # FIXED
            else:
                messages.error(request, "Only admin users can log in here.")
        else:
            messages.error(request, "Invalid username or password.")

        return redirect("admin_cz:admin_login")  # FIXED

    return render(request, 'admin/login.html')

# Admin Check Function
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def admin_dashboard(request):
    today = timezone.now().date()
    last_7_days = today - timedelta(days=6)

    # Define which order statuses count as "paid"
    PAID_STATUSES = ['PLACED', 'PROCESSING', 'SHIPPED', 'DELIVERED']

    # === Key Statistics ===
    total_revenue = Order.objects.filter(
        order_status__in=PAID_STATUSES,
        created_at__gte=last_7_days
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    total_orders = Order.objects.filter(created_at__gte=last_7_days).count()
    new_orders_today = Order.objects.filter(created_at__date=today).count()
    pending_products = Product.objects.filter(is_approved=False, is_active=True).count()

    avg_rating_result = Review.objects.aggregate(avg=Avg('rating'))
    avg_rating = round(avg_rating_result['avg'], 1) if avg_rating_result['avg'] else 0
    total_reviews = Review.objects.count()

    # === Weekly Sales Data ===
    weekly_data = []
    for i in range(7):
        date = today - timedelta(days=6 - i)
        day_sales = Order.objects.filter(
            order_status__in=PAID_STATUSES,
            created_at__date=date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        weekly_data.append(float(day_sales))

    # === Top 10 Products by Sales ===
    top_products = (
        Product.objects
        .annotate(total_sold=Count('orderitem__quantity'))
        .filter(total_sold__gt=0)
        .order_by('-total_sold')[:10]
    )

    top_products_list = []
    for p in top_products:
        stock_status = "active"
        if p.stock <= 0:
            stock_status = "out"
        elif p.stock <= 10:
            stock_status = "low"

        top_products_list.append({
            'name': p.title,
            'category': p.category.name if p.category else "Uncategorized",
            'price': float(p.price),
            'stock': p.stock,
            'status': stock_status,
        })

    # === Recent 8 Orders ===
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]
    recent_orders_list = []
    for order in recent_orders:
        items_count = order.items.count()
        status_display = dict(Order.ORDER_STATUS_CHOICES).get(order.order_status, order.order_status)

        recent_orders_list.append({
            'id': order.id,
            'customer': order.user.get_full_name() or order.user.username or "Guest",
            'product_count': items_count,
            'amount': float(order.total_amount),
            'status': status_display,
        })

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'new_orders_today': new_orders_today,
        'pending_products': pending_products,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'weekly_sales': json.dumps(weekly_data),
        'top_products': top_products_list,
        'recent_orders': recent_orders_list,
    }

    return render(request, 'admin/admin_dashboard.html', context)




def admin_products(request):
    # Base queryset
    products = Product.objects.select_related('category', 'seller__user').order_by('-created_at')
    categories = Category.objects.all()

    # Get filters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', 'all')
    status_filter = request.GET.get('status', 'all')
    stock_filter = request.GET.get('stock', 'all')

    # 1️⃣ SEARCH FILTER
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(seller__store_name__icontains=search_query) |
            Q(seller__user__username__icontains=search_query)
        )

    # 2️⃣ CATEGORY FILTER
    if category_filter != 'all':
        products = products.filter(category_id=category_filter)

    # 3️⃣ STATUS FILTER
    if status_filter != 'all':
        if status_filter == 'approved':
            products = products.filter(is_approved=True)
        elif status_filter == 'pending':
            products = products.filter(is_approved=False)

    # 4️⃣ STOCK FILTER
    if stock_filter != 'all':
        if stock_filter == 'active':
            products = products.filter(stock__gt=10)
        elif stock_filter == 'low':
            products = products.filter(stock__gt=0, stock__lte=10)
        elif stock_filter == 'out':
            products = products.filter(stock=0)

    # CALCULATE STATS
    total_products = Product.objects.count()
    approved_products = Product.objects.filter(is_approved=True).count()
    pending_products = Product.objects.filter(is_approved=False).count()
    out_of_stock = Product.objects.filter(stock=0).count()

    # PAGINATION
    paginator = Paginator(products, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': categories,
        'total_products': total_products,
        'approved_products': approved_products,
        'pending_products': pending_products,
        'out_of_stock': out_of_stock,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'stock_filter': stock_filter,
    }

    return render(request, 'admin/admin_products.html', context)



def product_detail(request, product_id):
    """
    View product details
    """
    try:
        product = get_object_or_404(
            Product.objects.select_related('category', 'seller__user'),
            id=product_id
        )

        # FIX: Use first image instead of trying to use is_main field
        main_image = product.images.first()
        image_url = main_image.image.url if main_image else '/static/images/default-product.jpg'

        context = {
            'product': product,
            'image_url': image_url,
        }

        return render(request, 'admin/product_detail.html', context)

    except Exception as e:
        messages.error(request, f'Error loading product: {str(e)}')
        return redirect('admin_products')




def approve_product(request, product_id):
    """
    Approve a product
    """
    try:
        product = get_object_or_404(Product, id=product_id)
        product.is_approved = True
        product.save()

        messages.success(request, f'Product "{product.title}" has been approved!')
        return redirect('product_detail', product_id=product_id)

    except Exception as e:
        messages.error(request, f'Error approving product: {str(e)}')
        return redirect('product_detail', product_id=product_id)




@require_POST
def reject_product(request, product_id):
    """
    Reject a product
    """
    try:
        product = get_object_or_404(Product, id=product_id)
        product.is_approved = False
        product.save()

        messages.success(request, f'Product "{product.title}" has been rejected!')
        return redirect('product_detail', product_id=product_id)

    except Exception as e:
        messages.error(request, f'Error rejecting product: {str(e)}')
        return redirect('product_detail', product_id=product_id)




def edit_product(request, product_id):
    """
    Edit product page
    """
    product = get_object_or_404(Product, id=product_id)
    messages.info(request, 'Edit functionality coming soon!')
    return redirect('product_detail', product_id=product_id)




def delete_product(request, product_id):
    """
    Delete a product
    """
    try:
        product = get_object_or_404(Product, id=product_id)
        product_title = product.title
        product.delete()

        messages.success(request, f'Product "{product_title}" has been deleted!')
        return redirect('admin_products')

    except Exception as e:
        messages.error(request, f'Error deleting product: {str(e)}')
        return redirect('product_detail', product_id=product_id)




def get_product_details(request, product_id):
    """
    AJAX endpoint to get product details
    """
    try:
        product = get_object_or_404(
            Product.objects.select_related('category', 'seller__user'),
            id=product_id
        )

        product_data = {
            'id': product.id,
            'title': product.title,
            'description': product.description,
            'price': str(product.price),
            'stock': product.stock,
            'category': product.category.name if product.category else 'Uncategorized',
            'is_approved': product.is_approved,
            'status': 'approved' if product.is_approved else 'pending',
            'seller': {
                'name': product.seller.store_name or product.seller.user.username,
                'username': product.seller.user.username,
                'email': product.seller.user.email,
            },
            'created_at': product.created_at.strftime('%Y-%m-%d %H:%M'),
        }

        return JsonResponse({'success': True, 'product': product_data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})




def admin_profile(request):
    user = request.user

    # Default session values (only used if not set)
    defaults = {
        "phone": "",
        "birth_date": "",
        "gender": "",
        "email_notifications": True,
        "sms_notifications": False,
        "two_factor_auth": False,
        "marketing_emails": False,
        "store_name": "ShopHub Admin",
        "store_description": "Central administration panel for ShopHub platform.",
        "store_category": "platform",
        "store_currency": "INR",
    }

    # Initialize session values if they don't exist
    for key, value in defaults.items():
        if key not in request.session:
            request.session[key] = value

    context = {
        "phone": request.session.get("phone", ""),
        "birth_date": request.session.get("birth_date", ""),
        "gender": request.session.get("gender", ""),
        "email_notifications": request.session.get("email_notifications", True),
        "sms_notifications": request.session.get("sms_notifications", False),
        "two_factor_auth": request.session.get("two_factor_auth", False),
        "marketing_emails": request.session.get("marketing_emails", False),
        "store_name": request.session.get("store_name", "ShopHub Admin"),
        "store_description": request.session.get("store_description", ""),
        "store_category": request.session.get("store_category", "platform"),
        "store_currency": request.session.get("store_currency", "INR"),
    }

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # === 1. Personal Information ===
        if form_type == "personal_info":
            first_name = request.POST.get("firstName", "").strip()
            last_name = request.POST.get("lastName", "").strip()
            email = request.POST.get("email", "").strip()

            # Update User model
            user.first_name = first_name
            user.last_name = last_name
            if email and email != user.email:
                user.email = email
            user.save()

            # Update session fields
            request.session["phone"] = request.POST.get("phone", "").strip()
            request.session["birth_date"] = request.POST.get("birthDate", "")
            request.session["gender"] = request.POST.get("gender", "")

            messages.success(request, "Personal information updated successfully!")
            return redirect("admin_profile")

        # === 2. Change Password ===
        elif form_type == "change_password":
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            elif len(new_password) < 8:
                messages.error(request, "New password must be at least 8 characters long.")
            elif not any(c.isupper() for c in new_password):
                messages.error(request, "Password must contain at least one uppercase letter.")
            elif not any(c.isdigit() for c in new_password):
                messages.error(request, "Password must contain at least one number.")
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Important: keeps user logged in
                messages.success(request, "Password changed successfully!")
            return redirect("admin_profile")

        # === 3. Account Settings (Toggles) ===
        elif form_type == "account_settings":
            request.session["email_notifications"] = "email_notifications" in request.POST
            request.session["sms_notifications"] = "sms_notifications" in request.POST
            request.session["two_factor_auth"] = "two_factor_auth" in request.POST
            request.session["marketing_emails"] = "marketing_emails" in request.POST

            messages.success(request, "Account settings updated successfully!")
            return redirect("admin_profile")

        # === 4. Store / Platform Settings ===
        elif form_type == "store_settings":
            request.session["store_name"] = request.POST.get("store_name", "").strip()
            request.session["store_description"] = request.POST.get("store_description", "").strip()
            request.session["store_category"] = request.POST.get("store_category", "platform")
            request.session["store_currency"] = request.POST.get("store_currency", "INR")

            messages.success(request, "Platform settings updated successfully!")
            return redirect("admin_profile")

    return render(request, "admin/admin_profile.html", context)




def admin_orders(request):
    """
    Admin view to manage all orders
    """
    # Base queryset
    orders = Order.objects.select_related('user').prefetch_related(
        'items__product__seller__user',
        'items__product__images'
    ).order_by('-created_at')

    # Get filters from request
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    date_range = request.GET.get('date_range', 'all')

    # Apply search filter
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(items__product__title__icontains=search_query)
        ).distinct()

    # Apply status filter
    if status_filter != 'all':
        orders = orders.filter(order_status=status_filter)

    # Apply date range filter
    today = timezone.now().date()
    if date_range != 'all':
        if date_range == 'today':
            orders = orders.filter(created_at__date=today)
        elif date_range == 'week':
            start_date = today - timedelta(days=today.weekday())
            orders = orders.filter(created_at__date__gte=start_date)
        elif date_range == 'month':
            orders = orders.filter(created_at__year=today.year, created_at__month=today.month)
        elif date_range == 'quarter':
            current_quarter = (today.month - 1) // 3 + 1
            start_month = 3 * (current_quarter - 1) + 1
            end_month = start_month + 2
            orders = orders.filter(
                created_at__year=today.year,
                created_at__month__gte=start_month,
                created_at__month__lte=end_month
            )

    # Pagination
    paginator = Paginator(orders, 10)  # 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_range': date_range,
        'total_orders': orders.count(),
    }

    return render(request, 'admin/admin_orders.html', context)



def resolve_dispute(request, order_id):
    """
    Resolve a disputed order
    """
    try:
        order = get_object_or_404(Order, id=order_id)

        if order.order_status != 'DISPUTED':
            messages.error(request, 'This order is not in disputed status.')
            return redirect('admin_orders')

        # Resolve the dispute - set status to appropriate value
        order.order_status = 'CONFIRMED'
        order.save()

        messages.success(request, f'Dispute for order #{order_id} has been resolved successfully.')

    except Exception as e:
        messages.error(request, f'Error resolving dispute: {str(e)}')

    return redirect('admin_orders')




@require_POST
def update_order_status(request, order_id):
    """
    Update order status
    """
    try:
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')

        if new_status not in dict(Order.ORDER_STATUS_CHOICES):
            messages.error(request, 'Invalid order status.')
            return redirect('admin_orders')

        order.order_status = new_status
        order.save()

        messages.success(request, f'Order #{order_id} status updated to {new_status}.')

    except Exception as e:
        messages.error(request, f'Error updating order status: {str(e)}')

    return redirect('admin_orders')




def order_detail(request, order_id):
    """
    View order details
    """
    try:
        order = get_object_or_404(
            Order.objects.select_related('user').prefetch_related(
                'items__product__seller__user',
                'items__product__images'
            ),
            id=order_id
        )

        context = {
            'order': order,
        }

        return render(request, 'admin/order_detail.html', context)

    except Exception as e:
        messages.error(request, f'Error loading order: {str(e)}')
        return redirect('admin_orders')


def admin_categories(request):
    categories = Category.objects.all().annotate(
        subcategory_count=Count('subcategories')
    )

    for category in categories:
        # REAL PRODUCT COUNT
        category.product_count = Product.objects.filter(category=category).count()

        # Add session data
        category.description = request.session.get(f'category_{category.id}_description', 'No description provided.')
        category.icon = request.session.get(f'category_{category.id}_icon', '📱')
        category.status = request.session.get(f'category_{category.id}_status', 'active')

    return render(request, 'admin/admin_categories.html', {
        'categories': categories
    })




@require_http_methods(["POST"])
def create_category(request):
    try:
        data = json.loads(request.body)
        category = Category.objects.create(
            name=data['name']
        )

        # Store additional data in session
        request.session[f'category_{category.id}_description'] = data.get('description', '')
        request.session[f'category_{category.id}_icon'] = data.get('icon', '📱')
        request.session[f'category_{category.id}_status'] = data.get('status', 'active')
        request.session[f'category_{category.id}_product_count'] = data.get('product_count', 0)

        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': data.get('description', ''),
                'icon': data.get('icon', '📱'),
                'status': data.get('status', 'active'),
                'product_count': data.get('product_count', 0)
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@require_http_methods(["POST"])
def update_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id)
        data = json.loads(request.body)

        category.name = data.get('name', category.name)
        category.save()

        # Update additional data in session
        if 'description' in data:
            request.session[f'category_{category.id}_description'] = data['description']
        if 'icon' in data:
            request.session[f'category_{category.id}_icon'] = data['icon']
        if 'status' in data:
            request.session[f'category_{category.id}_status'] = data['status']
        if 'product_count' in data:
            request.session[f'category_{category.id}_product_count'] = data['product_count']

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})




@require_http_methods(["DELETE", "POST"])
def delete_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id)
        category.delete()

        # Clean up session data
        keys_to_remove = [
            f'category_{category_id}_description',
            f'category_{category_id}_icon',
            f'category_{category_id}_status',
            f'category_{category_id}_product_count'
        ]
        for key in keys_to_remove:
            if key in request.session:
                del request.session[key]

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



def get_category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    # Get additional data from session
    description = request.session.get(f'category_{category_id}_description', '')
    icon = request.session.get(f'category_{category_id}_icon', '📱')
    status = request.session.get(f'category_{category_id}_status', 'active')
    product_count = request.session.get(f'category_{category_id}_product_count', 0)

    return JsonResponse({
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': description,
        'icon': icon,
        'status': status,
        'product_count': product_count
    })


from django.db.models import Count

def admin_subcategories(request):
    categories = Category.objects.all()

    # Fetch DB subcategories WITH product count
    subcategories = SubCategory.objects.select_related('category') \
                                       .annotate(product_count=Count('products'))

    # Filters
    category_filter = request.GET.get('category', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    if category_filter != 'all':
        subcategories = subcategories.filter(category__id=category_filter)

    if search_query:
        subcategories = subcategories.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Session-based extra fields (only icon, description, status)
    for subcategory in subcategories:
        subcategory.description = request.session.get(
            f'subcategory_{subcategory.id}_description', 'No description provided.'
        )
        subcategory.icon = request.session.get(
            f'subcategory_{subcategory.id}_icon', '📱'
        )
        subcategory.status = request.session.get(
            f'subcategory_{subcategory.id}_status', 'active'
        )
        subcategory.display_order = request.session.get(
            f'subcategory_{subcategory.id}_display_order', 1
        )

    # Status filter (this uses session override)
    if status_filter != 'all':
        subcategories = [
            s for s in subcategories if s.status == status_filter
        ]

    # Stats
    total_subcategories = SubCategory.objects.count()
    active_count = sum(
        1 for s in SubCategory.objects.all()
        if request.session.get(f'subcategory_{s.id}_status', 'active') == 'active'
    )
    inactive_count = total_subcategories - active_count
    categories_count = Category.objects.count()

    context = {
        'subcategories': subcategories,
        'categories': categories,
        'current_category_filter': category_filter,
        'current_status_filter': status_filter,
        'search_query': search_query,
        'total_subcategories': total_subcategories,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'categories_count': categories_count,
    }

    return render(request, 'admin/admin_subcategories.html', context)


@require_http_methods(["POST"])
def create_subcategory(request):
    """Create a new subcategory"""
    try:
        data = json.loads(request.body)

        # Validate required fields
        if not data.get('name'):
            return JsonResponse({
                'success': False,
                'error': 'Subcategory name is required'
            })

        if not data.get('category_id'):
            return JsonResponse({
                'success': False,
                'error': 'Parent category is required'
            })

        category = get_object_or_404(Category, id=data['category_id'])

        # Create subcategory
        subcategory = SubCategory.objects.create(
            category=category,
            name=data['name']
        )

        # Store additional data in session
        request.session[f'subcategory_{subcategory.id}_description'] = data.get('description', '')
        request.session[f'subcategory_{subcategory.id}_icon'] = data.get('icon', '📱')
        request.session[f'subcategory_{subcategory.id}_status'] = data.get('status', 'active')
        request.session[f'subcategory_{subcategory.id}_display_order'] = data.get('display_order', 1)
        request.session[f'subcategory_{subcategory.id}_product_count'] = 0

        messages.success(request, f'Subcategory "{subcategory.name}" created successfully!')

        return JsonResponse({
            'success': True,
            'message': 'Subcategory created successfully',
            'subcategory': {
                'id': subcategory.id,
                'name': subcategory.name,
                'slug': subcategory.slug,
                'category_name': category.name
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)



@require_http_methods(["POST"])
def update_subcategory(request, subcategory_id):
    """Update an existing subcategory"""
    try:
        subcategory = get_object_or_404(SubCategory, id=subcategory_id)
        data = json.loads(request.body)

        # Update category if provided
        if 'category_id' in data:
            category = get_object_or_404(Category, id=data['category_id'])
            subcategory.category = category

        # Update name if provided
        if 'name' in data:
            subcategory.name = data['name']

        subcategory.save()

        # Update session data
        if 'description' in data:
            request.session[f'subcategory_{subcategory.id}_description'] = data['description']
        if 'icon' in data:
            request.session[f'subcategory_{subcategory.id}_icon'] = data['icon']
        if 'status' in data:
            request.session[f'subcategory_{subcategory.id}_status'] = data['status']
        if 'display_order' in data:
            request.session[f'subcategory_{subcategory.id}_display_order'] = data['display_order']

        messages.success(request, f'Subcategory "{subcategory.name}" updated successfully!')

        return JsonResponse({
            'success': True,
            'message': 'Subcategory updated successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["DELETE", "POST"])
def delete_subcategory(request, subcategory_id):
    """Delete a subcategory"""
    try:
        subcategory = get_object_or_404(SubCategory, id=subcategory_id)
        subcategory_name = subcategory.name

        # Delete the subcategory
        subcategory.delete()

        # Clean up session data
        keys_to_remove = [
            f'subcategory_{subcategory_id}_description',
            f'subcategory_{subcategory_id}_icon',
            f'subcategory_{subcategory_id}_status',
            f'subcategory_{subcategory_id}_display_order',
            f'subcategory_{subcategory_id}_product_count'
        ]
        for key in keys_to_remove:
            if key in request.session:
                del request.session[key]

        messages.success(request, f'Subcategory "{subcategory_name}" deleted successfully!')

        return JsonResponse({
            'success': True,
            'message': 'Subcategory deleted successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)




def get_subcategory_detail(request, subcategory_id):
    """Get details of a specific subcategory"""
    try:
        subcategory = get_object_or_404(SubCategory, id=subcategory_id)

        # Get additional data from session
        description = request.session.get(f'subcategory_{subcategory_id}_description', '')
        icon = request.session.get(f'subcategory_{subcategory_id}_icon', '📱')
        status = request.session.get(f'subcategory_{subcategory_id}_status', 'active')
        display_order = request.session.get(f'subcategory_{subcategory_id}_display_order', 1)
        product_count = request.session.get(f'subcategory_{subcategory_id}_product_count', 0)

        return JsonResponse({
            'success': True,
            'subcategory': {
                'id': subcategory.id,
                'name': subcategory.name,
                'slug': subcategory.slug,
                'description': description,
                'icon': icon,
                'status': status,
                'display_order': display_order,
                'product_count': product_count,
                'category_id': subcategory.category.id,
                'category_name': subcategory.category.name
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=404)