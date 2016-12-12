from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from saleor.product.models import Product
from ...search.forms import SearchForm
from ...search.views import paginate_results
from .forms import ModelFilteredSearchForm


@staff_member_required
def search(request):
    form = SearchForm(data=request.GET or None)
    query = ''
    if form.is_valid():
        results = form.search(model_or_queryset=Product.objects.all())
        page = paginate_results(results, request.GET, 25)
        query = form.cleaned_data['q']
    else:
        page = []
    ctx = {
        'form': form,
        'query': query,
        'results': page,
        'query_string': '?q=%s' % query}
    return render(request, 'dashboard/search/results.html', ctx)
