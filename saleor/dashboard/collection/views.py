from django.template.response import TemplateResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from ...product.models import Collection
from ...core.utils import get_paginator_items
from ..views import staff_member_required
from .forms import CollectionForm


@staff_member_required
def collection_list(request):
    collections = Collection.objects.all()
    collections = get_paginator_items(collections, 30, request.GET.get('page'))
    ctx = {'colections': collections}
    return TemplateResponse(request,
                            'dashboard/collection/list.html', ctx)


@staff_member_required
def collection_create(request):
    collection = Collection()
    form = CollectionForm(request.POST or None)
    if form.is_valid():
        collection = form.save()
        messages.success(request, _('Added collection %s') % collection)
        return redirect('dashboard:collection-list')
    ctx = {'collection': collection, 'form': form}
    return TemplateResponse(request, 'dashboard/collection/detail.html', ctx)
