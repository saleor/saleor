from . import ItemDiscount, DiscountManager, ItemSetDiscount
from cart import Cart
from decimal import Decimal
from django.test import TestCase
from mock import MagicMock, patch
from prices import Price, inspect_price
from product.models import Product
import operator


class ProductDiscount(ItemDiscount):

    value = Decimal(5)
    name = 'Product discount'

    def apply(self, price):
        return Price(price.gross - self.value,
                     currency=price.currency,
                     previous=price,
                     modifier=self,
                     operation=operator.__sub__)

    def __repr__(self):
        return 'ProductDiscount(%r, name=%r)' % (str(self.value), self.name)


class CartDiscount(ItemSetDiscount):

    precent = Decimal(0.5)
    name = 'Cart discount'

    def apply(self, price):
        return Price(price.gross - (price.gross * self.precent),
                     currency=price.currency,
                     previous=price,
                     modifier=self,
                     operation=operator.__sub__)

    def __repr__(self):
        return 'CartDiscount(%r%%, name=%r)' % (int(self.precent * 100),
                                                self.name)


class TestDiscountManager(TestCase):

    def setUp(self):
        self.product = Product(name='test', price=Price(10, currency='USD'),
                               sku='1', category_id=1)
        self.cart = Cart()
        self.cart.add(self.product, 2)

    def test_discount_manager_with_one_item_discaunt(self):
        discount = ProductDiscount()
        discounts = DiscountManager([discount])
        discounts.apply(self.product)
        self.assertEqual(self.product.price, Price(5, currency='USD'))

    def test_discount_manager_with_many_item_discaunts(self):
        discount = ProductDiscount()
        discounts = DiscountManager([discount])
        discounts.append(discount)
        discounts.apply(self.product)
        self.assertEqual(self.product.price, Price(0, currency='USD'))

    def test_discount_manager_with_one_item_set_discaunt(self):
        discount = CartDiscount()
        discounts = DiscountManager([discount])
        discounts.apply(self.cart)
        self.assertEqual(self.cart[0].product.price, Price(5, currency='USD'))

    def test_discount_manager_with_different_discaunts(self):
        discount_cart = CartDiscount()
        discount_product = ProductDiscount()
        discounts = DiscountManager([discount_cart, discount_product])
        discounts.apply(self.cart)
        self.assertEqual(self.cart[0].product.price, Price(5, currency='USD'))
