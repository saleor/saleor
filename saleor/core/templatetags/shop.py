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


def get_menu_items(slug):
    menu = Menu.objects.filter(slug=slug).prefetch_related('items').first()
    return menu.get_direct_items() if menu else None


@register.inclusion_tag('navbar_menu.html')
def navbar_menu():
    return {'menu_items': get_menu_items('navbar')}


@register.inclusion_tag('footer_menu.html')
def footer_menu():
    return {'menu_items': get_menu_items('footer')}
