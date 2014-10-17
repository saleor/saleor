from django.template import Library

register = Library()


@register.simple_tag(takes_context=True)
def construct_get_query(context, **params):
    request_get = context['request'].GET.dict()
    if not (request_get or params):
        return ''

    for param in params.keys():
        if param in request_get:
            del request_get[param]

    query = '?' + _format_params(params)
    if request_get:
        query += '&' + _format_params(request_get)
    return query


def _format_params(params):
    return '&'.join(['%s=%s' % (param, value)
                    for param, value in params.items()])
