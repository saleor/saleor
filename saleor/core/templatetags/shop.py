from __future__ import unicode_literals
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from django.contrib.staticfiles.templatetags.staticfiles import static
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


@register.assignment_tag(takes_context=True)
def get_sort_by_toggle(context, field):
    request = context['request']
    request_get = request.GET.copy()
    sort_by = request_get.get('sort_by')
    arrow_src = ''
    active = ''
    if sort_by:
        # toggle existing sort_by
        new_sort_by, arrow_src, active = toggle(field, sort_by)
    else:
        # first click on link
        new_sort_by = u'-%s' % field  # descending sort
    request_get['sort_by'] = new_sort_by

    return {
        'url': '%s?%s' % (request.path, request_get.urlencode()),
        'is_active': active,
        'arrow_src': arrow_src}


def toggle(field, sort_by):
    if field == sort_by:
        active, arrow_src, new_sort_by = set_ascending(field)
    else:
        active, arrow_src, new_sort_by = set_descending(field, sort_by)
    return new_sort_by, arrow_src, active


def set_ascending(field):
    new_sort_by = u'-%s' % field  # descending sort
    arrow_src = static('/images/arrow_up_icon.svg')
    active = 'active'
    return active, arrow_src, new_sort_by


def set_descending(field, sort_by):
    new_sort_by = field  # ascending sort
    if field == sort_by[1:]:
        arrow_src = static('/images/arrow_down_icon.svg')
        active = 'active'
    else:
        arrow_src = ''
        active = ''
    return active, arrow_src, new_sort_by
