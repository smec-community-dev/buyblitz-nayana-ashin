from .models import Wishlist, Cart

def header_counts(request):
    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        cart_count = Cart.objects.filter(user=request.user).count()
    else:
        wishlist_count = 0
        cart_count = 0

    return {
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
    }
