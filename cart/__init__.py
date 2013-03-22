from delivery import DummyShipping, DigitalDelivery
from django.conf import settings
from django.utils.translation import ugettext
from itertools import groupby
from prices import Price
from product.models import StockedProduct, DigitalShip
from satchless import cart
from satchless.item import Item, ItemLine, ItemSet, Partitioner
from userprofile.forms import AddressForm
import datetime


class Group(ItemSet):

    _state = None
    default_error_messages = {
        'attribute_error': '\'%s\' object has no attribute \'%s\''
    }

    def __init__(self, items):
        super(Group, self).__init__(items)
        self._state = {}

    def __getstate__(self):
        self._state['pk'] = str(self)
        return self._state

    def __setstate__(self, state):
        self._state = state

    def __str__(self):
        raise NotImplementedError()

    def add_to_order(self, order):
        raise NotImplementedError()

    def get_delivery_methods(self, **kwargs):
        raise NotImplementedError()

    def get_delivery_total(self, **kwargs):
        methods = self.get_delivery_methods()
        return min(method.get_price_per_item(**kwargs) for method in methods)


class ShippedGroup(Group):

    def __init__(self, items, pk=None, address=None, delivery=None):
        super(Group, self).__init__(items)
        self.pk = pk
        self._state = {}
        self._state['address'] = address
        self._state['delivery'] = delivery

    def __str__(self):
        if self.pk:
            return 'delivery-' % (self.pk, )
        return 'delivery'

    @property
    def address(self):
        return self._state['address']

    @address.setter
    def address(self, value):
        self._state['address'] = value

    @address.deleter
    def address(self):
        del self._state['address']

    @property
    def delivery(self):
        if self._state['delivery'] != None:
            delivery_methods = list(self.get_delivery_methods())
            return delivery_methods[self._state['delivery']]

    @delivery.setter
    def delivery(self, value):
        delivery_methods = list(self.get_delivery_methods())
        self._state['delivery'] = delivery_methods.index(value)

    @delivery.deleter
    def delivery(self):
        del self._state['delivery']

    def add_to_order(self, order):
        raise NotImplementedError()

    def get_delivery_methods(self):
        yield DummyShipping(self)


class DigitalGroup(Group):

    def __init__(self, items, pk=None, email=None):
        super(Group, self).__init__(items)
        self.pk = pk
        self._state = {}
        self._state['email'] = email

    def __str__(self):
        if self.pk:
            return 'digital-delivery-' % (self.pk, )
        return 'digital-delivery'

    @property
    def email(self):
        return self._state['email']

    @email.setter
    def email(self, value):
        self._state['email'] = value

    @email.deleter
    def email(self):
        del self._state['email']

    def add_to_order(self, order):
        raise NotImplementedError()

    def get_delivery_methods(self, **kwargs):
        yield DigitalDelivery(self)


class CartPartitioner(Partitioner):

    def __iter__(self):
        for product_class, items in groupby(
                self.subject,
                lambda cart_item: cart_item.product.__class__):
            delivery_class = ShippedGroup
            if issubclass(product_class, DigitalShip):
                delivery_class = DigitalGroup
            delivery = delivery_class(items)
            yield delivery

    def get_delivery_subtotal(self, partion, **kwargs):
        return partion.get_delivery_total(**kwargs)

    def get_delivery_total(self, **kwargs):
        items = [self.get_delivery_subtotal(partion, **kwargs)
                 for partion in self]
        if not items:
            raise AttributeError(
                'Calling get_delivery_total() for an empty cart')
        return sum(items[1:], items[0])

    def _repr__(self):
        return 'CartPartitioner(%r)'%(list(self),)


class InsufficientStockException(Exception):

    def __init__(self, product):
        super(InsufficientStockException, self).__init__(
            'Insufficient stock for %r' % (product,))
        self.product = product


class Cart(cart.Cart):

    SESSION_KEY = 'cart'
    timestamp = None
    billing_address = None

    def __init__(self, *args, **kwargs):
        super(Cart, self).__init__(self, *args, **kwargs)
        self.timestamp = datetime.datetime.now()

    def __unicode__(self):
        return ugettext('Your cart (%(cart_count)s)') % {
            'cart_count': self.count()}

    def check_quantity(self, product, quantity, data=None):
        if (isinstance(product, StockedProduct) and
            quantity > product.stock):
            raise InsufficientStockException(product)
        return super(Cart, self).check_quantity(product, quantity, data)


def get_cart_from_request(request):
    try:
        return request.session[Cart.SESSION_KEY]
    except KeyError:
        _cart = Cart()
        request.session[Cart.SESSION_KEY] = _cart
        return _cart


def remove_cart_from_request(request):
    del request.session[Cart.SESSION_KEY]
