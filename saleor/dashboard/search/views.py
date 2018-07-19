from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from ..views import staff_member_required
from .forms import DashboardSearchForm


def limit_results(*results):
    """Pass-through only first few best items for each result query."""
    limit = settings.DASHBOARD_SEARCH_LIMIT
    return (qs[:limit] for qs in results)


def get_results(request, form):
    user = request.user
    results = form.search()
    products = results['products']
    orders = results['orders']
    users = results['users']
    if not user.has_perm('order.manage_orders'):
        orders = orders.none()
    if not user.has_perm('account.manage_users'):
        users = users.none()
    return limit_results(products, orders, users)


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
        products, orders, users = get_results(request, form)
        query = form.cleaned_data['q']
    ctx = {
        'form': form,
        'query': query,
        'products': products,
        'orders': orders,
        'users': users,
        'query_string': '?q=%s' % query}
    return render(request, 'dashboard/search/results.html', ctx)
