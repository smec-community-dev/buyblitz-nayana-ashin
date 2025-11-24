

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages,auth
from django.template.defaultfilters import title
from user.models import Order,OrderItem,Review
from core.models import User,Category
from django.shortcuts import get_object_or_404

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
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))

        request.session["buy_now"] = {
            "product_id": product_id,
            "quantity": quantity
        }

        return redirect("checkout")

    return redirect("single_view", slug=Product.objects.get(id=product_id).slug)


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



@login_required
def single_view(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # ⭐ Selected image logic (for switching images)
    image_id = request.GET.get("image_id")
    selected_image = None
    if image_id:
        try:
            selected_image = product.images.get(id=image_id)
        except ProductImage.DoesNotExist:
            selected_image = None

    # Wishlist & cart details
    wishlist_ids = []
    wishlist_count = 0
    cart_count = 0

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        cart_count = Cart.objects.filter(user=request.user).count()

    # ⭐ Check if user already reviewed
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(
            user=request.user,
            product=product
        ).first()

    # ⭐ Check if user is allowed to review (must be delivered)
    can_review = False
    if request.user.is_authenticated:
        delivered_items = OrderItem.objects.filter(
            order__user=request.user,
            order__order_status="DELIVERED",
            product=product
        )

        if delivered_items.exists():
            can_review = True

    # ⭐ Review submission
    if request.method == "POST" and can_review and not user_review:
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        if not rating:
            messages.error(request, "Please select a rating")
        else:
            Review.objects.create(
                user=request.user,
                product=product,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Review submitted successfully!")
            return redirect(f"/user/product/{product.slug}/")

    return render(request, "user/product_view.html", {
        "product": product,
        "selected_image": selected_image,   # ⭐ IMPORTANT
        "wishlist_ids": list(wishlist_ids),
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,
        "user_review": user_review,
        "can_review": can_review,
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
        return redirect("products")

    user = request.user

    # ✅ Get quantity from product page (+ / - buttons)
    quantity = int(request.POST.get("quantity", 1))

    # Create or update cart item
    cart_item, created = Cart.objects.get_or_create(
        user=user,
        product=product
    )

    if created:
        # First time adding product
        cart_item.quantity = quantity
    else:
        # Already in cart → increase quantity
        cart_item.quantity += quantity

    cart_item.save()

    return redirect("cart")

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
@login_required
def update_cart(request, id):
    item = get_object_or_404(Cart, id=id, user=request.user)
    action = request.POST.get("action")

    if action == "increment":
        item.quantity += 1
    elif action == "decrement":
        if item.quantity > 1:
            item.quantity -= 1

    item.save()
    return redirect("cart")


def remove_cart(request, id):
    if request.method == "POST":
        try:
            cart_item = Cart.objects.get(id=id, user=request.user)
            cart_item.delete()
        except Cart.DoesNotExist:
            pass

        return redirect("cart")   # FIXED URL NAME

    return redirect("cart")


@login_required
def checkout(request):


    # If user coming from cart → remove old buy_now session
    if request.GET.get("from_cart"):
        if "buy_now" in request.session:
            del request.session["buy_now"]



    buy_now_data = request.session.get("buy_now")

    # BUY NOW MODE
    if buy_now_data:
        product = Product.objects.get(id=buy_now_data["product_id"])
        quantity = buy_now_data["quantity"]
        total = product.price * quantity

        return render(request, "user/checkout.html", {
            "mode": "buy_now",
            "product": product,
            "quantity": quantity,
            "total": total,          # ✅ FIXED (was total_amount)
            "total_amount": total,   # Optional if HTML uses this
        })

    # CART MODE
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.subtotal for item in cart_items)

    return render(request, "user/checkout.html", {
        "mode": "cart",
        "cart_items": cart_items,
        "total": total_amount,        # ✅ FIXED (added)
        "total_amount": total_amount, # Already correct
    })






def order_detail(request):
    return render(request, 'user/order.html')





@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'user/order_history.html', {
        "orders": orders
    })





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


# def order_history(request):
#     return render(request, 'user/order_history.html')


@login_required
def place_order(request):
    if request.method != "POST":
        return redirect("checkout")  # if someone loads directly

    mode = request.POST.get("mode")

    # BUY NOW
    if mode == "buy_now":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))

        product = Product.objects.get(id=product_id)
        total = product.price * quantity

        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            full_name=request.POST.get("full_name"),

            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            pincode=request.POST.get("pincode"),
            payment_method=request.POST.get("payment_method"),
        )

        # Create OrderItem
        OrderItem.objects.create(
            order=order,
            product=product,
            product_title=product.title,
            quantity=quantity,
            price_at_purchase=product.price
        )

        return redirect("order_success", order_number=order.order_number)

    # CART CHECKOUT
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.subtotal for item in cart_items)

    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        full_name=request.POST.get("full_name"),

    phone=request.POST.get("phone"),
        address=request.POST.get("address"),
        city=request.POST.get("city"),
        state=request.POST.get("state"),
        pincode=request.POST.get("pincode"),
        payment_method=request.POST.get("payment_method"),
    )

    # Create Order Items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_title=item.product.title,
            quantity=item.quantity,
            price_at_purchase=item.product.price
        )

    # Clear cart
    cart_items.delete()

    return redirect("order_success", order_number=order.order_number)


def order_success(request, order_number):
    order = Order.objects.get(order_number=order_number)
    return render(request, "user/order_success.html", {"order": order})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # wishlist and cart counts
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    cart_count = Cart.objects.filter(user=request.user).count()

    # Mark each item whether user reviewed or not
    for item in order.items.all():
        if item.product:
            item.user_has_reviewed = item.product.reviews.filter(user=request.user).exists()
        else:
            item.user_has_reviewed = True  # no product = no review button

    return render(request, "user/order.html", {
        "order": order,
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,
    })


@login_required
def add_review(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    # Only allow review if delivered
    if item.order.order_status != "DELIVERED":
        return redirect("order_history")

    # Prevent duplicate review
    if Review.objects.filter(product=item.product, user=request.user).exists():
        return redirect("order_history")

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        Review.objects.create(
            product=item.product,
            user=request.user,
            rating=rating,
            comment=comment
        )

        return redirect("order_history")

    return render(request, "user/add_review.html", {"item": item})
