from .models import Cart, Wishlist

def cart_wishlist_count(request):

    if request.user.is_authenticated:

        cart_count = Cart.objects.filter(
            user=request.user
        ).count()

        wishlist_count = Wishlist.objects.filter(
            user=request.user
        ).count()

    else:

        cart_count = 0
        wishlist_count = 0

    return {

        "cart_count": cart_count,

        "wishlist_count": wishlist_count,

    }