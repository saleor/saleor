from django import template
from django.utils.safestring import mark_safe
from markdown import markdown as format_markdown

register = template.Library()


@register.filter
def markdown(text):
    html = format_markdown(text, safe_mode='escape', output_format='html5')
    return mark_safe(html)
