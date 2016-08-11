from __future__ import unicode_literals

from functools import wraps

from .models import Cart


def assign_anonymous_cart(view):
    """If user is authenticated, assign cart from current session"""

    @wraps(view)
    def func(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        if request.user.is_authenticated():
            cookie = request.get_signed_cookie(Cart.COOKIE_NAME, default=None)
            if cookie:
                try:
                    cart = Cart.objects.open().get(token=cookie)
                except Cart.DoesNotExist:
                    pass
                else:
                    if cart.user is None:
                        request.user.carts.open().update(status=Cart.CANCELED)
                        cart.user = request.user
                        cart.save(update_fields=['user'])
                response.delete_cookie(Cart.COOKIE_NAME)

        return response
    return func




