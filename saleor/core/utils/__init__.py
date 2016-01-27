# coding: utf-8
from __future__ import unicode_literals
import re

from django import forms
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.encoding import iri_to_uri, smart_text
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


__all__ = ['CategoryChoiceField', 'build_absolute_uri']

absolute_http_url_re = re.compile(r'^https?://', re.I)


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # pylint: disable=W0212
        level = getattr(obj, obj._mptt_meta.level_attr)
        indent = max(0, level - 1) * '│'
        if obj.parent:
            last = ((obj.parent.rght - obj.rght == 1) and
                    (obj.rght - obj.lft == 1))
            if last:
                indent += '└ '
            else:
                indent += '├ '
        return '%s%s' % (indent, smart_text(obj))


def build_absolute_uri(location, is_secure=False):
    from django.contrib.sites.models import Site
    site = Site.objects.get_current()
    host = site.domain
    if not absolute_http_url_re.match(location):
        current_uri = '%s://%s' % ('https' if is_secure else 'http', host)
        location = urljoin(current_uri, location)
    return iri_to_uri(location)


def get_paginator_items(items, paginate_by, page):
    paginator = Paginator(items, paginate_by)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)
    return items
