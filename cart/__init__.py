from delivery import DummyShipping, DigitalDelivery
from django.conf import settings
from django.utils.translation import ugettext
from itertools import groupby
from prices import Price
from product.models import StockedProduct, DigitalShip
from satchless import cart
from satchless.item import Item, ItemLine, ItemSet, Partitioner
import datetime


class BaseGroup(list, ItemSet):
    '''
    Base Saleor cart group. It is used in cart and checkout to group products
    depends on delivery methods.
    '''
    delivery_method = None

    def __init__(self, items, delivery_method=None):
        super(BaseGroup, self).__init__(items)
        if delivery_method and delivery_method not in self.delivery_method():
            raise AttributeError('Bad delivery method')
        self.delivery_method = delivery_method

    def get_delivery_methods(self, **kwargs):
        '''
        Method should returns iterable object with delivery groups.
        '''
        raise NotImplementedError()

    def get_delivery_total(self, **kwargs):
        '''
        Method returns price from the self.delivery_method or lowest price
        form delivery methods.
        '''
        if self.delivery_method:
            return self.delivery_method.get_price_per_item(**kwargs)
        methods = self.get_delivery_methods()
        return min(method.get_price_per_item(**kwargs) for method in methods)


class ShippedGroup(BaseGroup):
    '''
    Group for shippable products.
    '''
    def get_delivery_methods(self):
        '''
        Returns shippable delivery methods.
        '''
        yield DummyShipping(self)


class DigitalGroup(BaseGroup):
    '''
    Group for digital products.
    '''
    def get_delivery_methods(self, **kwargs):
        '''
        Returns digital delivery methods.
        '''
        yield DigitalDelivery(self)


class CartPartitioner(Partitioner):
    '''
    Dividing cart into groups.
    '''
    def __iter__(self):
        '''
        Change this method to provide custom delivery groups.
        '''
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

    def get_total(self):
        total = super(CartPartitioner, self).get_total()
        return total + self.get_delivery_total()

    def __repr__(self):
        return 'CartPartitioner(%r)' % (list(self),)


class InsufficientStockException(Exception):
    '''An error while validating product stock.'''
    def __init__(self, product):
        super(InsufficientStockException, self).__init__(
            'Insufficient stock for %r' % (product,))
        self.product = product


class Cart(cart.Cart):
    '''
    Contains cart items. Serialized instance of cart is saved into django
    session.
    '''
    SESSION_KEY = 'cart'
    timestamp = None
    billing_address = None

    def __unicode__(self):
        return ugettext('Your cart (%(cart_count)s)') % {
            'cart_count': self.count()}

    def check_quantity(self, product, quantity, data=None):
        '''
        Raises exception when product has stock and user insert too big
        quantity.
        '''
        if (isinstance(product, StockedProduct) and
            quantity > product.stock):
            raise InsufficientStockException(product)
        return super(Cart, self).check_quantity(product, quantity, data)


def remove_cart_from_request(request):
    '''
    Method removes cart instance from django session.
    '''
    del request.session[Cart.SESSION_KEY]
