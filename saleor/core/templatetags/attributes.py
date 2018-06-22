from django.template import Library

register = Library()


@register.simple_tag
def get_object_properties(object, properties):
    """Returns first non empty property of given object."""
    properties = properties.split(',')
    for property in properties:
        attribute = getattr(object, property, '')
        if attribute:
            return attribute
    return ''
