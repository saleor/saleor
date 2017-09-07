from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from saleor.core.permissions import get_user_permissions, update_permissions
from .forms import PermissionsForm
from ..views import staff_member_required
from ...core.utils import get_paginator_items
from ...userprofile.models import User


@staff_member_required
def staff_list(request):
    staff_members = (
        User.objects
        .filter(is_staff=True)
    )
    staff_members = get_paginator_items(staff_members, 30, request.GET.get('page'))
    ctx = {'staff': staff_members}
    return TemplateResponse(request, 'dashboard/staff/list.html', ctx)


@staff_member_required
def staff_details(request, pk):
    queryset = User.objects.filter(is_staff=True)
    staff_member = get_object_or_404(queryset, pk=pk)

    ctx = {'staff_member': staff_member}

    if not staff_member.is_superuser:
        user_permissions = get_user_permissions(user=staff_member)
        form = PermissionsForm(request.POST or user_permissions)
        ctx['form'] = form
        if form.is_valid():
            for category, permissions in form.cleaned_data.items():
                update_permissions(
                    user=staff_member, pk=pk, permissions=permissions)

    return TemplateResponse(request, 'dashboard/staff/detail.html', ctx)
