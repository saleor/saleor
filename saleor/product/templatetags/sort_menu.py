from django import template

register = template.Library()


@register.inclusion_tag('category/_sort_menu.html', takes_context=True)
def sort_menu(context, attribute):
    t = []
    for attr in [a[0] for a in attribute]:
        t.append(attr)
        t.append('-' + str(attr))
    choices = [a[1] for a in attribute]
    context['sort_by_choices'] = [{'label': a[1],
                                   'value': a[0]} for a in attribute]
    context['choice'] = choices[int(t.index(context['request'].GET.get('sort_by', 'name')) / 2)]
    context['arrow_up'] = (context['request'].GET.get('sort_by', 'name')[0] != '-')
    return context
