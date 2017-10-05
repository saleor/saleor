from django import template

register = template.Library()


@register.inclusion_tag('category/_sort_menu.html', takes_context=True)
def sort_menu(context, attributes):
    ordering_options = []
    for attr in [a['value'] for a in attributes]:
        ordering_options.append(attr)
        ordering_options.append('-' + str(attr))
    choices = [a['label'] for a in attributes]
    context['sort_by_choices'] = attributes
    get_sort_by = context['request'].GET.get('sort_by', 'name')
    context['choice'] = choices[int(ordering_options.index(get_sort_by) / 2)]
    context['arrow_up'] = \
        (context['request'].GET.get('sort_by', 'name')[0] != '-')
    return context
