from collections import defaultdict

from satchless.process import ProcessManager

from .steps import (BillingAddressStep, ShippingStep, DigitalDeliveryStep,
                    SummaryStep)
from ..cart import CartPartitioner, DigitalGroup
from ..core import analytics
from ..order.models import Order

STORAGE_SESSION_KEY = 'checkout_storage'


class CheckoutStorage(defaultdict):

    modified = False

    def __init__(self, *args, **kwargs):
        super(CheckoutStorage, self).__init__(dict, * args, **kwargs)
        if not 'billing' in self:
            self['billing'] = {'address': None, 'anonymous_user_email': None}


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
        self.generate_steps(request.cart)

    def generate_steps(self, cart):
        self.items = CartPartitioner(cart)
        self.billing = BillingAddressStep(
            self, self.request, self.storage['billing'])
        self.steps.append(self.billing)
        for index, delivery_group in enumerate(self.items):
            if isinstance(delivery_group, DigitalGroup):
                step_class = DigitalDeliveryStep
            else:
                step_class = ShippingStep
            storage_key = 'shipping_%s' % (index,)
            step = step_class(self, self.request, self.storage[storage_key],
                              delivery_group, index)
            self.steps.append(step)
        summary_step = SummaryStep(self, self.request, self.storage['summary'])
        self.steps.append(summary_step)

    @property
    def anonymous_user_email(self):
        return self.storage['billing']['anonymous_user_email']

    @anonymous_user_email.setter
    def anonymous_user_email(self, email):
        self.storage['billing']['anonymous_user_email'] = email

    @anonymous_user_email.deleter
    def anonymous_user_email(self, email):
        self.storage['billing']['anonymous_user_email'] = ''

    @property
    def billing_address(self):
        return self.storage['billing']['address']

    @billing_address.setter
    def billing_address(self, address):
        self.storage['billing']['address'] = address

    @billing_address.deleter
    def billing_address(self, address):
        self.storage['billing']['address'] = None

    def get_step_data(self, name):
        return self.storage[name]

    def set_step_data(self, name, group):
        self[name] = group

    def get_total(self, **kwargs):
        return self.items.get_total(**kwargs)

    def save(self):
        self.request.session[STORAGE_SESSION_KEY] = dict(self.storage)

    def clear_storage(self):
        del self.request.session[STORAGE_SESSION_KEY]
        self.request.cart.clear()

    def __iter__(self):
        return iter(self.steps)

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
