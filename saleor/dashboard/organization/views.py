from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...account.models import Organization, User
from ...core.utils import get_paginator_items
from ...order.models import Order
from ..views import staff_member_required
from .filters import OrganizationFilter
from .forms import OrganizationDeleteForm, OrganizationForm


@staff_member_required
@permission_required('account.manage_organizations')
def organization_list(request):
    organizations = (
        Organization.objects
        .select_related('default_billing_address')
        .order_by('name'))
    organization_filter = OrganizationFilter(request.GET, queryset=organizations)
    organizations = get_paginator_items(
        organization_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'organizations': organizations, 'filter_set': organization_filter,
        'is_empty': not organization_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/organization/list.html', ctx)


@staff_member_required
@permission_required('account.manage_organizations')
def organization_details(request, pk):
    queryset = Organization.objects.select_related('default_billing_address')
    organization = get_object_or_404(queryset, pk=pk)
    organization_orders = Order.objects.filter(user__organization=organization)
    organization_users = User.objects.filter(organization=organization)
    ctx = {'organization': organization, 'organization_users': organization_users,
           'organization_orders': organization_orders}
    return TemplateResponse(request, 'dashboard/organization/detail.html', ctx)


@staff_member_required
@permission_required('account.manage_organizations')
def organization_create(request):
    organization = Organization()
    form = OrganizationForm(request.POST or None, instance=organization)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added organization %s' % organization)
        messages.success(request, msg)
        return redirect('dashboard:organization-details', pk=organization.pk)
    ctx = {'form': form, 'organization': organization}
    return TemplateResponse(request, 'dashboard/organization/form.html', ctx)


@staff_member_required
@permission_required('account.manage_organizations')
def organization_edit(request, pk=None):
    organization = get_object_or_404(Organization, pk=pk)
    form = OrganizationForm(request.POST or None, instance=organization)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated organization %s' % organization)
        messages.success(request, msg)
        return redirect('dashboard:organization-details', pk=organization.pk)
    ctx = {'form': form, 'organization': organization}
    return TemplateResponse(request, 'dashboard/organization/form.html', ctx)


@staff_member_required
@permission_required('account.manage_organizations')
def ajax_organizations_list(request):
    queryset = Organization.objects.select_related('default_billing_address')
    search_query = request.GET.get('q', '')
    if search_query:
        queryset = queryset.filter(
            Q(default_billing_address__name__icontains=search_query))

    organizations = [
        {'id': organization.pk, 'text': organization.get_ajax_label()}
        for organization in queryset]
    return JsonResponse({'results': organizations})


@staff_member_required
@permission_required('account.manage_organizations')
def organization_delete(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    form = OrganizationDeleteForm(
        request.POST or None, instance=organization, user=request.user)
    status = 200
    allow_delete = not organization.user_set.exists()

    if request.method == 'POST' and form.is_valid():
        organization.delete()
        msg = pgettext_lazy(
            'Dashboard message',
            '%(organization_name)s successfully removed') % {
                'organization_name': organization}
        messages.success(request, msg)
        return redirect('dashboard:organizations')
    elif request.method == 'POST' and not form.is_valid():
        status = 400
    ctx = {'organization': organization, 'form': form,
           'allow_delete': allow_delete}
    return TemplateResponse(
        request, 'dashboard/organization/modal/confirm_delete.html', ctx,
        status=status)
