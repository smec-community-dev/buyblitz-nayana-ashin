from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from django.db.models import Sum, F
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.text import slugify

from core.models import User, SubCategory
from seller.models import Seller, Product, ProductImage
from user.models import Order, OrderItem
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ProductImage
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q

from django.utils import timezone
from datetime import timedelta


from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta

from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
import json



from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
import json



def seller_dashboard(request):
    print("===== DEBUG: DASHBOARD VIEW STARTED =====")

    # 1. Check logged-in seller
    try:
        seller = Seller.objects.get(user=request.user)
        print("DEBUG: Seller found ->", seller)
    except Seller.DoesNotExist:
        print("ERROR: No seller profile for:", request.user)
        return render(request, "seller/no_seller.html")

    # 2. Seller products
    seller_products = Product.objects.filter(seller=seller)
    print("DEBUG: Seller Products Count =", seller_products.count())

    # 3. Seller order items
    seller_order_items = OrderItem.objects.filter(product__in=seller_products)
    print("DEBUG: Seller Order Items Count =", seller_order_items.count())

    # 4. Order IDs
    order_ids = list(seller_order_items.values_list('order_id', flat=True).distinct())
    print("DEBUG: Order IDs =", order_ids)

    # 5. Recent orders
    recent_orders = Order.objects.filter(id__in=order_ids).order_by('-created_at')[:5]
    print("DEBUG: Recent Orders Count =", recent_orders.count())

    # 6. Total orders
    total_orders = Order.objects.filter(id__in=order_ids).count()

    # 7. Total revenue (DELIVERED only)
    delivered_orders = Order.objects.filter(id__in=order_ids, order_status="DELIVERED")
    total_revenue = sum(order.total_amount for order in delivered_orders)
    print("DEBUG: Delivered Orders =", delivered_orders.count())

    # 8. Active products
    active_products = seller_products.filter(is_active=True).count()

    # 9. Customers
    total_customers = Order.objects.filter(id__in=order_ids).values('user').distinct().count()

    # 10. Product performance
    product_performance = []
    for product in seller_products[:5]:
        product_orders = seller_order_items.filter(product=product)
        total_sold = product_orders.aggregate(total_sold=Sum('quantity'))['total_sold'] or 0
        total_revenue_for_product = product_orders.aggregate(
            total_revenue=Sum(F('price_at_purchase') * F('quantity'))
        )['total_revenue'] or 0

        product_performance.append({
            'product': product,
            'sold': total_sold,
            'revenue': total_revenue_for_product
        })

    product_performance.sort(key=lambda x: x['revenue'], reverse=True)

    # 11. Activity feed
    recent_activity = []

    # Orders
    for order in recent_orders:
        recent_activity.append({
            'icon': '📦',
            'title': f'Order {order.order_number}',
            'desc': f'{order.user.username if order.user else "Guest"} - ₹{order.total_amount}',
            'timestamp': order.created_at
        })

    # Recent products
    recent_products = seller_products.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')[:2]

    for product in recent_products:
        recent_activity.append({
            'icon': '🆕',
            'title': 'New Product',
            'desc': f'{product.title} added',
            'timestamp': product.created_at
        })

    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:8]

    # 12. CHART DATA GENERATION - Simple line chart only
    def generate_chart_data(order_ids, months=6):
        """Generate chart data for the last N months with correct dates"""

        now = timezone.now()
        current_month = now.month
        current_year = now.year

        # Generate labels for last 6 months in correct chronological order
        labels = []
        month_year_pairs = []

        for i in range(months-1, -1, -1):  # From 5 to 0 to maintain order
            month_num = current_month - i
            year_num = current_year

            # Handle year rollover
            if month_num < 1:
                month_num += 12
                year_num -= 1

            month_name = datetime(year_num, month_num, 1).strftime('%b')
            labels.append(month_name)
            month_year_pairs.append((year_num, month_num))

        print(f"DEBUG: Generated labels: {labels}")
        print(f"DEBUG: Month-year pairs: {month_year_pairs}")

        # Initialize with zeros
        revenue_data = [0.0] * months
        orders_data = [0] * months

        # Calculate start date (first day of the first month in our range)
        first_month_year, first_month_num = month_year_pairs[0]
        start_date = timezone.make_aware(datetime(first_month_year, first_month_num, 1))

        # Get all orders in the date range
        orders = Order.objects.filter(
            id__in=order_ids,
            created_at__range=[start_date, now]
        )

        print(f"DEBUG: Orders found for chart: {orders.count()}")

        # Fill in actual data
        for order in orders:
            order_month = order.created_at.month
            order_year = order.created_at.year

            # Find the correct index for this order
            for i, (year_num, month_num) in enumerate(month_year_pairs):
                if order_month == month_num and order_year == year_num:
                    orders_data[i] += 1
                    if order.order_status == "DELIVERED":
                        revenue_data[i] += float(order.total_amount)
                    break

        return {
            'labels': labels,
            'revenue_data': revenue_data,
            'orders_data': orders_data
        }

    # Generate chart data
    chart_data = generate_chart_data(order_ids, months=6)

    # 13. Fix recent activity timestamps
    def format_time_ago(timestamp):
        """Format timestamp to human-readable time ago"""
        now = timezone.now()
        diff = now - timestamp

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

    # Update recent activity with proper time formatting
    for activity in recent_activity:
        activity['time_ago'] = format_time_ago(activity['timestamp'])

    context = {
        'seller': seller,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'active_products': active_products,
        'total_customers': total_customers,
        'product_performance': product_performance,
        'recent_activity': recent_activity,

        # Chart data for JavaScript
        'chart_labels_json': json.dumps(chart_data['labels']),
        'chart_revenue_data_json': json.dumps(chart_data['revenue_data']),
        'chart_orders_data_json': json.dumps(chart_data['orders_data']),

        # DEBUG VARIABLES
        'debug_seller_products': seller_products.count(),
        'debug_order_items': seller_order_items.count(),
        'debug_order_ids': order_ids,
        'debug_recent_orders': recent_orders.count(),
    }

    print("DEBUG: Current Date:", timezone.now())
    print("DEBUG: Chart Labels ->", chart_data['labels'])
    print("DEBUG: Chart Revenue ->", chart_data['revenue_data'])
    print("DEBUG: Chart Orders ->", chart_data['orders_data'])
    print("===== DEBUG: DASHBOARD VIEW END =====")
    return render(request, 'seller/seller_dashboard.html', context)


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Seller
from django.contrib.auth import login, authenticate

from django.contrib.auth import get_user_model
User = get_user_model()


def register_seller(request):
    User = get_user_model()
    if request.method == "POST":
        # Basic user fields
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register_seller")

        # Check if email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("register_seller")

        # Validate required fields based on role
        if role == "seller":
            shop_name = request.POST.get("shop_name")
            shop_type = request.POST.get("shop_type")
            shop_address = request.POST.get("shop_address")
            gst_number = request.POST.get("gst_number")
            bank_account_number = request.POST.get("bank_account_number")

            # Validate seller-specific fields
            if not all([shop_name, shop_type, shop_address, gst_number, bank_account_number]):
                messages.error(request, "All seller fields are required")
                return redirect("register_seller")

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            # Add role to user profile or custom field if you have one
            # If you have a custom user model with role field, use that instead
            # user.role = role
            # user.save()

        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return redirect("register_seller")

        # Create seller ONLY if role == seller
        if role == "seller":
            try:
                Seller.objects.create(
                    user=user,
                    shop_name=shop_name,
                    shop_type=shop_type,
                    shop_address=shop_address,
                    gst_number=gst_number,
                    bank_account_number=bank_account_number
                )
            except Exception as e:
                user.delete()  # Clean up user if seller creation fails
                messages.error(request, f"Error creating seller profile: {str(e)}")
                return redirect("register_seller")

        # Auto login after registration and redirect to home
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Registration successful! Welcome to your account.")
            return redirect("home")  # Change "home" to your actual home page name
        else:
            messages.success(request, "Registration successful! Please login.")
            return redirect("login")

    return render(request, "seller/register.html")

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from core.models import User
from seller.models import Seller

from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages


def login_seller(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        User = get_user_model()

        # Allow login using email OR username
        if User.objects.filter(email=username).exists():
            user_obj = User.objects.get(email=username)
            username = user_obj.username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Check if seller
            if hasattr(user, 'seller') or Seller.objects.filter(user=user).exists():
                messages.success(request, 'Welcome back! You have successfully logged in.')
                return redirect('seller_dashboard')

            return redirect('home')

        # Error message when login fails
        return render(request, "seller/login.html", {
            "error": "Invalid username/email or password. Please try again."
        })

    return render(request, "seller/login.html")


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from seller.models import Seller

User = get_user_model()


def role_selection(request):
    """Show role selection page after Google OAuth"""
    # Check if user came from Google OAuth
    if not request.session.get('pending_google_signup'):
        messages.error(request, "Invalid access. Please login with Google first.")
        return redirect('login')

    return render(request, 'seller/role_selection.html')


def complete_google_signup(request):
    """Handle role selection and redirect to appropriate form"""
    if request.method == "POST":
        if not request.session.get('pending_google_signup'):
            messages.error(request, "Session expired. Please try again.")
            return redirect('login')

        selected_role = request.POST.get('selected_role')

        if not selected_role:
            messages.error(request, "Please select a role")
            return redirect('role_selection')

        # Store selected role in session
        request.session['selected_role'] = selected_role

        # Redirect based on role
        if selected_role == 'user':
            return redirect('google_user_form')
        elif selected_role == 'seller':
            return redirect('google_seller_form')
        else:
            messages.error(request, "Invalid role selected")
            return redirect('role_selection')

    return redirect('role_selection')


def google_user_form(request):
    """Show user registration form for Google signup"""
    if not request.session.get('pending_google_signup'):
        messages.error(request, "Invalid access. Please login with Google first.")
        return redirect('login')

    if request.session.get('selected_role') != 'user':
        messages.error(request, "Invalid role")
        return redirect('role_selection')

    context = {
        'google_email': request.session.get('google_email', ''),
        'google_first_name': request.session.get('google_first_name', ''),
        'google_last_name': request.session.get('google_last_name', ''),
    }
    return render(request, 'seller/google_user_form.html', context)


def google_seller_form(request):
    """Show seller registration form for Google signup"""
    if not request.session.get('pending_google_signup'):
        messages.error(request, "Invalid access. Please login with Google first.")
        return redirect('login')

    if request.session.get('selected_role') != 'seller':
        messages.error(request, "Invalid role")
        return redirect('role_selection')

    context = {
        'google_email': request.session.get('google_email', ''),
        'google_first_name': request.session.get('google_first_name', ''),
        'google_last_name': request.session.get('google_last_name', ''),
    }
    return render(request, 'seller/google_seller_form.html', context)


def finalize_google_user(request):
    """Create user account with Google data"""
    if request.method != "POST":
        return redirect('login')

    if not request.session.get('pending_google_signup'):
        messages.error(request, "Session expired. Please try again.")
        return redirect('login')

    # Get form data
    username = request.POST.get('username', '').strip()
    phone = request.POST.get('phone', '').strip()

    # Get Google data from session
    email = request.session.get('google_email')
    first_name = request.session.get('google_first_name', '')
    last_name = request.session.get('google_last_name', '')

    # Validation
    if not username:
        messages.error(request, "Username is required")
        return redirect('google_user_form')

    if User.objects.filter(username=username).exists():
        messages.error(request, "Username already taken. Please choose another.")
        return redirect('google_user_form')

    if User.objects.filter(email=email).exists():
        messages.error(request, "An account with this email already exists.")
        return redirect('login')

    try:
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        # If you have a phone field in your User model, save it
        # user.phone = phone
        # user.save()

        # Log the user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Clear session data
        request.session.pop('pending_google_signup', None)
        request.session.pop('google_email', None)
        request.session.pop('google_first_name', None)
        request.session.pop('google_last_name', None)
        request.session.pop('google_picture', None)
        request.session.pop('selected_role', None)

        messages.success(request, f"Welcome {first_name}! Your account has been created successfully.")
        return redirect('home')  # Change to your home page URL name

    except Exception as e:
        messages.error(request, f"Error creating account: {str(e)}")
        return redirect('google_user_form')


def finalize_google_seller(request):
    """Create seller account with Google data"""
    if request.method != "POST":
        return redirect('login')

    if not request.session.get('pending_google_signup'):
        messages.error(request, "Session expired. Please try again.")
        return redirect('login')

    # Get form data
    username = request.POST.get('username', '').strip()
    shop_name = request.POST.get('shop_name', '').strip()
    shop_type = request.POST.get('shop_type', '').strip()
    shop_address = request.POST.get('shop_address', '').strip()
    gst_number = request.POST.get('gst_number', '').strip()
    bank_account_number = request.POST.get('bank_account_number', '').strip()

    # Get Google data from session
    email = request.session.get('google_email')
    first_name = request.session.get('google_first_name', '')
    last_name = request.session.get('google_last_name', '')

    # Validation
    if not username:
        messages.error(request, "Username is required")
        return redirect('google_seller_form')

    if not all([shop_name, shop_type, shop_address, gst_number, bank_account_number]):
        messages.error(request, "All seller fields are required")
        return redirect('google_seller_form')

    if User.objects.filter(username=username).exists():
        messages.error(request, "Username already taken. Please choose another.")
        return redirect('google_seller_form')

    if User.objects.filter(email=email).exists():
        messages.error(request, "An account with this email already exists.")
        return redirect('login')

    try:
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        # Create seller profile
        seller = Seller.objects.create(
            user=user,
            shop_name=shop_name,
            shop_type=shop_type,
            shop_address=shop_address,
            gst_number=gst_number,
            bank_account_number=bank_account_number
        )

        # Log the user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Clear session data
        request.session.pop('pending_google_signup', None)
        request.session.pop('google_email', None)
        request.session.pop('google_first_name', None)
        request.session.pop('google_last_name', None)
        request.session.pop('google_picture', None)
        request.session.pop('selected_role', None)

        messages.success(request, f"Welcome {first_name}! Your seller account has been created successfully.")
        return redirect('seller_dashboard')

    except Exception as e:
        # If seller creation fails, delete the user
        if 'user' in locals():
            user.delete()
        messages.error(request, f"Error creating seller account: {str(e)}")
        return redirect('google_seller_form')

def seller_products(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get seller object of logged-in user
    try:
        seller = Seller.objects.get(user=request.user)
    except Seller.DoesNotExist:
        return HttpResponse("Seller profile not found!")

    # Query products correctly
    products = Product.objects.filter(seller=seller)

    if request.method == "POST":
        Product.objects.create(
            seller=seller,
            title=request.POST['title'],
            description=request.POST['description'],
            price=request.POST['price'],
            stock=request.POST['stock'],
            image=request.FILES.get('image')
        )
        return redirect('seller_products')

    return render(request, "seller/"
                           "seller_product.html", {"products": products})


from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category

def add_product(request):
    seller = get_object_or_404(Seller, user=request.user)
    categories = Category.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        category_id = request.POST.get("category")

        product = Product.objects.create(
            seller=seller,
            category_id=category_id,
            title=title,
            description=description,
            price=price,
            stock=stock,
            slug=slugify(title)
        )

        # Handle image
        image_file = request.FILES.get("image")
        if image_file:
            ProductImage.objects.create(product=product, image=image_file)

        return redirect("seller_products")

    return render(request, "seller/add_product.html", {
        "categories": categories
    })
def update_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    subcategories = SubCategory.objects.all()

    if request.method == "POST":
        product.sub_category_id = request.POST.get("sub_category")
        product.title = request.POST.get("product_name")
        product.price = request.POST.get("price")
        product.stock = request.POST.get("stock")
        product.rating = request.POST.get("rating")
        product.slug = request.POST.get("slug")
        product.description = request.POST.get("description")
        product.save()

        # SAVE MULTIPLE IMAGES
        images = request.FILES.getlist("images")
        for img in images:
            ProductImage.objects.create(product=product, image=img)

        # -------------------------------
        # 🔔 SEND NOTIFICATION TO SELLER
        # -------------------------------
        send_notification(
            user=request.user,
            message=f"Your product '{product.title}' has been updated successfully!"
        )

        return redirect('seller_products')

    return render(request, "seller/update_product.html", {
        "product": product,
        "subcategories": subcategories,
    })


def delete_product(request, slug):
    product = get_object_or_404(Product, slug=slug, seller__user=request.user)
    product.delete()
    return redirect("seller_products")

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # Load all reviews for this product
    reviews = product.reviews.all()   # because related_name = "reviews"

    return render(request, 'seller/product_detail.html', {
        'product': product,
        'reviews': reviews,
    })


from django.shortcuts import render, get_object_or_404

from django.core.paginator import Paginator

def seller_orders(request):
    status_filter = request.GET.get('status')

    # Map URL filters to model values
    STATUS_MAP = {
        'pending': 'PENDING',
        'processing': 'PROCESSING',
        'placed': 'PLACED',
        'shipped': 'SHIPPED',
        'delivered': 'DELIVERED',
        'cancelled': 'CANCELLED',
    }

    if status_filter:
        mapped_status = STATUS_MAP.get(status_filter)
        if mapped_status:
            orders = Order.objects.filter(order_status=mapped_status)
        else:
            orders = Order.objects.all()
    else:
        orders = Order.objects.all()

    # -------- PAGINATION ----------
    paginator = Paginator(orders, 3)  # 5 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'seller/seller_orders.html', {
        'orders': page_obj,         # important
        'page_obj': page_obj,
        'status_filter': status_filter,
    })

@login_required
def order_detail(request, order_id):
    """View individual order details"""
    try:
        # Check if user is a seller
        try:
            seller = Seller.objects.get(user=request.user)
        except Seller.DoesNotExist:
            messages.error(request, "Seller profile not found.")
            return redirect('seller_dashboard')

        # Get seller's products
        seller_products = Product.objects.filter(seller=seller)

        # Get order items that belong to this seller
        order_items = OrderItem.objects.filter(
            order_id=order_id,
            product__in=seller_products
        ).select_related('order', 'product')

        if not order_items.exists():
            messages.error(request, "Order not found or doesn't contain your products.")
            return redirect('seller_orders')

        # Get the order from the first order item (all items belong to same order)
        order = order_items.first().order

        # Calculate totals and add image data
        seller_total = 0
        total_quantity = 0

        for item in order_items:
            item.total_price = float(item.price_at_purchase) * int(item.quantity)
            seller_total += item.total_price
            total_quantity += item.quantity

            try:
                first_img = item.product.images.first()
                item.first_image = first_img.image.url if first_img else None
            except Exception as img_error:
                item.first_image = None

        context = {
            'order': order,
            'order_items': order_items,
            'seller_total': seller_total,
            'total_quantity': total_quantity,
            'seller': seller,
        }

        return render(request, 'seller/order_detail.html', context)

    except Exception as e:
        messages.error(request, f"Error loading order details: {str(e)}")
        return redirect('seller_orders')


@login_required
def update_order_status(request, order_id):
    """Update order status"""
    if request.method == "POST":
        try:
            # Check if user is a seller
            try:
                seller = Seller.objects.get(user=request.user)
            except Seller.DoesNotExist:
                messages.error(request, "Seller profile not found.")
                return redirect('seller_dashboard')

            # Get the order and verify it contains seller's products
            seller_products = Product.objects.filter(seller=seller)
            order_items = OrderItem.objects.filter(
                order_id=order_id,
                product__in=seller_products
            )

            if not order_items.exists():
                messages.error(request, "Order not found or doesn't contain your products.")
                return redirect('seller_orders')

            order = order_items.first().order
            new_status = request.POST.get('status')

            if new_status:
                order.order_status = new_status
                order.save()

                messages.success(request, f"Order status updated to {order.get_order_status_display()}.")

        except Exception as e:
            messages.error(request, f"Error updating order status: {str(e)}")

    return redirect('order_detail', order_id=order_id)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm


@login_required
def seller_profile(request):
    user = request.user

    # Initialize context with default values
    context = {
        "phone": request.session.get("phone", ""),
        "birth_date": request.session.get("birth_date", ""),
        "gender": request.session.get("gender", ""),
        "email_notifications": request.session.get("email_notifications", True),
        "sms_notifications": request.session.get("sms_notifications", False),
        "two_factor_auth": request.session.get("two_factor_auth", False),
        "marketing_emails": request.session.get("marketing_emails", False),
        "store_name": request.session.get("store_name", "TechGadgets Inc."),
        "store_description": request.session.get("store_description",
                                                 "We specialize in the latest smartphones, laptops, headphones, and smart home devices."),
        "store_category": request.session.get("store_category", "electronics"),
        "store_currency": request.session.get("store_currency", "USD"),
    }

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "personal_info":
            # Handle personal information update
            user.first_name = request.POST.get("firstName", "")
            user.last_name = request.POST.get("lastName", "")
            user.email = request.POST.get("email", "")
            user.save()

            # Save extra values to session
            request.session["phone"] = request.POST.get("phone", "")
            request.session["birth_date"] = request.POST.get("birthDate", "")
            request.session["gender"] = request.POST.get("gender", "")

            messages.success(request, "Profile updated successfully!")
            return redirect("seller_profile")

        elif form_type == "change_password":
            # Handle password change
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            elif len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, "Password changed successfully!")

            return redirect("seller_profile")

        elif form_type == "account_settings":
            # Handle account settings
            request.session["email_notifications"] = "email_notifications" in request.POST
            request.session["sms_notifications"] = "sms_notifications" in request.POST
            request.session["two_factor_auth"] = "two_factor_auth" in request.POST
            request.session["marketing_emails"] = "marketing_emails" in request.POST

            messages.success(request, "Account settings updated successfully!")
            return redirect("seller_profile")

        elif form_type == "store_settings":
            # Handle store settings
            request.session["store_name"] = request.POST.get("store_name", "")
            request.session["store_description"] = request.POST.get("store_description", "")
            request.session["store_category"] = request.POST.get("store_category", "electronics")
            request.session["store_currency"] = request.POST.get("store_currency", "USD")

            messages.success(request, "Store settings updated successfully!")
            return redirect("seller_profile")

    return render(request, "seller/seller_profile.html", context)

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_seller(request):
    logout(request)
    return redirect('login')   # change to your login page name
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from seller.models import Notification

def send_notification(user, message):
    # Save DB
    Notification.objects.create(
        user=user,
        title="Product Update",
        message=message
    )

    # Send real-time
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "notify",
            "message": message
        }
    )

# send_notification("New user registered!")

def notification_page(request):
    seller = Seller.objects.get(user=request.user)
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    # Mark notifications as read
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "seller/notifications.html", {"notifications": notifications,'seller':seller,"unread_count":unread_count})