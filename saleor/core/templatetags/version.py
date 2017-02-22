from django.template import Library
from ...version import __version__

register = Library()


@register.simple_tag
def version():
    return __version__
