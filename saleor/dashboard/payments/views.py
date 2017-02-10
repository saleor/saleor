from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from ...core.utils import get_paginator_items
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

    page = get_paginator_items(payments, 30, request.GET.get('page'))

    form = PaymentFilterForm(request.POST or None,
                             initial={'status': active_status or None})

    ctx = {'payments': page.object_list, 'page_obj': page,
           'is_paginated': page.has_other_pages(), 'form': form}
    return TemplateResponse(request, 'dashboard/payments/list.html', ctx)


@staff_member_required
def payment_details(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return TemplateResponse(request, 'dashboard/payments/detail.html',
                            {'payment': payment})
