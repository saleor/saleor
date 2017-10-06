from django import template

register = template.Library()


@register.inclusion_tag('category/_sort_menu.html', takes_context=True)
def sort_menu(context, attributes):
    context['sort_by'] = \
        context['request'].GET.get('sort_by', 'name').strip('-')
    context['sort_by_choices'] = attributes
    context['arrow_down'] = \
        (context['request'].GET.get('sort_by', 'name').startswith('-'))
    return context
