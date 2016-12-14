from __future__ import unicode_literals

from django.core.paginator import Paginator, InvalidPage
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from .forms import SearchForm
from ..product.utils import products_with_details


def paginate_results(results, get_data, paginate_by=25):
    paginator = Paginator(results, paginate_by)
    page_number = get_data.get('page', 1)
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        raise Http404('No such page!')
    return page


def search(request):
    form = SearchForm(data=request.GET or None)
    if form.is_valid():
        visible_products = products_with_details(request.user)
        results = form.search(model_or_queryset=visible_products)
        page = paginate_results(results, request.GET, settings.PAGINATE_BY)
    else:
        page = form.no_query_found()
    query = form.cleaned_data['q']
    ctx = {
        'query': query,
        'results': page,
        'query_string': '?q=%s' % query}
    return render(request, 'search/results.html', ctx)
