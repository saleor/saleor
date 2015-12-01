# coding: utf-8
from __future__ import unicode_literals
import re

from django import forms
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.template.response import TemplateResponse
from django.utils.encoding import iri_to_uri, smart_text
from satchless.process import InvalidData, Step
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


__all__ = ['BaseStep', 'CategoryChoiceField', 'build_absolute_uri']

absolute_http_url_re = re.compile(r"^https?://", re.I)


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # pylint: disable=W0212
        level = getattr(obj, obj._mptt_meta.level_attr)
        indent = max(0, level - 1) * '│'
        if obj.parent:
            last = ((obj.parent.rght - obj.rght == 1)
                    and (obj.rght - obj.lft == 1))
            if last:
                indent += '└ '
            else:
                indent += '├ '
        return '%s%s' % (indent, smart_text(obj))


class BaseStep(Step):

    forms = None
    template = ''
    group = None

    def __init__(self, request):
        self.request = request
        self.forms = {}

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
    from django.contrib.sites.models import Site
    site = Site.objects.get_current()
    host = site.domain
    if not absolute_http_url_re.match(location):
        current_uri = '%s://%s' % ('https' if is_secure else 'http', host)
        location = urljoin(current_uri, location)
    return iri_to_uri(location)


def get_paginator_items(items, page):
    paginator = Paginator(items, settings.PAGINATE_BY)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)
    return items
