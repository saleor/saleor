from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...userprofile.models import User
from ..emails import send_set_password_email
from ..views import staff_member_required
from .filters import UserFilter
from .forms import CustomerForm


@staff_member_required
@permission_required('userprofile.view_user')
def customer_list(request):
    customers = (
        User.objects
        .filter(
            Q(is_staff=False) | (Q(is_staff=True) & Q(orders__isnull=False)))
        .distinct()
        .prefetch_related('orders', 'addresses')
        .select_related('default_billing_address', 'default_shipping_address')
        .order_by('email'))
    customer_filter = UserFilter(request.GET, queryset=customers)
    customers = get_paginator_items(
        customer_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'customers': customers, 'filter_set': customer_filter,
        'is_empty': not customer_filter.queryset.exists()}
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


@staff_member_required
@permission_required('userprofile.edit_user')
def customer_create(request):
    customer = User()
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added customer %s' % customer)
        send_set_password_email(customer)
        messages.success(request, msg)
        return redirect('dashboard:customer-details', pk=customer.pk)
    ctx = {'form': form, 'customer': customer}
    return TemplateResponse(request, 'dashboard/customer/form.html', ctx)


@staff_member_required
@permission_required('userprofile.edit_user')
def customer_edit(request, pk=None):
    customer = get_object_or_404(User, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated customer %s' % customer)
        messages.success(request, msg)
        return redirect('dashboard:customer-details', pk=customer.pk)
    ctx = {'form': form, 'customer': customer}
    return TemplateResponse(request, 'dashboard/customer/form.html', ctx)
