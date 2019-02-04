from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import pgettext_lazy
from django.views.decorators.http import require_POST

from ...core.utils import get_paginator_items
from ...product.models import Collection
from ..menu.utils import get_menus_that_needs_update, update_menus
from ..views import staff_member_required
from .filters import CollectionFilter
from .forms import AssignHomepageCollectionForm, CollectionForm


@staff_member_required
@permission_required('product.manage_products')
def collection_list(request):
    site_settings = request.site.settings
    assign_homepage_col_form = AssignHomepageCollectionForm(
        request.POST or None, instance=site_settings)
    if request.method == 'POST' and assign_homepage_col_form.is_valid():
        assign_homepage_col_form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated homepage collection')
        messages.success(request, msg)
        return redirect('dashboard:collection-list')
    collections = Collection.objects.prefetch_related('products').all()
    collection_filter = CollectionFilter(request.GET, queryset=collections)
    collections = get_paginator_items(
        collection_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'collections': collections, 'filter_set': collection_filter,
        'is_empty': not collection_filter.queryset.exists(),
        'assign_homepage_col_form': assign_homepage_col_form}
    return TemplateResponse(
        request, 'dashboard/collection/list.html', ctx)


@staff_member_required
@permission_required('product.manage_products')
def collection_create(request):
    collection = Collection()
    form = CollectionForm(
        request.POST or None, request.FILES or None, instance=collection)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy('Collection message', 'Added collection')
        messages.success(request, msg)
        return redirect('dashboard:collection-list')
    ctx = {'collection': collection, 'form': form}
    return TemplateResponse(request, 'dashboard/collection/detail.html', ctx)


@staff_member_required
@permission_required('product.manage_products')
def collection_update(request, pk=None):
    collection = get_object_or_404(Collection, pk=pk)
    form = CollectionForm(
        request.POST or None, request.FILES or None, instance=collection)
    if form.is_valid():
        collection = form.save()
        msg = pgettext_lazy('Collection message', 'Updated collection')
        messages.success(request, msg)
        return redirect('dashboard:collection-update', pk=collection.pk)
    is_unpublish_restricted = (
        collection == request.site.settings.homepage_collection and
        collection.is_published)
    ctx = {
        'collection': collection, 'form': form,
        'is_unpublish_restricted': is_unpublish_restricted}
    return TemplateResponse(request, 'dashboard/collection/detail.html', ctx)


@staff_member_required
@permission_required('product.manage_products')
def collection_delete(request, pk=None):
    collection = get_object_or_404(Collection, pk=pk)
    if request.method == 'POST':
        menus = get_menus_that_needs_update(collection=collection)
        collection.delete()
        if menus:
            update_menus(menus)
        msg = pgettext_lazy('Collection message', 'Deleted collection')
        messages.success(request, msg)
        if request.is_ajax():
            response = {'redirectUrl': reverse('dashboard:collection-list')}
            return JsonResponse(response)
        return redirect('dashboard:collection-list')
    ctx = {'collection': collection}
    return TemplateResponse(
        request, 'dashboard/collection/confirm_delete.html', ctx)


@require_POST
@staff_member_required
@permission_required('product.manage_products')
def collection_toggle_is_published(request, pk):
    collection = get_object_or_404(Collection, pk=pk)
    collection.is_published = not collection.is_published
    collection.save(update_fields=['is_published'])
    return JsonResponse(
        {'success': True, 'is_published': collection.is_published})
