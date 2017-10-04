from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from .forms import StaffForm
from ..views import superuser_required
from ...core.utils import get_paginator_items
from ...userprofile.models import User
from ...settings import DASHBOARD_PAGINATE_BY


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
    form = StaffForm(request.POST or None, instance=staff_member)
    if form.is_valid():
        form.save()
    ctx = {'staff_member': staff_member, 'form': form}
    return TemplateResponse(request, 'dashboard/staff/detail.html', ctx)


@superuser_required
def staff_create(request):
    staff = User()
    staff_form = StaffForm()

    if staff_form.is_valid():
        staff = staff_form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added staff user %s') % staff
        return redirect('dashboard:staff-list', pk=staff.pk)

    ctx = {'form': staff_form}
    return TemplateResponse(request, 'dashboard/staff/detail.html', ctx)
