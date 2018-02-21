from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .models import Page


def page_detail(request, url):
    page = get_object_or_404(
        Page.objects.get_available(
            allow_draft=request.user.is_staff), url=url)
    return TemplateResponse(request, 'page/details.html', {'page': page})
