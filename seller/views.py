from os import remove

from django.shortcuts import render,redirect

from seller.models import Product


def view_product(request):
    data=Product.objects.all()
    return render(request,'seller/seller_dashboard.html')

#
# def delete_product(request,id):
#     data=Product.objects.get(id=id)
#     data.delete()
#     return redirect('/')


# def update_product(request,id):
#     data=Product.objects.get(id=id)
#     if request.method == "POST":
#         seller = request.POST.get('seller')
#         age = request.POST.get('age')
#         data.seller = seller
#         data.age = age
#         data.save()
#         return redirect('/')
#     return render(request,'seller/seller_product.html')