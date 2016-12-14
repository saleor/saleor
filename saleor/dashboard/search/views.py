from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .forms import DashboardSearchForm
from ...search.views import paginate_results
from ...product.models import Product
from ...order.models import Order


@staff_member_required
def search(request):
    form = DashboardSearchForm(data=request.GET or None)
    query = ''
    queryset_map = {
        Product: Product.objects.prefetch_related('images'),
        Order: Order.objects.prefetch_related('user')}
    if form.is_valid():
        results = form.search(queryset_map=queryset_map)
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
