from django import template
from django.urls import translate_url as django_translate_url

register = template.Library()


@register.simple_tag
def build_absolute_uri(request, location):
    return request.build_absolute_uri(location)


@register.simple_tag
def translate_url(url, lang_code):
    return django_translate_url(url, lang_code)
