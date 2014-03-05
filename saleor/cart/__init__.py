from __future__ import unicode_literals
import json

from django.utils.translation import pgettext
from django.utils.encoding import python_2_unicode_compatible
from satchless import cart
from satchless.item import ItemList, InsufficientStock
from saleor.product.models import Product


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

    def as_data(self):
        items = []
        for cartline in self:
            if isinstance(cartline.product, dict):
                data = cartline.product
            else:
                data = cartline.product.as_data()
            data['quantity'] = cartline.quantity
            items.append(data)
        cart_data = {
            'items': items,
            'modified': self.modified
        }
        return cart_data

    @classmethod
    def from_data(cls, cart_data):
        cart = Cart()
        for item in cart_data['items']:
            product = Product.objects.get(pk=item['product_id'])
            variant = product.variants.get(pk=item['variant_id'])
            quantity = item['quantity']
            cart.add(variant, quantity=quantity, check_quantity=False)
        return cart
