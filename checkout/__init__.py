from delivery import DummyShipping, DigitalDelivery
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from satchless import process
from satchless.item import ItemSet
from satchless.process import InvalidData
from userprofile.models import Address


class Checkout(object):

    data = {'billing_address':None}


class Step(process.Step):

    forms = None
    template = ''

    def __init__(self, cart, request):
        self.forms = {}
        self.cart = cart
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

    def process(self):
        if self.request.method == 'GET' or not self.forms_are_valid():
            return TemplateResponse(self.request, self.template, {
                'step': self
            })
        self.save()

    @models.permalink
    def get_absolute_url(self):
        return ('checkout:details', (), {'step': str(self)})


