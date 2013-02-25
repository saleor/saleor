from decimal import Decimal
from django.conf import settings
from django.utils.translation import ugettext as _
from satchless.item import ItemSet, ItemLine
from satchless import cart


class InvalidQuantityException(Exception):

    def __init__(self, reason, quantity_delta):
        super(InvalidQuantityException, self).__init__(reason)
        self.quantity_delta = quantity_delta


class Cart(cart.Cart):

    SESSION_KEY = 'cart'
    modified = False

    def __unicode__(self):
        return _('Cart (%(cart_count)s)' % {'cart_count': self.count()})

    def check_quantity(self, product, quantity, replace=False):
        if quantity > product.stock:
            raise InvalidQuantityException(
                _(u'Only %(total)s of product in stock.' % {
                    'total':product.stock
                }),
                product.stock - quantity
            )

        return super(Cart, self).check_quantity(product, quantity, replace)

    def get_default_currency(self):
        return settings.SATCHLESS_DEFAULT_CURRENCY


def get_cart_from_request(request):
    try:
        return request.session[Cart.SESSION_KEY]
    except KeyError:
        _cart = Cart()
        request.session[Cart.SESSION_KEY] = _cart
        return _cart

