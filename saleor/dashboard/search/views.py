from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from haystack.forms import SearchForm

from ...order.models import Order
from ...product.models import Product
from ...search.views import paginate_results
from ...userprofile.models import User


@staff_member_required
def search(request):
    form = SearchForm(data=request.GET or None, load_all=True)
    if form.is_valid():
        results = form.search().models(Order, Product, User)
        page = paginate_results(results, request.GET, 25)
    else:
        page = form.no_query_found()
    query = form.cleaned_data['q']
    ctx = {
        'query': query,
        'results': page,
        'query_string': '?q=%s' % query}
    return render(request, 'dashboard/search/results.html', ctx)
