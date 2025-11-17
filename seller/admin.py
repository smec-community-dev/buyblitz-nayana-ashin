from django.contrib import admin



# Register your models here.
from seller.models import Product,ProductImage,Seller


admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Seller)

