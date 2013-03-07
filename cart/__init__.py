from django.conf import settings
from django.utils.translation import ugettext
from prices import Price
from satchless import cart
from satchless.item import ItemSet, ItemLine, Item, ItemRange


class Shipping(Item):

    def get_price_per_item(self, **kwargs):
        return Price(5, currency=settings.SATCHLESS_DEFAULT_CURRENCY)


class DeliveryGroup(ItemSet):

    items = None

    def __init__(self, items):
        self.items = items or []

    def __iter__(self):
        for i in self.items:
            yield i

    def get_delivery_methods(self, **kwargs):
        yield Shipping(**kwargs)

    def get_min_delivery_method(self, **kwargs):
        return min(self.get_delivery_methods(),
                   key=lambda x: x.get_price_per_item(**kwargs))


def cart_partition(cart):
    yield DeliveryGroup(list(cart))


class InsufficientStockException(Exception):

    def __init__(self, product):
        super(InsufficientStockException, self).__init__(
            'Insufficient stock for %r' % (product,))
        self.product = product


class Cart(cart.Cart):

    SESSION_KEY = 'cart'

    def __unicode__(self):
        return ugettext('Your cart (%(cart_count)s)') % {
            'cart_count': self.count()}

    def check_quantity(self, product, quantity, data=None):
        if quantity > product.stock:
            raise InsufficientStockException(product)
        return super(Cart, self).check_quantity(product, quantity, data)


def get_cart_from_request(request):
    try:
        return request.session[Cart.SESSION_KEY]
    except KeyError:
        _cart = Cart()
        request.session[Cart.SESSION_KEY] = _cart
        return _cart
