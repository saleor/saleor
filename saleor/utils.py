# coding: utf-8

from django import forms
from django.db import models
from django.template.response import TemplateResponse
from satchless.process import Step
from satchless.process import InvalidData


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        level = getattr(obj, obj._mptt_meta.level_attr)  # pylint: disable=W0212
        indent = max(0, level - 1) * u'│'
        if obj.parent:
            last = ((obj.parent.rght - obj.rght == 1)
                    and (obj.rght - obj.lft == 1))
            if last:
                indent += u'└ '
            else:
                indent += u'├ '
        return u'%s%s' % (indent, unicode(obj))


class BaseStep(Step):

    forms = None
    template = ''

    def __init__(self, request):
        self.request = request
        self.forms = {}

    def __unicode__(self):
        raise NotImplementedError()

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
        raise NotImplementedError()
