from __future__ import unicode_literals

from django.db.models import Count, Max
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from .forms import CustomerSearchForm
from ..utils import paginate
from ..views import staff_member_required
from ...userprofile.models import User


def _get_users_with_open_orders(queryset):
    open_order = ['new', 'payment-pending', 'fully-paid']
    return queryset.filter(orders__status__in=open_order)


@staff_member_required
def customer_list(request):
    customers = User.objects.prefetch_related('orders', 'addresses').annotate(
        num_orders=Count('orders', distinct=True),
        last_order=Max('orders', distinct=True))

    form = CustomerSearchForm(request.GET or None, queryset=customers)
    if form.is_valid():
        customers = form.search()
        title = _('Search results (%s)' % len(customers))
    else:
        customers = _get_users_with_open_orders(customers)
        title = _('Customers with open orders (%s)' % len(customers))

    customers, paginator = paginate(customers, 30, request.GET.get('page'))
    ctx = {'customers': customers, 'form': form, 'title': title,
           'paginator': paginator}
    return TemplateResponse(request, 'dashboard/customer/list.html', ctx)


@staff_member_required
def customer_details(request, pk):
    queryset = User.objects.prefetch_related(
        'orders', 'addresses').select_related('default_billing_address')
    customer = get_object_or_404(queryset, pk=pk)
    ctx = {'customer': customer}
    return TemplateResponse(request, 'dashboard/customer/detail.html', ctx)
