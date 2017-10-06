from __future__ import unicode_literals
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from django.template import Library
from django.utils.http import urlencode

from ...product.filters import DEFAULT_SORT

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


@register.inclusion_tag('category/_sort_by.html', takes_context=True)
def sort_by(context, attributes):
    ctx = {
        'request': context['request'],
        'sort_by': (context['request'].GET.get('sort_by', DEFAULT_SORT)
                    .strip('-')),
        'sort_by_choices': attributes,
        'arrow_down': (context['request'].GET.get('sort_by', DEFAULT_SORT)
                       .startswith('-'))}
    return ctx
