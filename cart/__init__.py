from django.conf import settings
from django.utils.translation import ugettext as _
from satchless import cart


class InsufficientStockException(Exception):

    def __init__(self, product):
        super(InsufficientStockException, self).__init__(
            'Insufficient stock for %r' % (product,))
        self.product = product


class Cart(cart.Cart):

    SESSION_KEY = 'cart'

    def __unicode__(self):
        return _('Cart (%(cart_count)s)' % {'cart_count': self.count()})

    def check_quantity(self, product, quantity, data=None):
        if quantity > product.stock:
            raise InsufficientStockException(product)
        return super(Cart, self).check_quantity(product, quantity, data)

    def get_default_currency(self):
        return settings.SATCHLESS_DEFAULT_CURRENCY


def get_cart_from_request(request):
    try:
        return request.session[Cart.SESSION_KEY]
    except KeyError:
        _cart = Cart()
        request.session[Cart.SESSION_KEY] = _cart
        return _cart
