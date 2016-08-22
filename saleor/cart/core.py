from datetime import timedelta

from .models import Cart


def set_cart_cookie(simple_cart, response):
    ten_years = timedelta(days=(365 * 10))
    response.set_signed_cookie(
        Cart.COOKIE_NAME, simple_cart.token, max_age=ten_years.total_seconds())
