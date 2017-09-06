from __future__ import unicode_literals

from django import forms
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.contrib.auth.models import Permission

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

    form = PermissionsForm(request.POST or None)

    if form.is_valid():
        print form.cleaned_data

        for category, permissions in form.cleaned_data.items():
            add_permissions(user=staff_member, category=category,
                            permissions=permissions)

    ctx = {'staff_member': staff_member, 'form': form, "permissions": permissions}
    return TemplateResponse(request, 'dashboard/staff/detail.html', ctx)


def add_permissions(user, category, permissions):
    print user.user_permissions
    # user.user_permissions.set(['product_view'])
    print user.user_permissions

