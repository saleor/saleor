from django.db import models
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


def get_model_fields(model):
    local_fields = [
        (field.name, field)
        for field in sorted(
            list(model._meta.fields) + list(model._meta.local_many_to_many)
        )
    ]

    # Make sure we don't duplicate local fields with "reverse" version
    local_field_names = [field[0] for field in local_fields]
    reverse_fields = get_reverse_fields(model, local_field_names)

    all_fields = local_fields + list(reverse_fields)

    return all_fields


def get_reverse_fields(model, local_field_names):
    for name, attr in model.__dict__.items():
        # Don't duplicate any local fields
        if name in local_field_names:
            continue

        # "rel" for FK and M2M relations and "related" for O2O Relations
        related = getattr(attr, "rel", None) or getattr(attr, "related", None)
        if isinstance(related, models.ManyToOneRel):
            yield (name, related)
        elif isinstance(related, models.ManyToManyRel) and not related.symmetrical:
            yield (name, related)


def is_valid_django_model(model):
    return inspect.isclass(model) and issubclass(model, models.Model)
