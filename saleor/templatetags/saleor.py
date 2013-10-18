from itertools import izip_longest

from django.template import Library

register = Library()


@register.filter
def slice(items, group_size=1):
    args = [iter(items)] * group_size
    return (filter(None, group)
            for group in izip_longest(*args, fillvalue=None))
