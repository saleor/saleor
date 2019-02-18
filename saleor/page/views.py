import datetime

from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .utils import pages_visible_to_user


def page_details(request, slug):
    page = get_object_or_404(
        pages_visible_to_user(user=request.user).filter(slug=slug))
    today = datetime.date.today()
    is_visible = (
        page.publication_date is None or page.publication_date <= today)
    return TemplateResponse(
        request, 'page/details.html', {
            'page': page, 'is_visible': is_visible})
