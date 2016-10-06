from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.shortcuts import render

from haystack.forms import SearchForm
from ..product.models import ProductVariant


def search(request):
    form = SearchForm(data=request.GET or None, load_all=True)
    paginate_by = 2
    if form.is_valid():
        results = form.search().models(ProductVariant)
        paginator = Paginator(results, paginate_by)
        page_number = request.GET.get('page', 1)
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            raise Http404("No such page!")
    else:
        page = form.no_query_found()
    ctx = {
        'results': page,
        'query_string': '?q=%s' % form.cleaned_data['q']}
    return render(request, 'search/results.html', ctx)
