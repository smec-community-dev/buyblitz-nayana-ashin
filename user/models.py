from django.db import models


# 🛒 CART MODEL
class Cart(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    product = models.ForeignKey("product.Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user or self.session_id} - {self.product.title} (x{self.quantity})"

    @property
    def subtotal(self):
        return self.product.price * self.quantity


# 📦 ORDER MODEL
class Order(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    ORDER_STATUS_CHOICES = [
        ("PLACED", "Placed"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    order_status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="PLACED"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            from uuid import uuid4
            self.order_number = f"ORD-{uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)


# 🧾 ORDER ITEM MODEL
class OrderItem(models.Model):
    order = models.ForeignKey("order.Order", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("product.Product", on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"

    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity


# ⭐ PRODUCT REVIEW MODEL
class Review(models.Model):
    product = models.ForeignKey("product.Product", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey("user.User", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "user")  # 1 review per user per product
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.title} - {self.user.username} ({self.rating})"


# ❤️ WISHLIST MODEL
class Wishlist(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey("product.Product", on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} ❤️ {self.product.title}"
