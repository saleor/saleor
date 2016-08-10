from .models import Cart


def get_user_open_cart_token(user):
    user_carts_tokens = list(
        user.carts.open().values_list('token', flat=True))
    if len(user_carts_tokens) > 1:
        # logger.warning('%s has more then one open basket')
        user.carts.open().exclude(token=user_carts_tokens[0]).update(
            status=Cart.CANCELED)
    if user_carts_tokens:
        return user_carts_tokens[0]


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
    except Cart.DoesNotExist, TypeError:
        return {'cart_counter': 0}
    else:
        return {'cart_counter': cart.quantity}
