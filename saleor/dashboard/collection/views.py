from django.template.response import TemplateResponse
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import pgettext_lazy

from ...product.models import Collection
from ...core.utils import get_paginator_items
from ..views import staff_member_required
from .forms import CollectionForm


@staff_member_required
@permission_required('product.view_product')
def collection_list(request):
    collections = Collection.objects.prefetch_related('products').all()
    collections = get_paginator_items(collections, 30, request.GET.get('page'))
    ctx = {'collections': collections}
    return TemplateResponse(request,
                            'dashboard/collection/list.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def collection_create(request):
    collection = Collection()
    form = CollectionForm(request.POST or None)
    if form.is_valid():
        collection = form.save()
        msg = pgettext_lazy('Collection message', 'Added collection')
        messages.success(request, msg)
        return redirect('dashboard:collection-list')
    ctx = {'collection': collection, 'form': form}
    return TemplateResponse(request, 'dashboard/collection/detail.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def collection_update(request, pk=None):
    collection = get_object_or_404(Collection, pk=pk)
    form = CollectionForm(request.POST or None, instance=collection)
    if form.is_valid():
        collection = form.save()
        msg = pgettext_lazy('Collection message', 'Updated collection')
        messages.success(request, msg)
        return redirect('dashboard:collection-update', pk=collection.pk)
    ctx = {'collection': collection, 'form': form}
    return TemplateResponse(request, 'dashboard/collection/detail.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def collection_delete(request, pk=None):
    collection = get_object_or_404(Collection, pk=pk)
    if request.method == 'POST':
        collection.delete()
        msg = pgettext_lazy('Collection message', 'Deleted collection')
        messages.success(request, msg)
        if request.is_ajax():
            response = {'redirectUrl': reverse('dashboard:collection-list')}
            return JsonResponse(response)
        return redirect('dashboard:collection-list')
    ctx = {'collection': collection}
    return TemplateResponse(request, 'dashboard/collection/modal_delete.html',
                            ctx)
