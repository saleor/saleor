from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from ..views import staff_member_required
from ...order.models import Payment
from ..order.forms import PaymentFilterForm


@staff_member_required
def payment_list(request):
    payments = Payment.objects.select_related('order').all().order_by(
        '-created')

    active_status = request.GET.get('status')
    if active_status:
        payments = payments.filter(status=active_status)

    paginator = Paginator(payments, 30)
    page_number = request.GET.get('page')
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    form = PaymentFilterForm(request.GET or None)

    ctx = {'payments': page.object_list, 'paginator': paginator,
           'page_obj': page, 'is_paginated': page.has_other_pages(),
           'form': form}
    return TemplateResponse(request, 'dashboard/payments/list.html', ctx)


@staff_member_required
def payment_details(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return TemplateResponse(request, 'dashboard/payments/detail.html',
                            {'payment': payment})
