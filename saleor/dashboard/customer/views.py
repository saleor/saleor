from __future__ import unicode_literals

from django.db.models import Count, Max
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from .forms import CustomerSearchForm
from ..views import staff_member_required
from ...core.utils import get_paginator_items
from ...userprofile.models import User


@staff_member_required
def customer_list(request):
    customers = (
        User.objects
        .prefetch_related('orders', 'addresses')
        .select_related('default_billing_address', 'default_shipping_address')
        .annotate(
            num_orders=Count('orders', distinct=True),
            last_order=Max('orders', distinct=True)))

    form = CustomerSearchForm(request.GET or None, queryset=customers)
    form_values = [(field.name, field.value() or '') for field in form]
    if form.is_valid():
        customers = form.search()
    else:
        customers = customers.filter(
            orders__status__in=['new', 'payment-pending', 'fully-paid'])
    title = _('Results (%s)') % len(customers)

    customers = get_paginator_items(customers, 30, request.GET.get('page'))
    ctx = {'customers': customers, 'form': form, 'title': title,
           'default_pagination_params': form_values}
    return TemplateResponse(request, 'dashboard/customer/list.html', ctx)


@staff_member_required
def customer_details(request, pk):
    queryset = User.objects.prefetch_related(
        'orders', 'addresses').select_related('default_billing_address')
    customer = get_object_or_404(queryset, pk=pk)
    customer_orders = customer.orders.all()
    ctx = {'customer': customer, 'customer_orders': customer_orders}
    return TemplateResponse(request, 'dashboard/customer/detail.html', ctx)
