from django import template
import markdown as markd
from django.utils.safestring import mark_safe
register = template.Library()

@register.filter
def markdown(text):
    #should use bleach here instad of safe_mode="remove"?
    return mark_safe(markd.markdown(text, safe_mode="remove", output_format="html5"))
    pass
