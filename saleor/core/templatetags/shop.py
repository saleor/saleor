from django.template import Library
from django.utils.http import urlencode

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
def menu(site_menu=None, horizontal=False):
    menu_items = site_menu.json_content if site_menu else []
    return {
        'menu_items': menu_items,
        'horizontal': horizontal}


@register.inclusion_tag('footer_menu.html')
def footer_menu(site_menu=None):
    menu_items = site_menu.json_content if site_menu else []
    return {'menu_items': menu_items}


@register.simple_tag
def get_menu_item_name(menu_item, lang_code):
    translated = menu_item['translations'].get(lang_code)
    if translated:
        return translated['name']
    return menu_item['name']
