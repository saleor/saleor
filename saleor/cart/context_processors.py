from .models import Cart
from .utils import get_user_open_cart_token


def cart_counter(request):
    """ Return number of items from cart """

    if request.user.is_authenticated():
        cart_token = get_user_open_cart_token(request.user)
        cart_queryset = request.user.carts
    else:
        cart_token = request.get_signed_cookie(
            Cart.COOKIE_NAME, default=None)
        cart_queryset = Cart.objects.anonymous()

    try:
        cart = cart_queryset.open().get(token=cart_token)
    except (Cart.DoesNotExist, TypeError, ValueError):
        return {'cart_counter': 0}
    else:
        return {'cart_counter': cart.quantity}
