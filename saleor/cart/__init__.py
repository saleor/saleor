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
            product = Product.objects.get(pk=item.data['product_id'])
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
        variant_data = {
            'product_id': variant.product.pk,
            'variant_id': variant.pk,
            'unit_price': str(variant.get_price_per_item().gross)
        }
        return variant_data

    def add(self, product, quantity=1, data=None, replace=False,
            check_quantity=True, modify_session_cart=True):
        super(Cart, self).add(product, quantity, data, replace, check_quantity)

        if modify_session_cart:
            data = self.get_data_for_product(product)
            self.session_cart.add(product, quantity, data, replace)

    def clear(self):
        super(Cart, self).clear()
        self.session_cart.clear()


class SessionCartLine(cart.CartLine):
    def get_price_per_item(self, **kwargs):
        return self.data.get('unit_price')

    def as_data(self):
        all_data = {
            'product': self.product,
            'quantity': self.quantity
        }
        all_data.update(self.data)
        return all_data

    @classmethod
    def from_data(self, data_dict):
        product = data_dict.pop('product')
        quantity = data_dict.pop('quantity')
        data = data_dict

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
            cart._state.append(SessionCartLine.from_data(line_data))
        return cart

    def for_storage(self):
        cart_data = {
            'items': [i.as_data() for i in self._state],
            'modified': self.modified
        }
        return cart_data

    def get_line(self, product, data=None):
        return super(SessionCart, self).get_line(smart_text(product), data)

    def create_line(self, product, quantity, data):
        # In this place product attribute is ProductVariant instance
        variant = product
        variant_data = {
            'product_id': variant.product.pk,
            'variant_id': variant.pk,
            'unit_price': str(variant.get_price_per_item().gross)
        }
        if isinstance(data, dict):
            variant_data.update(data)
        return SessionCartLine(smart_text(product), quantity, variant_data)