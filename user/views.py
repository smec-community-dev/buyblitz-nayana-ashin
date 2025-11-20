

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages,auth
from core.models import User,Category
from django.db.models import Q
from seller.models import Product
from user.models import Wishlist,Cart
from django.http import JsonResponse

def home(request):
    categories = Category.objects.all()


    wishlist_count = 0
    cart_count = 0

    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        cart_count = Cart.objects.filter(user=request.user).count()

    return render(request, "user/home.html", {
        "products": products,
        "categories": categories,
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,
    })

@login_required
def orders(request):
    # If you have an Order model you can fetch user's orders:
    # orders = Order.objects.filter(user=request.user).order_by('-created_at')
    # return render(request, "user/orders.html", {"orders": orders})

    # placeholder for now:
    return render(request, "user/orders.html")
def profile(request):
    return render(request, "user/profile.html")




def register_user(request):
    if request.method == "POST":
        first_name = request.POST.get("first-name")
        last_name = request.POST.get("last-name")
        email = request.POST.get("email")
        password = request.POST.get("password")


        username = email.split("@")[0]

        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        user.set_password(password)
        user.save()

        return redirect("login")

    return render(request, "user/registration.html")




def login_user(request):
    if request.method == "POST":
        print("POST DATA:", request.POST)
        username = request.POST.get("username")
        password = request.POST.get("password")
        print("username:", username, "password present?:", bool(password))

        user = authenticate(request, username=username, password=password)
        print("authenticate returned:", user)

        if user is not None:
            login(request, user)
            return redirect("/user/home")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("/user/login")

    return render(request, "user/login.html")


def category(request):
    return render(request,'user/category.html')
from django.db.models import Q
def products(request):

    # SEARCH
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "featured")

    # MULTI-CATEGORY SUPPORT
    selected_categories = request.GET.getlist("category")

    # Base queryset
    products = Product.objects.all()

    # Apply MULTIPLE category filters
    if selected_categories:
        products = products.filter(category__name__in=selected_categories)

    # Apply search
    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Sorting
    if sort == "price-low":
        products = products.order_by("price")
    elif sort == "price-high":
        products = products.order_by("-price")
    elif sort == "newest":
        products = products.order_by("-id")

    # Wishlist + Cart
    wishlist_ids = []
    wishlist_count = 0
    cart_count = 0

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        cart_count = Cart.objects.filter(user=request.user).count()

    # SEND NEW VARIABLES
    categories = Category.objects.all()

    return render(request, "user/product.html", {
        "products": products,
        "wishlist_ids": list(wishlist_ids),
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,

        "query": query,
        "sort": sort,

        # NEW
        "categories": categories,
        "selected_categories": selected_categories,
    })



def update_cart(request, item_id):
    if request.method == "POST":
        action = request.POST.get("action")
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)

        if action == "increment":
            cart_item.quantity += 1
        elif action == "decrement":
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return redirect("cart")

        cart_item.save()
    return redirect("cart")


def deals(request):
    # query whatever deals data you need
    return render(request, 'user/deals.html', {})
def about(request):
    return render(request, 'user/about.html')
def contact(request):
    return render(request, 'user/contact.html')
def trending(request):
    return render(request, 'user/trending.html')

def category_products(request, category_name):
    products = Product.objects.filter(category__name__iexact=category_name)

    return render(request, "user/category.html", {
        "category_name": category_name,
        "products": products,
    })


def toggle_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return redirect("login")

    item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product_id=product_id
    )

    if not created:
        item.delete()  # If already exists → remove

    return redirect("products")  # refresh page




def single_view(request, slug):
    product = Product.objects.get(slug=slug)

    wishlist_ids = []
    wishlist_count = 0
    cart_count = 0

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        cart_count = Cart.objects.filter(user=request.user).count()

    return render(request, "user/product_view.html", {
        "product": product,
        "wishlist_ids": list(wishlist_ids),
        "wishlist_count": wishlist_count,
        "cart_count": cart_count
    })






def trending(request):
    return render(request,'user/trending.html')

def search(request):
    query = request.GET.get("q", "")

    results = Product.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query)
    )

    return render(request, "user/search.html", {
        "query": query,
        "results": results
    })







@login_required
def add_to_cart(request, id):
    try:
        product = Product.objects.get(id=id)
    except Product.DoesNotExist:
        return redirect("products")   # If product not found

    user = request.user

    cart_item, created = Cart.objects.get_or_create(
        user=user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect("cart")   # <-- GO TO CART PAGE
def wishlist_page(request):
    items = Wishlist.objects.filter(user=request.user)

    wishlist_count = items.count()
    # cart_count = Cart.objects.filter(user=request.user).count()

    return render(request, "user/wishlist.html", {
        "items": items,
        "wishlist_count": wishlist_count,

    })



@login_required
def cart_page(request):
    user = request.user


    cart_items = Cart.objects.filter(user=user).select_related("product")

    total_amount = sum(item.subtotal for item in cart_items)
    # wishlist_count = Wishlist.objects.filter(user=request.user).count()
    cart_count = cart_items.count()

    return render(request, "user/cart.html", {
        "cart_items": cart_items,
        "total_amount": total_amount,
        # "wishlist_count": wishlist_count,
        "cart_count": cart_count,
    })
@login_required
def add_to_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)

    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if not created:
        item.delete()

    return redirect("products")



@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect('wishlist')   # or redirect("/user/wishlist/") if name differs
def update_cart(request, cart_id):
    action = request.GET.get("action")
    item = Cart.objects.get(id=cart_id, user=request.user)

    if action == "inc":
        item.quantity += 1
    elif action == "dec" and item.quantity > 1:
        item.quantity -= 1

    item.save()

    return JsonResponse({"qty": item.quantity, "total": item.subtotal})



def remove_cart(request, id):
    if request.method == "POST":
        try:
            cart_item = Cart.objects.get(id=id, user=request.user)
            cart_item.delete()
        except Cart.DoesNotExist:
            pass

        return redirect("cart")   # FIXED URL NAME

    return redirect("cart")


def checkout_page(request):
    return render(request, "user/checkout.html")






def logout_user(request):
    logout(request)
    return redirect("login")

def categories(request):
    return render(request, 'user/category.html')

