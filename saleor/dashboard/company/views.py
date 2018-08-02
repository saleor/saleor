from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...account.models import Company, User
from ...core.utils import get_paginator_items
from ...order.models import Order
from ..views import staff_member_required
from .filters import CompanyFilter
from .forms import CompanyDeleteForm, CompanyForm


@staff_member_required
@permission_required('account.manage_companies')
def company_list(request):
    companies = (
        Company.objects
        .select_related('default_billing_address')
        .order_by('name'))
    company_filter = CompanyFilter(request.GET, queryset=companies)
    companies = get_paginator_items(
        company_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'companies': companies, 'filter_set': company_filter,
        'is_empty': not company_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/company/list.html', ctx)


@staff_member_required
@permission_required('account.manage_companies')
def company_details(request, pk):
    queryset = Company.objects.select_related('default_billing_address')
    company = get_object_or_404(queryset, pk=pk)
    company_orders = Order.objects.filter(user__company=company)
    company_users = User.objects.filter(company=company)
    ctx = {'company': company, 'company_users': company_users,
           'company_orders': company_orders}
    return TemplateResponse(request, 'dashboard/company/detail.html', ctx)


@staff_member_required
@permission_required('account.manage_companies')
def company_create(request):
    company = Company()
    form = CompanyForm(request.POST or None, instance=company)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added company %s' % company)
        messages.success(request, msg)
        return redirect('dashboard:company-details', pk=company.pk)
    ctx = {'form': form, 'company': company}
    return TemplateResponse(request, 'dashboard/company/form.html', ctx)


@staff_member_required
@permission_required('account.manage_companies')
def company_edit(request, pk=None):
    company = get_object_or_404(Company, pk=pk)
    form = CompanyForm(request.POST or None, instance=company)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated company %s' % company)
        messages.success(request, msg)
        return redirect('dashboard:company-details', pk=company.pk)
    ctx = {'form': form, 'company': company}
    return TemplateResponse(request, 'dashboard/company/form.html', ctx)


@staff_member_required
@permission_required('account.manage_companies')
def ajax_companies_list(request):
    queryset = Company.objects.select_related('default_billing_address')
    search_query = request.GET.get('q', '')
    if search_query:
        queryset = queryset.filter(
            Q(default_billing_address__name__icontains=search_query))

    companies = [
        {'id': company.pk, 'text': company.get_ajax_label()}
        for company in queryset]
    return JsonResponse({'results': companies})


@staff_member_required
@permission_required('account.manage_companies')
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    form = CompanyDeleteForm(
        request.POST or None, instance=company, user=request.user)
    status = 200
    num_users = company.user_set.count()

    if num_users == 0:
        pass
    elif request.method == 'POST' and form.is_valid():
        company.delete()
        msg = pgettext_lazy(
            'Dashboard message',
            '%(company_name)s successfully removed') % {
                'company_name': company}
        messages.success(request, msg)
        return redirect('dashboard:companies')
    elif request.method == 'POST' and not form.is_valid():
        status = 400
    ctx = {'company': company, 'form': form, 'allow_delete': num_users == 0}
    return TemplateResponse(
        request, 'dashboard/company/modal/confirm_delete.html', ctx,
        status=status)
