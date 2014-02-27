from __future__ import unicode_literals

from django.utils.translation import pgettext
from satchless import cart
from satchless.item import ItemList, partition


class DigitalGroup(ItemList):
    '''
    Group for digital products.
    '''
    pass


class Cart(cart.Cart):
    '''
    Contains cart items. Serialized instance of cart is saved into django
    session.
    '''
    timestamp = None
    billing_address = None

    def __unicode__(self):
        return pgettext(
            'Shopping cart',
            'Your cart (%(cart_count)s)') % {'cart_count': self.count()}


def partitioner(subject):
    return partition(subject, lambda product: 'shippable')