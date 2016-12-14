from django.template import Library

register = Library()


@register.assignment_tag(takes_context=True)
def get_default_country(context):
    request = context['request']
    if request.user:
        default_shipping = request.user.default_shipping_address
        if default_shipping:
            return default_shipping.country
    return request.country
