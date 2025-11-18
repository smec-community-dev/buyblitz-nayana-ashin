import os
import django
import random
from faker import Faker
from PIL import Image, ImageDraw
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

fake = Faker()

from Core.models import User, Category, SubCategory
from Seller.models import Seller, Product, ProductImage
from User.models import Customer, Cart, Order, OrderItem, Wishlist, Review, ReviewImage


# ------------------ IMAGE GENERATOR --------------------
def generate_image(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    img = Image.new("RGB", (600, 600), color=(
        random.randint(50, 200),
        random.randint(50, 200),
        random.randint(50, 200)
    ))
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), text, fill="white")
    img.save(path)
    return path


# ------------------ REAL-WORLD PRODUCT DATA ---------------------

PRODUCT_DATA = {
    "Mobiles": [
        "iPhone 14 Pro Max", "Samsung Galaxy S23 Ultra", "OnePlus 11R",
        "Vivo V29 Pro", "Realme X7 Max"
    ],
    "Laptops": [
        "MacBook Air M2", "HP Pavilion Gaming", "Dell XPS 13",
        "Lenovo ThinkPad X1", "Asus ROG Strix G15"
    ],
    "Headphones": [
        "Sony WH-1000XM5", "JBL Tune 760", "Boat Rockerz 550",
        "Apple AirPods Pro", "Sennheiser HD450BT"
    ],
    "Mens Wear": [
        "Slim Fit Formal Shirt", "Denim Jacket", "Casual Cotton T-Shirt",
        "Regular Fit Jeans", "Hooded Sweatshirt"
    ],
    "Womens Wear": [
        "Floral Kurti", "Georgette Saree", "Crop Top",
        "Ladies Blazer", "Anarkali Dress"
    ],
    "Skincare": [
        "Vitamin C Serum", "Aloe Vera Gel", "Moisturizing Cream",
        "Sunscreen SPF 50", "Hydrating Face Wash"
    ],
    "Fitness": [
        "Yoga Mat", "Dumbbell Set", "Resistance Band",
        "Treadmill Machine", "Fitness Tracker Watch"
    ]
}

CATEGORY_MAPPING = {
    "Electronics": ["Mobiles", "Laptops", "Headphones"],
    "Fashion": ["Mens Wear", "Womens Wear"],
    "Beauty": ["Skincare"],
    "Sports": ["Fitness"],
}

# ------------------ USERS -------------------------
print("Creating Realistic Users...")

roles = ["admin", "seller", "customer"]

for i in range(15):
    User.objects.get_or_create(
        username=fake.user_name(),
        defaults={
            "password": "password123",
            "contact": fake.phone_number(),
            "role": random.choice(roles)
        }
    )

users = list(User.objects.all())

# ------------------ CATEGORIES -------------------------
print("Creating Categories...")

for cat in CATEGORY_MAPPING.keys():
    Category.objects.get_or_create(
        category_name=cat,
        defaults={
            "slug": slugify(cat),
            "description": fake.sentence()
        }
    )

categories = list(Category.objects.all())

# ------------------ SUBCATEGORIES -------------------------
print("Creating Subcategories...")

for cat in categories:
    for sub in CATEGORY_MAPPING[cat.category_name]:
        SubCategory.objects.get_or_create(
            category=cat,
            sub_category_name=sub,
            defaults={"description": fake.sentence()}
        )

subcategories = list(SubCategory.objects.all())

# ------------------ SELLERS -------------------------
print("Creating Realistic Sellers...")

seller_users = [u for u in users if u.role == "seller"]

for u in seller_users:
    img_path = f"media/seller_profiles/{u.username}.jpg"
    generate_image(img_path, text=u.username)

    Seller.objects.get_or_create(
        user=u,
        defaults={
            "shop_name": fake.company(),
            "address": fake.address(),
            "website": fake.url(),
            "profile_image": f"seller_profiles/{u.username}.jpg"
        }
    )

sellers = list(Seller.objects.all())

# ------------------ PRODUCTS -------------------------
print("Creating Realistic Products with REAL Names...")

product_list = []

for subcat in subcategories:
    name_list = PRODUCT_DATA.get(subcat.sub_category_name, [])
    if not name_list:
        continue

    for name in name_list:
        product_list.append((subcat, name))

random.shuffle(product_list)

# limit to 30
product_list = product_list[:30]

products_created = []

for subcat, prod_name in product_list:

    seller = random.choice(sellers)
    price = random.randint(300, 80000)

    product = Product.objects.create(
        seller=seller,
        sub_category=subcat,
        product_name=prod_name,
        price=price,
        description=fake.paragraph(),
        slug=slugify(prod_name),
        rating=round(random.uniform(3, 5), 1),
        stock=random.randint(5, 50)
    )

    for img_i in range(random.randint(2, 4)):
        path = f"media/products/{product.id}_{img_i}.jpg"
        generate_image(path, text=prod_name)
        ProductImage.objects.create(
            product=product,
            product_img=f"products/{product.id}_{img_i}.jpg"
        )

    products_created.append(product)

products = products_created

# ------------------ CUSTOMERS -------------------------
print("Creating Realistic Customers...")

customer_users = [u for u in users if u.role == "customer"]

for u in customer_users:
    path = f"media/profiles/{u.username}.jpg"
    generate_image(path, text=u.username)

    Customer.objects.get_or_create(
        user=u,
        defaults={
            "address": fake.address(),
            "profile_img": f"profiles/{u.username}.jpg"
        }
    )

# ------------------ CART -------------------------
print("Creating Realistic Cart Items...")

for cu in customer_users:
    for _ in range(2):
        Cart.objects.create(
            user=cu,
            product=random.choice(products),
            quantity=random.randint(1, 3)
        )

# ------------------ ORDERS -------------------------
print("Creating Realistic Orders...")

for cu in customer_users:
    order = Order.objects.create(
        user=cu,
        total_amount=random.randint(800, 20000),
        shipping_address=fake.address()
    )

    for _ in range(random.randint(1, 4)):
        OrderItem.objects.create(
            order=order,
            product=random.choice(products),
            quantity=random.randint(1, 3)
        )

# ------------------ WISHLIST -------------------------
print("Creating Wishlists...")

for cu in customer_users:
    for _ in range(2):
        Wishlist.objects.create(
            user=cu,
            product=random.choice(products)
        )

# ------------------ REVIEWS -------------------------
print("Creating Realistic Reviews...")

REVIEW_TEXTS = [
    "Amazing product, totally worth it!",
    "Good quality for this price.",
    "I am not fully satisfied.",
    "Best purchase of the year!",
    "Highly recommended!"
]

for cu in customer_users:
    for _ in range(3):
        product = random.choice(products)

        review = Review.objects.create(
            user=cu,
            product=product,
            review=random.choice(REVIEW_TEXTS),
            rating=random.randint(3, 5)
        )

        img = f"media/review_images/{review.id}.jpg"
        generate_image(img, text="Review")
        ReviewImage.objects.create(
            review=review,
            review_img=f"review_images/{review.id}.jpg"
        )

print("🌟 SUPER REALISTIC Dummy Data Created Successfully!")
