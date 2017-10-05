from django import template

register = template.Library()


@register.inclusion_tag('category/_sort_by.html', takes_context=True)
def sort_by(context, attribute):
    context['label'] = attribute['label']
    context['ascending_attribute'] = attribute['value']
    context['descending_attribute'] = '-' + str(attribute['value'])
    return context
