from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...userprofile.models import User
from ...settings import DASHBOARD_PAGINATE_BY
from ..views import staff_member_required, superuser_required


@staff_member_required
@permission_required('userprofile.view_user')
def customer_list(request):
    customers = (
        User.objects
        .prefetch_related('orders', 'addresses')
        .select_related('default_billing_address', 'default_shipping_address')
        .annotate(
            num_orders=Count('orders', distinct=True),
            last_order=Max('orders', distinct=True))
        .order_by('email'))
    customers = get_paginator_items(
        customers, DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {'customers': customers}
    return TemplateResponse(request, 'dashboard/customer/list.html', ctx)


@staff_member_required
@permission_required('userprofile.view_user')
def customer_details(request, pk):
    queryset = User.objects.prefetch_related(
        'orders', 'addresses').select_related(
        'default_billing_address', 'default_shipping_address')
    customer = get_object_or_404(queryset, pk=pk)
    customer_orders = customer.orders.all()
    ctx = {'customer': customer, 'customer_orders': customer_orders}
    return TemplateResponse(request, 'dashboard/customer/detail.html', ctx)


@superuser_required
def customer_promote_to_staff(request, pk):
    customer = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        customer.is_staff = True
        customer.save()
        msg = pgettext_lazy(
            'Dashboard message',
            'Customer %s promoted to staff member') % customer
        messages.success(request, msg)
        return redirect('dashboard:customer-details', pk=customer.pk)
    return TemplateResponse(
        request, 'dashboard/customer/modal/confirm_promote.html',
        {'customer': customer})
