from __future__ import unicode_literals

from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.template.response import TemplateResponse

from .forms import PermissionsForm
from ..views import staff_member_required


@staff_member_required
def groups_list(request):
    groups = Group.objects.all()

    ctx = {'groups': groups}
    return TemplateResponse(request, 'dashboard/groups/list.html', ctx)


@staff_member_required
def group_create(request):
    form = PermissionsForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('/dashboard/groups')

    ctx = {'group': 'Add new group', 'form': form}
    return TemplateResponse(request, 'dashboard/groups/detail.html', ctx)


@staff_member_required
def groups_details(request, pk):
    group = Group.objects.get(pk=pk)
    form = PermissionsForm(request.POST or None, instance=group)

    if form.is_valid():
        form.save()

    ctx = {'group': group.name,
           'form': form}
    return TemplateResponse(request, 'dashboard/groups/detail.html', ctx)
