from __future__ import unicode_literals

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import Group
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from .forms import GroupPermissionsForm
from ..views import staff_member_required


@staff_member_required
def groups_list(request):
    groups = Group.objects.all()

    ctx = {'groups': groups}
    return TemplateResponse(request, 'dashboard/group/list.html', ctx)


@staff_member_required
def group_create(request):
    form = GroupPermissionsForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('/dashboard/groups')

    ctx = {'group': 'Add new group', 'form': form}
    return TemplateResponse(request, 'dashboard/group/detail.html', ctx)


@staff_member_required
def group_details(request, pk):
    group = Group.objects.get(pk=pk)
    form = GroupPermissionsForm(request.POST or None, instance=group)

    if form.is_valid():
        form.save()

    ctx = {'group': group,
           'form': form}
    return TemplateResponse(request, 'dashboard/group/detail.html', ctx)


@staff_member_required
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.delete()
        messages.success(
            request,
            pgettext_lazy('Dashboard message', 'Deleted group %s') % group
        )
        return redirect('dashboard:group-list')
    return TemplateResponse(
        request, 'dashboard/group/modal_group_confirm_delete.html',
        {'group': group}
    )
