from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from .emails import send_set_password_email
from .forms import StaffForm
from ..views import superuser_required
from ...core.utils import get_paginator_items
from ...settings import DASHBOARD_PAGINATE_BY
from ...userprofile.models import User


@superuser_required
def staff_list(request):
    staff_members = (User.objects.filter(is_staff=True)
                     .prefetch_related('default_billing_address')
                     .order_by('email'))
    staff_members = get_paginator_items(
        staff_members, DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {'staff': staff_members}
    return TemplateResponse(request, 'dashboard/staff/list.html', ctx)


@superuser_required
def staff_details(request, pk):
    queryset = User.objects.filter(is_staff=True)
    staff_member = get_object_or_404(queryset, pk=pk)
    form = StaffForm(
        request.POST or None, instance=staff_member, user=request.user)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated staff member %s') % staff_member
        messages.success(request, msg)
        redirect('dashboard:staff-list')
    ctx = {'staff_member': staff_member, 'form': form}
    return TemplateResponse(request, 'dashboard/staff/detail.html', ctx)


@superuser_required
def staff_create(request):
    staff = User()
    form = StaffForm(request.POST or None, instance=staff)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added staff member %s') % staff
        messages.success(request, msg)
        send_set_password_email(staff)
        return redirect('dashboard:staff-list')
    ctx = {'form': form}
    return TemplateResponse(request, 'dashboard/staff/detail.html', ctx)


@superuser_required
def staff_delete(request, pk):
    queryset = User.objects.prefetch_related(
        'orders')
    staff = get_object_or_404(queryset, pk=pk)
    all_orders_count = staff.orders.count()
    if request.method == 'POST':
        staff.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Deleted staff member %s') % staff
        messages.success(request, msg)
        return redirect('dashboard:staff-list')
    return TemplateResponse(
        request, 'dashboard/staff/modal/confirm_delete.html',
        {'staff': staff, 'orders': all_orders_count})
