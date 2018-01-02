from django import template

register = template.Library()


@register.simple_tag
def build_absolute_uri(request, location):
    return request.build_absolute_uri(location)
