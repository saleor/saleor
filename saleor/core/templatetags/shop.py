from django.template import Library
from django.utils.http import urlencode

from ...menu.models import Menu

register = Library()


@register.simple_tag(takes_context=True)
def get_sort_by_url(context, field, descending=False):
    request = context['request']
    request_get = request.GET.dict()
    if descending:
        request_get['sort_by'] = '-' + field
    else:
        request_get['sort_by'] = field
    return '%s?%s' % (request.path, urlencode(request_get))


@register.inclusion_tag('menu.html')
def menu(menus, slug, horizontal=False):
    menu = next((menu for menu in menus if menu.slug == slug), None)
    menu_items = menu.get_direct_items() if menu else None
    return {'menu_items': menu_items, 'horizontal': horizontal}
