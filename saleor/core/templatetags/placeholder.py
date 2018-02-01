from django.conf import settings
from django.template import Library

register = Library()


@register.simple_tag
def placeholder(size):
    return '{static_url}images/placeholder{size}x{size}.png'.format(
        static_url=settings.STATIC_URL, size=size)
