

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages,auth
from django.template.defaultfilters import title

from core.models import User,Category
from django.db.models import Q
from seller.models import Product
from user.models import Wishlist,Cart
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
    # return render(request, "user/order.html", {"orders": orders})

    # placeholder for now:
    return render(request, "user/order.html")


@login_required
def profile(request):
    return render(request, "user/profile.html", {
        "user": request.user
    })


def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        # create order instantly or redirect to checkout
        return redirect('checkout', product_id=product.id)

    return redirect('login')


def register_user(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        phone = request.POST.get("phone", "")

        if not first_name:
            messages.error(request, "First name is required.")
            return redirect("register")

        # username = email.split("@")[0]
        # username from first name
        username = first_name.lower().replace(" ", "_")


        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        # Create profile with phone number
        # Profile.objects.create(
        #     user=user,
        #     phone=phone
        # )

        user.set_password(password)
        user.save()

        return redirect("login")

    return render(request, "user/registration.html")
@login_required
def update_personal_info(request):
    user = request.user

    if request.method == "POST":
        # Update User fields
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.bio = request.POST.get("bio")

        # Update profile picture (optional)
        if "profile_picture" in request.FILES:
            user.profile_picture = request.FILES["profile_picture"]

        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("personal_info")

    return render(request, "user/personal-info.html", {
        "user": user
    })



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


           # product

def products(request):

    # GET PARAMETERS
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "featured")
    selected_categories = request.GET.getlist("category")

    # BASE QUERYSET
    products_qs = Product.objects.all()

    # CATEGORY FILTER
    if selected_categories:
        products_qs = products_qs.filter(category__name__in=selected_categories)

    # SEARCH FILTER
    if query:
        products_qs = products_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # SORTING
    if sort == "price-low":
        products_qs = products_qs.order_by("price")
    elif sort == "price-high":
        products_qs = products_qs.order_by("-price")
    elif sort == "newest":
        products_qs = products_qs.order_by("-id")
    else:
        products_qs = products_qs.order_by("-id")  # Featured DEFAULT

    # PAGINATION
    paginator = Paginator(products_qs, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # PRESERVE FILTERS WHEN PAGINATING
    base_qs = request.GET.copy()
    if "page" in base_qs:
        base_qs.pop("page")
    base_querystring = base_qs.urlencode()

    # VALID PAGES
    valid_pages = [num for num in paginator.page_range if paginator.page(num).object_list.exists()]

    # WISHLIST / CART COUNTS
    wishlist_ids = []
    wishlist_count = cart_count = 0

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        cart_count = Cart.objects.filter(user=request.user).count()

    categories = Category.objects.all()

    return render(request, "user/product.html", {
        "page_obj": page_obj,
        "base_querystring": base_querystring,
        "valid_pages": valid_pages,

        "wishlist_ids": list(wishlist_ids),
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,

        "query": query,
        "sort": sort,
        "categories": categories,
        "selected_categories": selected_categories
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




def search_results(request):
    query = request.GET.get("q", "")

    results = Product.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query)
    )

    wishlist_ids = []
    wishlist_count = 0
    cart_count = 0

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        cart_count = Cart.objects.filter(user=request.user).count()

    return render(request, "user/search.html", {
        "query": query,
        "results": results,
        "wishlist_ids": list(wishlist_ids),
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,
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



def profile_dashboard(request):
    return render(request,'user/profile_dashboard.html')

def personal_info(request):
    return render(request, 'user/personal_info.html')


def change_password(request):
    return render(request, 'user/change_password.html')


def account_settings(request):
    return render(request, 'user/account_settings.html')


def order_history(request):
    return render(request, 'user/order_history.html')


