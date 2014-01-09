from __future__ import unicode_literals

from django.utils.translation import pgettext
from satchless import cart
from satchless.item import ItemSet, ClassifyingPartitioner

from ..product.models import DigitalShip


class ShippedGroup(list, ItemSet):
    '''
    Group for shippable products.
    '''
    pass


class DigitalGroup(list, ItemSet):
    '''
    Group for digital products.
    '''
    pass


class CartPartitioner(ClassifyingPartitioner):
    '''
    Dividing cart into groups.
    '''
    def classify(self, item):
        if isinstance(item.product, DigitalShip):
            return 'digital'
        return 'shippable'

    def get_partition(self, classifier, items):
        if classifier == 'digital':
            return DigitalGroup(items)
        return ShippedGroup(items)


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
