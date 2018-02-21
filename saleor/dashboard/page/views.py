from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import (get_paginator_items)
from ...page.models import Page
from ..views import staff_member_required
from .forms import PageForm


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
    if form.is_valid():
        form.save()
        msg = pgettext_lazy('Dashboard message', 'Saved page')
        messages.success(request, msg)
        return redirect('dashboard:page-list')
    ctx = {
        'page': page, 'form': form}
        # 'redirect_form': redirect_form}
    return TemplateResponse(request, 'dashboard/page/form.html', ctx)


@staff_member_required
def page_delete(request, pk):
    page = get_object_or_404(Page, pk=pk)
    if request.POST:
        page.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed page %s') % (page.title,)
        messages.success(request, msg)
        return redirect('dashboard:page-list')
    ctx = {'page': page}
    return TemplateResponse(request, 'dashboard/page/modal-delete.html', ctx)
