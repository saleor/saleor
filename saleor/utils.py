# coding: utf-8

from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http.request import absolute_http_url_re
from django.template.response import TemplateResponse
from django.utils.encoding import iri_to_uri
from satchless.process import InvalidData, Step
from urlparse import urljoin


__all__ = ['BaseStep', 'CategoryChoiceField', 'build_absolute_uri']


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

    def process(self, extra_context=None):
        context = extra_context or {}
        if not self.forms_are_valid() or self.request.method == 'GET':
            context['step'] = self
            return TemplateResponse(self.request, self.template, context)
        self.save()

    def get_absolute_url(self):
        raise NotImplementedError()


def build_absolute_uri(location, is_secure=False):
    try:
        host = settings.CANONICAL_HOSTNAME
    except AttributeError:
        raise ImproperlyConfigured('You need to specify CANONICAL_HOSTNAME in '
                                   'your Django settings file')
    if not absolute_http_url_re.match(location):
        current_uri = '%s://%s' % ('https' if is_secure else 'http', host)
        location = urljoin(current_uri, location)
    return iri_to_uri(location)
