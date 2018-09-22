from django.template import Library

from saleor import settings

register = Library()


@register.simple_tag
def get_object_properties(object, properties):
    """Returns first non empty property of given object."""
    properties = properties.split(',')
    for property in properties:
        attribute = getattr(object, property, '')
        if attribute:
            return getattr(object.translated, property)
    return ''


@register.simple_tag
def settings_value(name):
    """Return any value from settings.py
    :param name: name value
    :return: value
    """
    return getattr(settings, name, "")
