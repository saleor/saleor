from django import template
from ..models import Category

register = template.Library()


@register.inclusion_tag('category/_list.html')
def categories_list():
    return {'categories': Category.objects.filter(hidden=False)}
