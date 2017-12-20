from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import npgettext_lazy, pgettext_lazy

from ...core.utils import get_paginator_items
from ..views import staff_member_required
from .filters import GroupFilter
from .forms import GroupPermissionsForm


@staff_member_required
@permission_required('userprofile.view_group')
def group_list(request):
    groups = (Group.objects.all().prefetch_related('permissions')
              .order_by('name'))
    group_filter = GroupFilter(request.GET, queryset=groups)
    groups = [{'name': group, 'permissions': group.permissions.all()}
              for group in group_filter.qs]
    groups = get_paginator_items(
        groups, settings.DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    summary_msg = npgettext_lazy(
        'Filter set results summary',
        'Found %(counter)d matching group',
        'Found %(counter)d matching groups',
        'counter') % {'counter': group_filter.qs.count() }
    ctx = {
        'groups': groups, 'filter': group_filter,
        'is_empty': not group_filter.queryset.exists(),
        'summary_msg': summary_msg}
    return TemplateResponse(request, 'dashboard/group/list.html', ctx)


@staff_member_required
@permission_required('userprofile.edit_group')
def group_create(request):
    group = Group()
    form = GroupPermissionsForm(request.POST or None)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy('Dashboard message', 'Created group')
        messages.success(request, msg)
        return redirect('dashboard:group-list')
    ctx = {'group': group, 'form': form}
    return TemplateResponse(request, 'dashboard/group/detail.html', ctx)


@staff_member_required
@permission_required('userprofile.edit_group')
def group_details(request, pk):
    group = Group.objects.get(pk=pk)
    form = GroupPermissionsForm(request.POST or None, instance=group)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated group %s') % group.name
        messages.success(request, msg)
        return redirect('dashboard:group-list')
    ctx = {'group': group, 'form': form}
    return TemplateResponse(request, 'dashboard/group/detail.html', ctx)


@staff_member_required
@permission_required('userprofile.edit_group')
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.delete()
        msg = pgettext_lazy('Dashboard message', 'Removed group %s') % group
        messages.success(request, msg)
        return redirect('dashboard:group-list')
    return TemplateResponse(
        request, 'dashboard/group/modal/confirm_delete.html', {'group': group})
