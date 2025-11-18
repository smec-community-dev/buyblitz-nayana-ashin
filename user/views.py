

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages,auth
from core.models import User
from seller.models import Product
from user.models import Wishlist
from django.http import JsonResponse


def home(request):

    return render(request, "user/home.html")



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
def products(request):
    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    else:
        wishlist_count = 0




    products=Product.objects.all()
    return render(request,'user/product.html',{'products':products,"wishlist_count": wishlist_count,})



def single_view(request,slug):
    product = Product.objects.get(slug=slug)

    return render(request,'user/product_view.html',{'product':product})





def trending(request):
    return render(request,'user/trending.html')






def search(request):
    query = request.GET.get("q", "").lower()

    # Filter products
    results = [
        p for p in PRODUCTS
        if query in p["name"].lower()
        or query in p["category"].lower()
        or query in p["description"].lower()
    ]

    # Return to HOME PAGE
    return render(request, "user/home.html", {
        "products": results,
        "query": query
    })



@login_required
def add_to_cart(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
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
    if not request.user.is_authenticated:
        return redirect("login")

    items = Wishlist.objects.filter(user=request.user).select_related("product")

    return render(request, "user/wishlist.html", {"items": items})


@login_required
def cart_page(request):
    user = request.user

    # Get all items for the logged-in user
    cart_items = Cart.objects.filter(user=user).select_related("product")

    # Calculate total
    total_amount = sum(item.subtotal for item in cart_items)

    return render(request, "user/cart.html", {
        "cart_items": cart_items,
        "total_amount": total_amount
    })
@login_required
def add_to_wishlist(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Product not found"})

    user = request.user

    item, created = Wishlist.objects.get_or_create(user=user, product=product)

    if not created:
        item.delete()
        count = Wishlist.objects.filter(user=user).count()
        return JsonResponse({"status": "removed", "count": count})

    count = Wishlist.objects.filter(user=user).count()
    return JsonResponse({"status": "added", "count": count})


def logout_user(request):
    logout(request)
    return redirect("login")


