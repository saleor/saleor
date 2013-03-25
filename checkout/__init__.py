from .steps import BillingAddressStep, ShippingStep, DigitalDeliveryStep, \
    SummaryStep, SuccessStep
from cart import CartPartitioner, DigitalGroup
from collections import defaultdict
from delivery import DummyShipping, DigitalDelivery
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from satchless import process
from satchless.item import ItemSet
from satchless.process import InvalidData, ProcessManager
from userprofile.models import Address

STORAGE_SESSION_KEY = 'checkout_storage'


class CheckoutStorage(dict):

    modified = False

    def __init__(self, *args, **kwargs):
        super(CheckoutStorage, self).__init__(*args, **kwargs)
        self.update({
            'billing_address': None,
            'groups': defaultdict(dict)})


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
                              delivery_group.get_delivery_methods(), index)
            step_group = self.get_group(str(step))
            if 'delivery_method' in step_group:
                delivery_group.delivery_method = step_group['delivery_method']
            self.steps.append(step)
        self.steps.append(SummaryStep(self, self.request))
        self.steps.append(SuccessStep(self, self.request))

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

    def __iter__(self):
        return iter(self.steps)


