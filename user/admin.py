from django.contrib import admin
from .models import Cart,Order,OrderItem,Review,Wishlist



# from .models import User
#
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ("id", "first_name", "last_name", "email")


admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Wishlist)

# Register your models here.
