

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages,auth
from core.models import User
from seller.models import Product


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
    products=Product.objects.all()
    return render(request,'user/product.html',{'products':products})



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


def logout_user(request):
    logout(request)
    return redirect("login")


