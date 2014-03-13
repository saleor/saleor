from __future__ import unicode_literals

from django.utils.translation import pgettext
from django.utils.encoding import python_2_unicode_compatible, smart_text
from satchless import cart
from satchless.item import ItemList
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
        self.session_cart = session_cart

    @classmethod
    def for_session_cart(cls, session_cart):
        cart = Cart(session_cart)
        for item in session_cart:
            product = Product.objects.select_related().get(
                pk=item.data['product_id'])
            variant = product.variants.get(pk=item.data['variant_id'])
            quantity = item.quantity
            cart.add(variant, quantity=quantity, check_quantity=False,
                     modify_session_cart=False)
        return cart

    def __str__(self):
        return pgettext(
            'Shopping cart',
            'Your cart (%(cart_count)s)') % {'cart_count': self.count()}

    def get_data_for_product(self, variant):
        variant_price = variant.get_price_per_item()
        variant_data = {
            'product_id': variant.product.pk,
            'variant_id': variant.pk,
            'unit_price_gross': str(variant_price.gross),
            'unit_price_net': str(variant_price.net),
        }
        return variant_data

    def add(self, product, quantity=1, data=None, replace=False,
            check_quantity=True, modify_session_cart=True):
        super(Cart, self).add(product, quantity, data, replace, check_quantity)

        if modify_session_cart:
            data = self.get_data_for_product(product)
            self.session_cart.add(smart_text(product), quantity, data, replace)

    def clear(self):
        super(Cart, self).clear()
        self.session_cart.clear()


class SessionCartLine(cart.CartLine):
    def get_price_per_item(self, **kwargs):
        return self.data.get('unit_price')

    def for_storage(self):
        return {
            'product': self.product,
            'quantity': self.quantity,
            'data': self.data
        }

    @classmethod
    def from_storage(cls, data_dict):
        product = data_dict.pop('product')
        quantity = data_dict.pop('quantity')
        data = data_dict['data']
        instance = SessionCartLine(product, quantity, data)
        return instance


@python_2_unicode_compatible
class SessionCart(cart.Cart):

    def __str__(self):
        return 'SessionCart'

    @classmethod
    def from_storage(cls, cart_data):
        cart = SessionCart()
        for line_data in cart_data['items']:
            cart._state.append(SessionCartLine.from_storage(line_data))
        return cart

    def for_storage(self):
        cart_data = {
            'items': [i.for_storage() for i in self._state],
            'modified': False
        }
        return cart_data

    def get_line(self, product, data=None):
        return super(SessionCart, self).get_line(product, data)

    def create_line(self, product, quantity, data):
        return SessionCartLine(product, quantity, data)