from django.db.models.manager import Manager
from django.utils.encoding import force_str
from graphene.utils.str_converters import to_camel_case

try:
    import django_filters  # noqa

    DJANGO_FILTER_INSTALLED = True
except ImportError:
    DJANGO_FILTER_INSTALLED = False


def isiterable(value):
    try:
        iter(value)
    except TypeError:
        return False
    return True


def _camelize_django_str(s):
    if isinstance(s, Promise):
        s = force_str(s)
    return to_camel_case(s) if isinstance(s, str) else s


def camelize(data):
    if isinstance(data, dict):
        return {_camelize_django_str(k): camelize(v) for k, v in data.items()}
    if isiterable(data) and not isinstance(data, (str, Promise)):
        return [camelize(d) for d in data]
    return data


def maybe_queryset(value):
    if isinstance(value, Manager):
        value = value.get_queryset()
    return value
