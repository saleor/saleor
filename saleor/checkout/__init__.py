from collections import defaultdict

from satchless.process import ProcessManager

from .steps import (BillingAddressStep, ShippingStep, DigitalDeliveryStep,
                    SummaryStep)
from ..cart import CartPartitioner, DigitalGroup
from ..order.models import Order

STORAGE_SESSION_KEY = 'checkout_storage'


class CheckoutStorage(dict):

    modified = False

    def __init__(self, *args, **kwargs):
        super(CheckoutStorage, self).__init__(*args, **kwargs)
        self.update({'anonymous_user_email': '', 'billing_address': None,
                     'groups': defaultdict(dict), 'summary': False})


class Checkout(ProcessManager):

    storage = None
    steps = None
    groups = None

    def __init__(self, request):
        self.groups = CartPartitioner(request.cart)
        self.request = request
        try:
            self.storage = request.session[STORAGE_SESSION_KEY]
        except KeyError:
            self.storage = CheckoutStorage()
        self.generate_steps()

    def generate_steps(self):
        self.steps = [BillingAddressStep(self, self.request)]
        for index, delivery_group in enumerate(self.groups):
            step_class = ShippingStep
            if isinstance(delivery_group, DigitalGroup):
                step_class = DigitalDeliveryStep
            step = step_class(self, self.request,
                              delivery_group, index)
            step_group = self.get_group(str(step))
            if 'delivery_method' in step_group:
                delivery_group.delivery_method = step_group['delivery_method']
            self.steps.append(step)
        self.steps.append(SummaryStep(self, self.request))

    @property
    def anonymous_user_email(self):
        return self.storage['anonymous_user_email']

    @anonymous_user_email.setter
    def anonymous_user_email(self, email):
        self.storage['anonymous_user_email'] = email

    @anonymous_user_email.deleter
    def anonymous_user_email(self, email):
        self.storage['anonymous_user_email'] = ''

    @property
    def billing_address(self):
        return self.storage['billing_address']

    @billing_address.setter
    def billing_address(self, address):
        self.storage['billing_address'] = address

    @billing_address.deleter
    def billing_address(self, address):
        self.storage['billing_address'] = None

    def get_group(self, name):
        return self.storage['groups'][name]

    def set_group(self, name, group):
        self['groups'][name] = group

    def save(self):
        self.request.session[STORAGE_SESSION_KEY] = self.storage

    def clear_storage(self):
        del self.request.session[STORAGE_SESSION_KEY]
        self.request.cart.clear()

    def __iter__(self):
        return iter(self.steps)

    def create_order(self):
        order = Order()
        for step in self.steps:
            step.add_to_order(order)
        if self.request.user.is_authenticated():
            order.user = self.request.user
            order.anonymous_user_email = ''
        order.save()
        return order
