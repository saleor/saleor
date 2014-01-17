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
            self.request, self.get_storage('billing'))
        self.steps.append(self.billing)
        for index, delivery_group in enumerate(self.items):
            if isinstance(delivery_group, DigitalGroup):
                storage = self.get_storage('digital_%s' % (index,))
                step = DigitalDeliveryStep(
                    self.request, storage, delivery_group, _id=index)
            else:
                storage = self.get_storage('shipping_%s' % (index,))
                step = ShippingStep(
                    self.request, storage, delivery_group, _id=index,
                    default_address=self.billing_address)
            self.steps.append(step)
        summary_step = SummaryStep(
            self.request, self.get_storage('summary'), checkout=self)
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
    def anonymous_user_email(self, email):
        storage = self.get_storage('billing')
        storage['anonymous_user_email'] = ''

    @property
    def billing_address(self):
        storage = self.get_storage('billing')
        return storage.get('address')

    @billing_address.setter
    def billing_address(self, address):
        storage = self.get_storage('billing')
        storage['address'] = address

    @billing_address.deleter
    def billing_address(self, address):
        storage = self.get_storage('billing')
        storage['address'] = None

    def get_storage(self, name):
        return self.storage[name]

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
