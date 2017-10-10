from __future__ import unicode_literals

from django.core.paginator import Paginator, InvalidPage
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from .forms import SearchForm
from ..product.utils import products_with_details, products_with_availability


def paginate_results(results, page_counter, total,
                     paginate_by=settings.PAGINATE_BY):
    paginator = Paginator(results, paginate_by)
    # TODO: Think about clean and nice solution to pagination problem
    page_number = 1
    try:
        page = paginator.page(page_number)
        page.number = page_counter
        page.paginator.num_pages = total // settings.PAGINATE_BY + 1
    except InvalidPage:
        raise Http404('No such page!')
    return page


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

    page = paginate_results(results, page_counter, total)

    ctx = {
        'query': query,
        'results': page,
        'pages': total,
        'query_string': '?q=%s&%s' % (query, page_counter)}
    return render(request, 'search/results.html', ctx)
