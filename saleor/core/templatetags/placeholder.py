from django.template import Library
from django.contrib.staticfiles.templatetags.staticfiles import static

register = Library()


@register.simple_tag
def placeholder(size):
    return static('/images/placeholder{size}x{size}.png'.format(size=size))
