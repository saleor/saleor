from django import template

register = template.Library()


@register.inclusion_tag('category/_sort_by.html', takes_context=True)
def sort_by(context, attribute):
    context['attribute'] = attribute
    context['negativ_attribute'] = '-' + attribute
    return context
