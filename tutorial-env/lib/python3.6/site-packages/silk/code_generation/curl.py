import json

# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib.parse import urlencode

import jinja2

curl_template = """
curl {% if method %}-X {{ method }}{% endif %}
{% if content_type %}-H 'Content-Type: {{ content_type }}'{% endif %}
{% if modifier %}{{ modifier }} {% endif %}{% if body %}'{{ body }}'{% endif %}
{{ url }}{% if query_params %}{{ query_params }}{% endif %}
{% if extra %}{{ extra }}{% endif %}
"""


def _curl_process_params(body, content_type, query_params):
    extra = None
    modifier = None
    if query_params:
        try:
            query_params = urlencode(
                [(k, v.encode('utf8')) for k, v in query_params.items()]
            )
        except TypeError:
            pass
        query_params = '?' + str(query_params)
    if 'json' in content_type or 'javascript' in content_type:
        if isinstance(body, dict):
            body = json.dumps(body)
        modifier = '-d'
    # See http://curl.haxx.se/docs/manpage.html#-F
    # for multipart vs x-www-form-urlencoded
    # x-www-form-urlencoded is same way as browser,
    # multipart is RFC 2388 which allows file uploads.
    elif 'multipart' in content_type or 'x-www-form-urlencoded' in content_type:
        try:
            body = ' '.join(['%s=%s' % (k, v) for k, v in body.items()])
        except AttributeError:
            modifier = '-d'
        else:
            content_type = None
            modifier = '-F'
    elif body:
        body = str(body)
        modifier = '-d'
    else:
        modifier = None
        content_type = None
    # TODO: Clean up.
    return modifier, body, query_params, content_type, extra


def curl_cmd(url, method=None, query_params=None, body=None, content_type=None):
    if not content_type:
        content_type = 'text/plain'
    modifier, body, query_params, content_type, extra = _curl_process_params(
        body, content_type, query_params
    )
    t = jinja2.Template(curl_template)
    return ' '.join(t.render(url=url,
                             method=method,
                             query_params=query_params,
                             body=body,
                             modifier=modifier,
                             content_type=content_type,
                             extra=extra).split('\n'))
