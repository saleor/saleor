from functools import singledispatch

from django.core.exceptions import ImproperlyConfigured


@singledispatch
def convert_form_field(field):
    raise ImproperlyConfigured(
        "Don't know how to convert the Django form field %s (%s) "
        "to Graphene type" % (field, field.__class__)
    )
