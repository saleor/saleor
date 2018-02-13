from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...core.utils import (get_paginator_items, invalidate_etag,
                           redirect_after_save)
from ...page.models import Page
from ..views import staff_member_required
from .forms import AssetUploadFormset, PageForm


@staff_member_required
def page_list(request):
    pages = Page.objects.all()
    pages = get_paginator_items(pages, 30, request.GET.get('page'))
    ctx = {'pages': pages}
    return TemplateResponse(request, 'dashboard/page/list.html', ctx)


@staff_member_required
def page_edit(request, pk):
    page = get_object_or_404(Page, pk=pk)
    return _page_edit(request, page)


@staff_member_required
def page_add(request):
    page = Page()
    return _page_edit(request, page)


def _page_edit(request, page):
    form = PageForm(request.POST or None, instance=page)
    asset_formset = AssetUploadFormset(
        request.POST or None, request.FILES or None, instance=page)
    stay, redirect_form = redirect_after_save(request.POST or None)
    if form.is_valid() and asset_formset.is_valid():
        page = form.save()
        asset_formset.save()
        invalidate_etag('pages', view_kwargs={'url': page.url})
        messages.success(request, _('Saved page %s' % page))
        if stay:
            return redirect('dashboard:page-edit', pk=page.pk)
        else:
            return redirect('dashboard:page-list')
    ctx = {
        'page': page, 'form': form, 'asset_formset': asset_formset,
        'redirect_form': redirect_form}
    return TemplateResponse(request, 'dashboard/page/form.html', ctx)


@staff_member_required
def page_delete(request, pk):
    page = get_object_or_404(Page, pk=pk)
    if request.POST:
        page.delete()
        messages.success(request, _('Deleted page %s' % page))
        return redirect('dashboard:page-list')
    ctx = {'page': page}
    return TemplateResponse(request, 'dashboard/page/modal-delete.html', ctx)
