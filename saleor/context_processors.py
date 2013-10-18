from django.conf import settings


def get_setting_as_dict(name, short_name=None):
    short_name = short_name or name
    try:
        return {short_name: getattr(settings, name)}
    except AttributeError:
        return {}


def googe_analytics(request):
    return get_setting_as_dict('GOOGLE_ANALYTICS_CODE')


def canonical_hostname(request):
    return get_setting_as_dict('CANONICAL_HOSTNAME')


def default_currency(request):
    return get_setting_as_dict('SATCHLESS_DEFAULT_CURRENCY',
                               'DEFAULT_CURRENCY')
