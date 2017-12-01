from __future__ import unicode_literals

from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from ..views import staff_member_required
from .forms import DashboardSearchForm


def get_results(request, form):
    user = request.user
    results = form.search()
    products = results['products']
    orders = results['orders']
    users = results['users']
    if not user.has_perm('order.view_order'):
        orders = orders.none()
    if not user.has_perm('userprofile.view_user'):
        users = users.none()
    return products, orders, users


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
