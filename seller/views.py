from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.text import slugify

from core.models import User, SubCategory
from seller.models import Seller, Product, ProductImage
from user.models import Order, OrderItem
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ProductImage
from django.contrib.auth import get_user_model



def seller_dashboard(request):

    return render(request, 'seller/seller_dashboard.html')

def register_seller(request):
    if request.method == "POST":

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # Seller fields
        shop_name = request.POST.get("shop_name")
        shop_type = request.POST.get("shop_type")
        shop_address = request.POST.get("shop_address")
        gst_number = request.POST.get("gst_number")
        bank_account_number = request.POST.get("bank_account_number")

        # Check username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("seller_register")

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        # Create seller ONLY if role == seller
        if role == "seller":
            Seller.objects.create(
                user=user,
                shop_name=shop_name,
                shop_type=shop_type,
                shop_address=shop_address,
                gst_number=gst_number,
                bank_account_number=bank_account_number
            )

        messages.success(request, "Registration successful!")
        return redirect("login")

    return render(request, "seller/register.html")






from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from core.models import User
from seller.models import Seller

def login_seller(request):
    print("..................")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username,password)
        User = get_user_model()
        # Allow login using email OR username
        if User.objects.filter(email=username).exists():
            user_obj = User.objects.get(email=username)
            username = user_obj.username

        user = authenticate(request, username=username, password=password)
        print(user)

        if user is not None:
            login(request, user)

            # Check if seller
            if Seller.objects.filter(user=user).exists():
                print("........")
                return redirect('seller_dashboard')

            return redirect('home')

        # Error message when login fails
        return render(request, "seller/login.html", {"error": "Invalid username or password"})

    return render(request, "seller/login.html")


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





def seller_products(request):
    seller = get_object_or_404(Seller, user=request.user)
    products = Product.objects.filter(seller=seller).order_by("-created_at")
    categories = Category.objects.all()

    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    return render(request, "seller/seller_product.html", {
        "products": products,
        "categories": categories,
    })
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
        product.title = request.POST.get("product_name")   # title field
        product.price = request.POST.get("price")
        product.stock = request.POST.get("stock")
        product.rating = request.POST.get("rating")
        product.slug = request.POST.get("slug")
        product.description = request.POST.get("description")
        product.save()

        # SAVE MULTIPLE IMAGES
        images = request.FILES.getlist("images")
        for img in images:
            ProductImage.objects.create(
                product=product,
                image=img          # correct field name
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

def seller_orders(request):
    status_filter = request.GET.get('status')

    # Map URL filters to model values
    STATUS_MAP = {
        'pending': 'PENDING',
        'processing': 'PROCESSING',
        'placed':'PLACED',# (or create PROCESSING if you want)
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

    return render(request, 'seller/seller_orders.html', {
        'orders': orders,
        'status_filter': status_filter
    })


def order_detail(request, id):
    order = get_object_or_404(Order, id=id)
    items = order.items.all()  # related_name="items"

    return render(request, 'seller/order_detail.html', {
        'order': order,
        'items': items
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def seller_profile(request):
    user = request.user

    context = {
        "phone": request.session.get("phone", ""),
        "birth_date": request.session.get("birth_date", ""),
        "gender": request.session.get("gender", "")
    }

    if request.method == "POST":
        user.first_name = request.POST.get("firstName")
        user.last_name = request.POST.get("lastName")
        user.email = request.POST.get("email")
        user.save()

        # Save extra values to session
        request.session["phone"] = request.POST.get("phone")
        request.session["birth_date"] = request.POST.get("birthDate")
        request.session["gender"] = request.POST.get("gender")

        messages.success(request, "Profile updated successfully!")
        return redirect("seller_profile")

    return render(request, "seller/seller_profile.html", context)




from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_seller(request):
    logout(request)
    return redirect('seller_login')   # change to your login page name


