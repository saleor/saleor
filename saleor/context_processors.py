from django.conf import settings


def googe_analytics(request):
    try:
        return {'GOOGLE_ANALYTICS_CODE': settings.GOOGLE_ANALYTICS_CODE}
    except AttributeError:
        return {}


def canonical_hostname(request):
    try:
        return {'CANONICAL_HOSTNAME': settings.CANONICAL_HOSTNAME}
    except AttributeError:
        return {}
