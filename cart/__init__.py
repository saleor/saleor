from itertools import groupby

from django.utils.translation import pgettext
from satchless import cart
from satchless.item import ItemSet, Partitioner

from delivery import DummyShipping, DigitalDelivery
from product.models import StockedProduct, DigitalShip


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
        for classifier, items in groupby(self.subject, self.classify):
            delivery_class = self.get_delivery_class(classifier)
            delivery = delivery_class(items)
            yield delivery

    def classify(self, item):
        return item.product.__class__

    def get_delivery_class(self, classifier):
        if issubclass(classifier, DigitalShip):
            return DigitalGroup
        return ShippedGroup

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
        return pgettext(u'Shopping cart', u'Your cart (%(cart_count)s)') % {
            'cart_count': self.count()}

    def check_quantity(self, product, quantity, data=None):
        '''
        Raises exception when product has stock and user insert too big
        quantity.
        '''
        super(Cart, self).check_quantity(product, quantity, data)
        if isinstance(product, StockedProduct) and quantity > product.stock:
            raise InsufficientStockException(product)


def remove_cart_from_request(request):
    '''
    Method removes cart instance from django session.
    '''
    del request.session[Cart.SESSION_KEY]
