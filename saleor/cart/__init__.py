from __future__ import unicode_literals

from django.utils.translation import pgettext
from satchless import cart
from satchless.item import ItemSet, ClassifyingPartitioner

from ..delivery import DummyShipping, DigitalDelivery
from ..product.models import DigitalShip


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

    def _get_cheapest_delivery_method(self, **kwargs):
        if self.delivery_method:
            return (self.delivery_method,
                    self.delivery_method.get_price_per_item(**kwargs))
        methods = self.get_delivery_methods()
        prices = ((method.get_price_per_item(**kwargs), method)
                  for method in methods)
        cheapest_price, cheapest_method = min(prices)
        return cheapest_method, cheapest_price

    def get_delivery_total(self, **kwargs):
        '''
        Method returns price from the self.delivery_method or lowest price
        from delivery methods.
        '''
        method, price = self._get_cheapest_delivery_method(**kwargs)
        return price

    def get_delivery_method(self, **kwargs):
        '''
        Method returns price from the self.delivery_method or lowest price
        from delivery methods.
        '''
        method, price = self._get_cheapest_delivery_method(**kwargs)
        return method

    def get_total_with_delivery(self, **kwargs):
        return self.get_total() + self.get_delivery_total()


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


class CartPartitioner(ClassifyingPartitioner):
    '''
    Dividing cart into groups.
    '''
    def __iter__(self):
        items_attr = 'partitioner_groups'
        if not hasattr(self, items_attr):
            groups = super(CartPartitioner, self).__iter__()
            setattr(self, items_attr, list(groups))
        for group in getattr(self, items_attr):
            yield group

    def classify(self, item):
        if isinstance(item.product, DigitalShip):
            return 'digital'
        return 'shippable'

    def get_partition(self, classifier, items):
        if classifier == 'digital':
            return DigitalGroup(items)
        return ShippedGroup(items)

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


class Cart(cart.Cart):
    '''
    Contains cart items. Serialized instance of cart is saved into django
    session.
    '''
    timestamp = None
    billing_address = None

    def __unicode__(self):
        return pgettext('Shopping cart', 'Your cart (%(cart_count)s)') % {
            'cart_count': self.count()}

    def clear(self):
        self._state = []
