from __future__ import unicode_literals

from django.utils.translation import pgettext
from django.utils.encoding import python_2_unicode_compatible
from satchless import cart
from satchless.item import ItemList


class DigitalGroup(ItemList):
    '''
    Group for digital products.
    '''
    pass


@python_2_unicode_compatible
class Cart(cart.Cart):
    '''
    Contains cart items. Serialized instance of cart is saved into django
    session.
    '''
    timestamp = None
    billing_address = None

    def __str__(self):
        return pgettext(
            'Shopping cart',
            'Your cart (%(cart_count)s)') % {'cart_count': self.count()}