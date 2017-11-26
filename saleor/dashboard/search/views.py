from django.shortcuts import render

from django.conf import settings
from django.http import Http404

from ..views import staff_member_required
from .forms import DashboardSearchForm


@staff_member_required
def search(request):
    if not settings.ENABLE_SEARCH:
        raise Http404('No such page!')
    form = DashboardSearchForm(data=request.GET or None)
    query = ''
    users = []
    products = []
    orders = []
    if form.is_valid():
        results = form.search()
        users = results['users']
        products = results['products']
        orders = results['orders']
        query = form.cleaned_data['q']
    ctx = {
        'form': form,
        'query': query,
        'products': products,
        'orders': orders,
        'users': users,
        'query_string': '?q=%s' % query}
    return render(request, 'dashboard/search/results.html', ctx)
