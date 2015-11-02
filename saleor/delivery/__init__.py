from __future__ import unicode_literals

from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from prices import Price
from satchless.item import ItemSet


class BaseDelivery(ItemSet):
    group = None
    name = ''

    def __iter__(self):
        return iter(self.group)

    def get_delivery_total(self, **kwargs):
        return Price(0, currency=settings.DEFAULT_CURRENCY)

    def get_total_with_delivery(self):
        return self.group.get_total() + self.get_delivery_total()


@python_2_unicode_compatible
class FirstDummyShipping(BaseDelivery):
    name = 'first_dummy_shipping'

    def __str__(self):
        return 'First dummy shipping'

    def get_delivery_total(self, items, **kwargs):
        return Price(10, currency=settings.DEFAULT_CURRENCY)

@python_2_unicode_compatible
class SecondDummyShipping(BaseDelivery):
    name = 'second_dummy_shipping'

    def __str__(self):
        return 'Second dummy shipping'

    def get_delivery_total(self, items, **kwargs):
        return Price(25, currency=settings.DEFAULT_CURRENCY)


def get_delivery_options_for_items(items, **kwargs):
    if 'address' in kwargs:
        yield FirstDummyShipping()
        yield SecondDummyShipping()
    else:
        raise ValueError('Unknown delivery type')


def get_delivery(name):
    delivery_methods = [FirstDummyShipping, SecondDummyShipping]
    for delivery_method in delivery_methods:
        if name == delivery_method.name:
            return delivery_method()
    else:
        raise ValueError('Unknown delivery method: %s' % (name,))
