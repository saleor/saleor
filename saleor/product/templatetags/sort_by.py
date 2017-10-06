from django import template

register = template.Library()


@register.inclusion_tag('category/_sort_by.html', takes_context=True)
def sort_by(context, attribute):
    return {'request': context['request'],
            'label': attribute['label'],
            'ascending_attribute': attribute['value'],
            'descending_attribute': '-' + str(attribute['value'])}
