from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.shortcuts import render

from ...order.models import Order
from ...product.models import Product
from ...search.views import paginate_results
from ...userprofile.models import User
from .forms import DashboardSearchForm


@staff_member_required
def search(request):
    form = DashboardSearchForm(data=request.GET or None)
    query = ''
    queryset_map = {
        Product: Product.objects.prefetch_related('images'),
        Order: Order.objects.prefetch_related('user'),
        User: User.objects.all()}
    if form.is_valid():
        results = form.search(queryset_map=queryset_map)
        page = paginate_results(results, request.GET, settings.PAGINATE_BY)
        query = form.cleaned_data['q']
    else:
        page = []
    ctx = {
        'form': form,
        'query': query,
        'results': page,
        'query_string': '?q=%s' % query}
    return render(request, 'dashboard/search/results.html', ctx)
