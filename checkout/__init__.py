from delivery import DummyShipping, DigitalDelivery
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from satchless import process
from satchless.item import ItemSet
from satchless.process import InvalidData
from userprofile.models import Address

SESSION_KEY = 'checkout'


class Checkout(object):

    _state = None
    modified = False

    def __init__(self):
        self._state = {
            'billing_address': None,
            'groups': {}}

    @property
    def billing_address(self):
        return self._state['billing_address']

    @billing_address.setter
    def billing_address(self, address):
        self._state['billing_address'] = address

    @billing_address.deleter
    def billing_address(self, address):
        self._state['billing_address'] = None

    def get_group(self, name):
        return self._state['groups'].setdefault(name, {})

    def set_group(self, name, group):
        self._state['groups'][name] = group

    def save(self):
        self.modified = True


class Step(process.Step):

    forms = None
    template = ''

    def __init__(self, checkout, request):
        self.forms = {}
        self.checkout = checkout
        self.request = request

    def __unicode__(self):
        return u'Step'

    def __nonzero__(self):
        try:
            self.validate()
        except InvalidData:
            return False
        return True

    def save(self):
        raise NotImplementedError()

    def forms_are_valid(self):
        for form in self.forms.values():
            if not form.is_valid():
                return False
        return True

    def validate(self):
        if not self.forms_are_valid():
            raise InvalidData()

    def process(self):
        if not self.forms_are_valid() or self.request.method == 'GET':
            return TemplateResponse(self.request, self.template, {
                'step': self
            })
        self.save()

    @models.permalink
    def get_absolute_url(self):
        return ('checkout:details', (), {'step': str(self)})

    def add_to_order(self, order):
        raise NotImplementedError()


def get_checkout_from_request(request, save=True):
    try:
        return request.session[SESSION_KEY]
    except KeyError:
        checkout = Checkout()
        if save:
            request.session[SESSION_KEY] = checkout
        return checkout


