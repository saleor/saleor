from collections import defaultdict

from django.conf import settings
from prices import Price
from satchless.process import ProcessManager

from .steps import ShippingAddressStep, ShippingMethodStep, SummaryStep
from ..cart import Cart
from ..core import analytics
from ..order.models import Order

STORAGE_SESSION_KEY = 'checkout_storage'


class CheckoutStorage(defaultdict):
    modified = False

    def __init__(self, *args, **kwargs):
        super(CheckoutStorage, self).__init__(dict, *args, **kwargs)


class Checkout(ProcessManager):
    steps = None

    def __init__(self, request):
        self.request = request
        self.steps = []
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
        self.cart = cart
        if self.is_shipping_required():
            self.shipping_address_step = ShippingAddressStep(
                self.request, self.storage['shipping_address'], checkout=self)
            shipping_address = self.shipping_address_step.address
            self.steps.append(self.shipping_address_step)
            self.shipping_method_step = ShippingMethodStep(
                self.request, self.storage['shipping_method'], shipping_address,
                self.cart, checkout=self)
            self.steps.append(self.shipping_method_step)
        else:
            shipping_address = None
            self.shipping_address_step = None
            self.shipping_method_step = None

        summary_step = SummaryStep(self.request, self.storage['summary'],
                                   shipping_address, checkout=self)
        self.steps.append(summary_step)

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
            if (self.shipping_address_step and
                    self.shipping_method_step.delivery_method):
                delivery_method = self.shipping_method_step.delivery_method
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
        order.total_net = self.get_total()
        # Tax is not calculated by default
        order.total_tax = Price(0, currency=settings.DEFAULT_CURRENCY)
        order.save()
        return order

    def available_steps(self):
        available = []
        for step in self:
            step.is_step_available = True
            available.append(step)
            if not self.validate_step(step):
                break
            step.is_step_valid = True
        return available
