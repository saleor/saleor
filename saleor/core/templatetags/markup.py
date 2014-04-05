from django import template
register = template.Library()

@register.filter
def markdown(text):
    #pretty simple
    return markdown.markdown(text, safe_mode="remove", output_format="html5")
    pass
