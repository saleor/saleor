from django.conf import settings
from prices import Price
from satchless.item import Item


class BaseDelivery(Item):

    def __init__(self, delivery_group):
        self.group = delivery_group

    def get_price_per_item(self, **kwargs):
        return Price(0, currency=settings.SATCHLESS_DEFAULT_CURRENCY)


class DummyShipping(BaseDelivery):

    def __unicode__(self):
        return u'Dummy shipping'

    def get_price_per_item(self, **kwargs):
        weight = sum(line.product.weight for line in self.group)
        qty = sum(line.quantity for line in self.group)
        return Price(qty*weight, currency=settings.SATCHLESS_DEFAULT_CURRENCY)


class DigitalDelivery(BaseDelivery):

    pass
