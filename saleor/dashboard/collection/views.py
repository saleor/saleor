from django.template.response import TemplateResponse

from ...product.models import Collection
from ...core.utils import get_paginator_items
from ..views import staff_member_required


@staff_member_required
def collection_list(request):
    collections = Collection.objects.all()
    collections = get_paginator_items(collections, 30, request.GET.get('page'))
    ctx = {'colections': collections}
    return TemplateResponse(request,
                            'dashboard/collection/list.html', ctx)
