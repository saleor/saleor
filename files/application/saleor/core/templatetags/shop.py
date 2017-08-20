try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from django.template import Library

register = Library()


@register.filter
def slice(items, group_size=1):
    args = [iter(items)] * group_size
    return (filter(None, group)
            for group in zip_longest(*args, fillvalue=None))
