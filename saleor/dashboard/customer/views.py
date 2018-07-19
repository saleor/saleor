from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.context_processors import csrf
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...account.models import CustomerNote, User
from ...core.utils import get_paginator_items
from ..emails import send_set_password_email
from ..views import staff_member_required
from .filters import UserFilter
from .forms import CustomerDeleteForm, CustomerForm, CustomerNoteForm


@staff_member_required
@permission_required('account.manage_users')
def customer_list(request):
    customers = (
        User.objects
        .filter(
            Q(is_staff=False) | (Q(is_staff=True) & Q(orders__isnull=False)))
        .distinct()
        .prefetch_related('orders', 'addresses')
        .select_related('default_billing_address', 'default_shipping_address')
        .order_by('email'))
    customer_filter = UserFilter(request.GET, queryset=customers)
    customers = get_paginator_items(
        customer_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'customers': customers, 'filter_set': customer_filter,
        'is_empty': not customer_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/customer/list.html', ctx)


@staff_member_required
@permission_required('account.manage_users')
def customer_details(request, pk):
    queryset = User.objects.prefetch_related(
        'orders', 'addresses', 'notes').select_related(
            'default_billing_address', 'default_shipping_address')
    customer = get_object_or_404(queryset, pk=pk)
    customer_orders = customer.orders.all()
    notes = customer.notes.all()
    ctx = {
        'customer': customer, 'customer_orders': customer_orders,
        'notes': notes}
    return TemplateResponse(request, 'dashboard/customer/detail.html', ctx)


@staff_member_required
@permission_required('account.manage_users')
def customer_create(request):
    customer = User()
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added customer %s') % customer
        send_set_password_email(customer)
        messages.success(request, msg)
        return redirect('dashboard:customer-details', pk=customer.pk)
    ctx = {'form': form, 'customer': customer}
    return TemplateResponse(request, 'dashboard/customer/form.html', ctx)


@staff_member_required
@permission_required('account.manage_users')
def customer_edit(request, pk=None):
    customer = get_object_or_404(User, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated customer %s') % customer
        messages.success(request, msg)
        return redirect('dashboard:customer-details', pk=customer.pk)
    ctx = {'form': form, 'customer': customer}
    return TemplateResponse(request, 'dashboard/customer/form.html', ctx)


@staff_member_required
@permission_required('account.manage_users')
def ajax_users_list(request):
    queryset = User.objects.select_related('default_billing_address')
    search_query = request.GET.get('q', '')
    if search_query:
        queryset = queryset.filter(
            Q(default_billing_address__first_name__icontains=search_query) |
            Q(default_billing_address__last_name__icontains=search_query) |
            Q(email__icontains=search_query))

    users = [
        {'id': user.pk, 'text': user.get_ajax_label()} for user in queryset]
    return JsonResponse({'results': users})


@staff_member_required
@permission_required('account.manage_users')
def customer_add_note(request, customer_pk):
    customer = get_object_or_404(User, pk=customer_pk)
    note = CustomerNote(customer=customer, user=request.user)
    form = CustomerNoteForm(request.POST or None, instance=note)
    status = 200
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message related to an customer', 'Added note')
        messages.success(request, msg)
    elif form.errors:
        status = 400
    ctx = {'customer': customer, 'form': form}
    ctx.update(csrf(request))
    template = 'dashboard/customer/modal/add_note.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('account.manage_users')
def customer_delete(request, pk):
    customer = get_object_or_404(User, pk=pk)
    form = CustomerDeleteForm(
        request.POST or None, instance=customer, user=request.user)
    status = 200
    if request.method == 'POST' and form.is_valid():
        customer.delete()
        msg = pgettext_lazy(
            'Dashboard message',
            '%(customer_name)s successfully removed') % {
                'customer_name': customer}
        messages.success(request, msg)
        return redirect('dashboard:customers')
    elif request.method == 'POST' and not form.is_valid():
        status = 400
    ctx = {'customer': customer, 'form': form}
    return TemplateResponse(
        request, 'dashboard/customer/modal/confirm_delete.html', ctx,
        status=status)
