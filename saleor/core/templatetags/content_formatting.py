import json

from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("_content_formatting.html")
def format_content(content_json, content_html):
    if settings.USE_JSON_CONTENT:
        return {"content_json": json.dumps(content_json)}
    return {"content_html": content_html}
