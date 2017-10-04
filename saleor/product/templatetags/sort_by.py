from django import template

register = template.Library()


@register.inclusion_tag('category/_sort_by.html', takes_context=True)
def sort_by(context, attribute):
    context['ascending_attribute'] = attribute
    context['descending_attribute'] = '-' + str(attribute)
    return context
