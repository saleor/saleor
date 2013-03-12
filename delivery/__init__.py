from django.conf import settings
from prices import Price
from satchless.item import Item
from userprofile.forms import AddressForm
from satchless.handler import Handler, filter_handlers
from product.models import PhisicalProduct, DigitalShip


class BaseDelivery(Handler, Item):

    def __init__(self, delivery_group, **kwargs):
        self.group = delivery_group

    @classmethod
    def can_handle(cls, delivery_group, **kwargs):
        return True

    def get_price_per_item(self, **kwargs):
        return Price(0, currency=settings.SATCHLESS_DEFAULT_CURRENCY)


class DummyShipping(BaseDelivery):

    def __init__(self, delivery_group, address=None, **kwargs):
        self.address = address
        super(DummyShipping, self).__init__(delivery_group, **kwargs)

    @classmethod
    def can_handle(cls, delivery_group, **kwargs):
        for item in delivery_group:
            if not isinstance(item.product, PhisicalProduct):
                return False
        return True

    def get_price_per_item(self, **kwargs):
        weight = sum(grup.product.weight for grup in self.group)
        qty = sum(grup.quantity for grup in self.group)
        return Price(weight*qty, currency=settings.SATCHLESS_DEFAULT_CURRENCY)


class DigitalDelivery(BaseDelivery):

    @classmethod
    def can_handle(cls, delivery_group, **kwargs):
        for item in delivery_group:
            if not isinstance(item.product, DigitalShip):
                return False
        return True


def get_delivery_methods(delivery, **kwargs):
    return filter_handlers([DummyShipping, DigitalDelivery],delivery, **kwargs)
