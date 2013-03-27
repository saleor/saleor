from cart import Cart, InsufficientStockException, BaseGroup
from delivery import BaseDelivery
from django.test import TestCase
from prices import Price
from product.models import Ship
from satchless.cart import CartLine

__all__ = ['CartTest', 'ShippedGroupTest']


product = Ship.objects.create(stock=10, price=Price(10, currency='USD'),
                              category_id=1, weight=123)


class CartTest(TestCase):

    def test_check_quantity(self):
        'Stock limit works'
        cart = Cart()

        def illegal():
            cart.add(product, 100)

        self.assertRaises(InsufficientStockException, illegal)
        self.assertFalse(cart)


class Shipping(BaseDelivery):

    def __unicode__(self):
        return u'Dummy shipping'

    def get_price_per_item(self, **kwargs):
        weight = sum(line.product.weight for line in self.group)
        qty = sum(line.quantity for line in self.group)
        return Price(qty*weight, currency='USD')


class Group(BaseGroup):

    def get_delivery_methods(self):
        yield Shipping(self)


class GroupTest(TestCase):

    def test_get_delivery_total(self):
        'Shipped group works'
        group = Group([])
        self.assertEqual(group.get_delivery_total(),
                         Price(0,currency='USD'), 0)
        group.append(CartLine(product, 2))
        self.assertEqual(group.get_delivery_total(),
                           Price(246, currency='USD'), 246)
