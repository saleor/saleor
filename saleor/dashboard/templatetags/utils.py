import json
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from django.template import Library

register = Library()


@register.filter
def format_json(data, indent=2):
    return json.dumps(json.loads(data), indent=indent)


@register.simple_tag(takes_context=True)
def construct_get_query(context, **params):
    request_get = context['request'].GET.dict()
    if not (request_get or params):
        return ''
    all_params = {}
    all_params.update(request_get)
    all_params.update(params)
    return '?' + urlencode(all_params)
