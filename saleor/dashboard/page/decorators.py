from functools import wraps

from django.shortcuts import get_object_or_404

from ...page.models import Page
from .modals import modal_protected_page


def unprotected_page_required(view):
    @wraps(view)
    def _decorated_view(request, pk, *args, **kwargs):
        page = get_object_or_404(Page, pk=pk)
        if page.is_protected:
            return modal_protected_page(request, page=page)
        return view(request, *args, page=page, **kwargs)
    return _decorated_view
