from django.conf import settings
from django.shortcuts import render

from ...order.models import Order
from ...product.models import Product
from ...search.views import get_saleor_paginator_items
from ...userprofile.models import User
from ..views import staff_member_required
from .forms import DashboardSearchForm


@staff_member_required
def search(request):
    form = DashboardSearchForm(data=request.GET or None)
    page_counter = request.GET.get('page', 1)
    query = ''
    queryset_map = {
        Product: Product.objects.prefetch_related('images'),
        Order: Order.objects.prefetch_related('user'),
        User: User.objects.all()}
    if form.is_valid():
        results, total = form.search(queryset_map=queryset_map)
        page = get_saleor_paginator_items(results, settings.PAGINATE_BY, page_counter, total=total)
        query = form.cleaned_data['q']
    else:
        page = []
    ctx = {
        'form': form,
        'query': query,
        'results': page,
        'query_string': '?q=%s' % query}
    return render(request, 'dashboard/search/results.html', ctx)
