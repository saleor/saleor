from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from satchless import process
from satchless.process import InvalidData


class Step(process.Step):

    forms = None
    template = ''

    def __init__(self, order, request):
        self.forms = {}
        self.order = order
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
        if self.order.status != 'completed':
            if self.request.method == 'GET' or not self.forms_are_valid():
                return TemplateResponse(self.request, self.template, {
                    'forms': self.forms,
                    'order': self.order,
                    'step': self
                })
            self.save()

    @models.permalink
    def get_absolute_url(self):
        return ('order:details', (),
                {'token': self.order.token, 'step': str(self)})
