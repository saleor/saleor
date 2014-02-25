from __future__ import unicode_literals

from django.conf import settings
from prices import Price
from satchless.item import ItemSet


class BaseDelivery(ItemSet):

    group = None

    def __init__(self, delivery_group):
        self.group = delivery_group

    def __iter__(self):
        return iter(self.group)

    def get_delivery_total(self, **kwargs):
        return Price(0, currency=settings.DEFAULT_CURRENCY)

    def get_total_with_delivery(self):
        return self.group.get_total() + self.get_delivery_total()


class DummyShipping(BaseDelivery):

    def __init__(self, delivery_group, address):
        self.address = address
        super(DummyShipping, self).__init__(delivery_group)

    def __unicode__(self):
        return 'Dummy shipping'

    def get_delivery_total(self, **kwargs):
        weight = sum(line.product.product.weight for line in self.group)
        qty = sum(line.quantity for line in self.group)
        return Price(qty * weight,
                     currency=settings.DEFAULT_CURRENCY)


class DigitalDelivery(BaseDelivery):

    def __init__(self, delivery_group, email):
        self.email = email
        super(DigitalDelivery, self).__init__(delivery_group)

    def __unicode__(self):
        return 'Digital delivery'


def get_delivery_choices_for_group(group, **kwargs):
    if 'address' in kwargs:
        yield ('dummy_shipping', DummyShipping(group, kwargs['address']))
    elif 'email' in kwargs:
        yield ('digital_delivery', DigitalDelivery(group, kwargs['email']))
    else:
        raise ValueError('Unknown delivery type')
