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

    def to_json(self):
        items = []
        for cartline in self:
            items.append({
                'product_id': cartline.product.product.pk,
                'variant_id': cartline.product.pk,
                'quantity': cartline.quantity,
            })
        cart_data = {
            'items': items,
            'modified': self.modified
        }
        return json.dumps(cart_data)

    @classmethod
    def from_json(cls, cart_json):
        cart = Cart()
        cart_data = json.loads(cart_json)
        for item in cart_data['items']:
            product = Product.objects.get(pk=item['product_id'])
            variant = product.variants.get(pk=item['variant_id'])
            quantity = item['quantity']
            cart.add(variant, quantity=quantity, check_quantity=False)
        return cart
