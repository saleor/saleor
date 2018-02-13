from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .models import Page


def page_detail(request, url):
    if not url.startswith('/'):
        url = '/' + url
    try:
        page = get_object_or_404(
            Page.objects.get_available(
                allow_draft=request.user.is_staff), url=url)
    except Http404:
        if not url.endswith('/') and settings.APPEND_SLASH:
            url += '/'
            if Page.objects.filter(url=url).exists():
                return HttpResponsePermanentRedirect('%s/' % request.path)
            else:
                raise
        else:
            raise
    response = TemplateResponse(request, 'page/details.html', {'page': page})
    return response.render()
