from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...account.models import Company
from ...core.utils import get_paginator_items
from ..emails import send_set_password_email
from ..views import staff_member_required
from .filters import UserFilter
from .forms import CustomerForm


@staff_member_required
@permission_required('account.view_company')
def customer_list(request):
    companies = (
        Company.objects
        .select_related('default_billing_address')
        .order_by('name'))
    company_filter = UserFilter(request.GET, queryset=companies)
    companies = get_paginator_items(
        company_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'companies': companies, 'filter_set': company_filter,
        'is_empty': not company_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/ompany/list.html', ctx)


@staff_member_required
@permission_required('account.view_company')
def company_details(request, pk):
    queryset = Company.objects.select_related(
            'default_billing_address', 'default_shipping_address')
    company = get_object_or_404(queryset, pk=pk)
    company_contacts = customer.contacts.all()
    ctx = {'company': company, 'company_contacts': company_contacts}
    return TemplateResponse(request, 'dashboard/company/detail.html', ctx)


@staff_member_required
@permission_required('account.edit_company')
def company_create(request):
    company = Company()
    form = CompanyForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added company %s' % company)
        messages.success(request, msg)
        return redirect('dashboard:company-details', pk=company.pk)
    ctx = {'form': form, 'company': company}
    return TemplateResponse(request, 'dashboard/company/form.html', ctx)


@staff_member_required
@permission_required('account.edit_company')
def company_edit(request, pk=None):
    company = get_object_or_404(User, pk=pk)
    form = CustomerForm(request.POST or None, instance=company)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated company %s' % company)
        messages.success(request, msg)
        return redirect('dashboard:company-details', pk=company.pk)
    ctx = {'form': form, 'company': company}
    return TemplateResponse(request, 'dashboard/company/form.html', ctx)
