from __future__ import unicode_literals
from math import ceil

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from .forms import SearchForm
from ..product.utils import products_with_details, products_with_availability


class SaleorPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        total = kwargs.pop('total', 0)
        super(SaleorPaginator, self).__init__(*args, **kwargs)
        self._count = total

    def page(self, number):
        number = self.validate_number(number)
        return Page(self.object_list, number, self)

    @property
    def count(self):
        return self._count


def get_saleor_paginator_items(items, paginate_by, page, total):
    paginator = SaleorPaginator(items, paginate_by, total=total)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)
    return items


def search(request):
    form = SearchForm(data=request.GET or None)
    page_counter = int(request.GET.get('page', 1))
    total = 0

    if form.is_valid():
        visible_products = products_with_details(request.user)
        results, total = form.search(model_or_queryset=visible_products,
                                     page=page_counter,
                                     page_size=settings.PAGINATE_BY)
        results = products_with_availability(
            results, discounts=request.discounts,
            local_currency=request.currency)
        results = list(results)
        query = form.cleaned_data.get('q', '')
    else:
        results = []
        query = ''

    page = get_saleor_paginator_items(
        results, settings.PAGINATE_BY, page_counter, total=total)

    ctx = {
        'query': query,
        'results': page,
        'pages': total,
        'query_string': '?q=%s&%s' % (query, page_counter)}
    return render(request, 'search/results.html', ctx)
