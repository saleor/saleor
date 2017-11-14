from __future__ import unicode_literals
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from django.template import Library
from django.utils.http import urlencode


register = Library()


@register.filter
def slice(items, group_size=1):
    args = [iter(items)] * group_size
    return (filter(None, group)
            for group in zip_longest(*args, fillvalue=None))


@register.simple_tag(takes_context=True)
def get_sort_by_url(context, field, descending=False):
    request = context['request']
    request_get = request.GET.dict()
    if descending:
        request_get['sort_by'] = '-' + field
    else:
        request_get['sort_by'] = field
    return '%s?%s' % (request.path, urlencode(request_get))


@register.simple_tag(takes_context=True)
def get_sort_by_url_toggle(context, field):
    request = context['request']
    request_get = request.GET.dict()
    if field == request_get.get('sort_by'):
        new_sort_by = '-%s' % field  # descending sort
    else:
        new_sort_by = field  # ascending sort
    request_get['sort_by'] = new_sort_by
    return '%s?%s' % (request.path, urlencode(request_get))
