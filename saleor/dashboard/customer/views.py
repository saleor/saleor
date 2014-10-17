from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from .forms import CustomerSearchForm
from ..views import staff_member_required
from ...userprofile.models import User


def _search_customers(queryset, data):
    if data['email']:
        queryset = queryset.filter(email__icontains=data['email'])
    if data['name']:
        parts = data['name'].split()
        if len(parts) == 2:
            query = (Q(addresses__first_name__icontains=parts[0])
                     | Q(addresses__last_name__icontains=parts[1])) \
                | (Q(addresses__first_name__icontains=parts[1])
                    | Q(addresses__last_name__icontains=parts[0]))
        else:
            query = Q(addresses__first_name__icontains=data['name']) \
                | Q(addresses__last_name__istartswith=data['name'])
        queryset = queryset.filter(query).distinct()
    return queryset


def _get_users_with_open_orders(queryset):
    open_order = ['new', 'payment-pending', 'fully-paid']
    return queryset.filter(orders__status__in=open_order)


@staff_member_required
def customer_list(request):
    customers = User.objects.prefetch_related('orders', 'addresses').annotate(
        num_orders=Count('orders', distinct=True),
        last_order=Max('orders', distinct=True))
    form = CustomerSearchForm(request.POST or request.GET or None)
    if form.is_valid():
        customers = _search_customers(customers, form.cleaned_data)
        title = _('Search results')
    else:
        customers = _get_users_with_open_orders(customers)
        title = _('Customers with open orders')
    ctx = {'customers': customers, 'form': form, 'title': title}
    return TemplateResponse(request, 'dashboard/customer/list.html', ctx)


@staff_member_required
def customer_details(request, pk):
    qs = User.objects.prefetch_related('orders', 'addresses').select_related(
        'default_billing_address')
    customer = get_object_or_404(qs, pk=pk)
    ctx = {'customer': customer}
    return TemplateResponse(request, 'dashboard/customer/detail.html', ctx)
