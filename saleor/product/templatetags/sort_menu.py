from django import template

from ..filters import DEFAULT_SORT

register = template.Library()


@register.inclusion_tag('category/_sort_menu.html', takes_context=True)
def sort_menu(context, attributes):
    ctx = {
        'request': context['request'],
        'sort_by': (context['request'].GET.get('sort_by', DEFAULT_SORT)
                    .strip('-')),
        'sort_by_choices': attributes,
        'arrow_down': (context['request'].GET.get('sort_by', DEFAULT_SORT)
                       .startswith('-'))}
    return ctx
