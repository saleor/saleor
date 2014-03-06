from __future__ import unicode_literals
import json

from django.utils.translation import pgettext
from django.utils.encoding import python_2_unicode_compatible
from satchless import cart
from satchless.item import ItemList, InsufficientStock
from saleor.product.models import Product

CART_SESSION_KEY = 'cart'

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

    def __init__(self, session_cart):
        super(Cart, self).__init__()
        self.session_cart = SessionCart.from_data(session_cart)

    @classmethod
    def from_cart(cls, session_cart):
        cart = Cart(session_cart)
        for item in session_cart['items']:
            product = Product.objects.get(pk=item['product_id'])
            variant = product.variants.get(pk=item['variant_id'])
            quantity = item['quantity']
            cart.add(variant, quantity=quantity, check_quantity=False,
                     modify_session_cart=False)
        return cart

    def __str__(self):
        return pgettext(
            'Shopping cart',
            'Your cart (%(cart_count)s)') % {'cart_count': self.count()}

    def add(self, product, quantity=1, data=None, replace=False,
            check_quantity=True, modify_session_cart=True):
        super(Cart, self).add(product, quantity, data, replace, check_quantity)

        if modify_session_cart:
            self.session_cart.add(product, quantity, data, replace)

    def clear(self):
        super(Cart, self).clear()
        self.session_cart.clear()


@python_2_unicode_compatible
class SessionCart(cart.Cart):
    '''
    Serializable representation of cart.
    Parameters:
    variant - Instance of ProductVariant
    '''

    def __str__(self):
        return 'SessionCart'

    @classmethod
    def from_data(cls, cart_data):
        cart = SessionCart()
        cart.modified = cart_data['modified']
        cart._state = cart_data['items']
        return cart

    def add(self, variant, quantity=1, data=None, replace=False):
        product_data = {
            'product_id': variant.product.pk,
            'variant_id': variant.pk,
            'product_name': str(variant),
            'quantity': quantity,
            'unit_price': str(variant.get_price_per_item().gross)}

        if replace:
            # Replace quantity
            for item in self._state:
                if item['product_id'] == product_data['product_id'] \
                and item['variant_id'] == product_data['variant_id']:
                    self._state.remove(item)

        self._state.append(product_data)
        self.modified = True

    def get_line(self, variant, data=None):
        for item in self._state:
            if item['product_id'] == variant.product.pk \
                and item['variant_id'] == variant.pk:
                return item

    def count(self):
        return sum([item['quantity'] for item in self._state])

    def as_data(self):
        cart_data = {
            'items': self._state,
            'modified': self.modified
        }
        return cart_data