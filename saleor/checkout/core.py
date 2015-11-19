from collections import defaultdict

from django.conf import settings
from prices import Price
from satchless.process import ProcessManager

from .steps import ShippingAddressStep, SummaryStep, ShippingMethodStep
from ..cart import Cart
from ..core import analytics
from ..order.models import Order
from ..userprofile.models import Address


STORAGE_SESSION_KEY = 'checkout_storage'


class CheckoutStorage(defaultdict):

    modified = False

    def __init__(self, *args, **kwargs):
        super(CheckoutStorage, self).__init__(dict, *args, **kwargs)


class Checkout(ProcessManager):

    items = None
    groups = None
    billing = None
    steps = None

    def __init__(self, request):
        self.request = request
        self.groups = []
        self.steps = []
        self.items = []
        try:
            self.storage = CheckoutStorage(
                request.session[STORAGE_SESSION_KEY])
        except KeyError:
            self.storage = CheckoutStorage()
        self.cart = Cart.for_session_cart(request.cart,
                                          discounts=request.discounts)
        self.generate_steps(self.cart)

    def __iter__(self):
        return iter(self.steps)

    def generate_steps(self, cart):
        shipping_address = None
        self.cart = cart
        if self.is_shipping_required():
            self.shipping = ShippingAddressStep(
                self.request, self.storage['shipping_address'], checkout=self)
            shipping_address = self.shipping.address
            self.steps.append(self.shipping)
            self.delivery = ShippingMethodStep(
                self.request, self.storage['shipping_method'], shipping_address,
                self.cart, checkout=self)
            self.steps.append(self.delivery)
        else:
            self.shipping = None
            self.delivery = None

        summary_step = SummaryStep(self.request, self.storage['summary'],
                                   shipping_address, checkout=self)
        self.steps.append(summary_step)

    @property
    def anonymous_user_email(self):
        storage = self.get_storage('billing')
        return storage.get('anonymous_user_email')

    @anonymous_user_email.setter
    def anonymous_user_email(self, email):
        storage = self.get_storage('billing')
        storage['anonymous_user_email'] = email

    @anonymous_user_email.deleter
    def anonymous_user_email(self):
        storage = self.get_storage('billing')
        storage['anonymous_user_email'] = ''

    @property
    def billing_address(self):
        storage = self.get_storage('billing')
        address_data = storage.get('address', {})
        return Address(**address_data)

    @billing_address.setter
    def billing_address(self, address):
        storage = self.get_storage('billing')
        storage['address'] = address.as_data()

    @billing_address.deleter
    def billing_address(self):
        storage = self.get_storage('billing')
        storage['address'] = None

    @property
    def shipping_address(self):
        storage = self.get_storage('shipping')
        address_data = storage.get('address', {})
        return Address(**address_data)

    @shipping_address.setter
    def shipping_address(self, address):
        storage = self.get_storage('shipping')
        storage['address'] = address.as_data()

    @shipping_address.deleter
    def shipping_address(self):
        storage = self.get_storage('shipping')
        storage['address'] = None

    def get_storage(self, name):
        return self.storage[name]

    def get_total(self, **kwargs):
        zero = Price(0, currency=settings.DEFAULT_CURRENCY)
        cost_iterator = (total_with_delivery
                         for delivery, delivery_cost, total_with_delivery
                         in self.get_deliveries(**kwargs))
        total = sum(cost_iterator, zero)
        return total

    def save(self):
        self.request.session[STORAGE_SESSION_KEY] = dict(self.storage)

    def clear_storage(self):
        try:
            del self.request.session[STORAGE_SESSION_KEY]
        except KeyError:
            pass

        self.cart.clear()

    def is_shipping_required(self):
        return self.cart.is_shipping_required()

    def get_deliveries(self, **kwargs):
        for partition in self.cart.partition():
            if self.shipping:
                delivery_method = self.delivery.delivery_method
                delivery_cost = delivery_method.get_delivery_total(partition)
            else:
                delivery_cost = Price(0, currency=settings.DEFAULT_CURRENCY)
            total_with_delivery = partition.get_total(**kwargs) + delivery_cost
            yield partition, delivery_cost, total_with_delivery

    def create_order(self):
        order = Order()
        if self.request.user.is_authenticated():
            order.user = self.request.user
        for step in self.steps:
            step.add_to_order(order)
        if self.request.user.is_authenticated():
            order.anonymous_user_email = ''
        order.tracking_client_id = analytics.get_client_id(self.request)
        order.save()
        return order

    def available_steps(self):
        available = []
        for step in self:
            available.append(step)
            if not self.validate_step(step):
                break
        return available