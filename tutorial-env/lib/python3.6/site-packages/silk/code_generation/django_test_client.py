import autopep8

import jinja2
# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib.parse import urlencode
from silk.profiling.dynamic import is_str_typ


template = """
from django.test import Client
c = Client()
response = c.{{ lower_case_method }}(path='{{ path }}'{% if data or content_type %},{% else %}){% endif %}{% if data %}
data={{ data }}{% endif %}{% if data and content_type %},{% elif data %}){% endif %}{% if content_type %}
content_type='{{ content_type }}'){% endif %}
"""


def _encode_query_params(query_params):
    try:
        query_params = urlencode(query_params)
    except TypeError:
        pass
    return '?' + query_params


def gen(path,
        method=None,
        query_params=None,
        data=None,
        content_type=None):
    # generates python code representing a call via django client.
    # useful for use in testing
    method = method.lower()
    t = jinja2.Template(template)
    if method == 'get':
        r = t.render(path=path,
                     data=query_params,
                     lower_case_method=method,
                     content_type=content_type)
    else:
        if query_params:
            query_params = _encode_query_params(query_params)
            path += query_params
        if is_str_typ(data):
            data = "'%s'" % data
        r = t.render(path=path,
                     data=data,
                     lower_case_method=method,
                     query_params=query_params,
                     content_type=content_type)
    return autopep8.fix_code(
        r, options=autopep8.parse_args(['--aggressive', ''])
    )
