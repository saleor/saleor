import json

from django import template
from django.conf import settings
from draftjs_sanitizer import SafeJSONEncoder

register = template.Library()


@register.inclusion_tag("_content_formatting.html")
def format_content(content_json, content_html):
    if settings.USE_JSON_CONTENT:
        return {"content_json": json.dumps(content_json, cls=SafeJSONEncoder)}
    return {"content_html": content_html}
