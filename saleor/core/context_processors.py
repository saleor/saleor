from django.conf import settings

from ..menu.models import Menu


def get_setting_as_dict(name, short_name=None):
    short_name = short_name or name
    try:
        return {short_name: getattr(settings, name)}
    except AttributeError:
        return {}


# request is a required parameter
# pylint: disable=W0613
def default_currency(request):
    return get_setting_as_dict('DEFAULT_CURRENCY')


# request is a required parameter
# pylint: disable=W0613
def navigation(request):
    slugs = ['navbar', 'footer']
    kwargs = ['items', 'items__collection', 'items__category', 'items__page']
    menus = Menu.objects.prefetch_related(*kwargs).filter(slug__in=slugs)
    return {'menus': list(menus)}


def search_enabled(request):
    return {'SEARCH_IS_ENABLED': settings.ENABLE_SEARCH}
