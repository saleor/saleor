from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.generic import ListView
from payments.models import PAYMENT_STATUS_CHOICES
from prices import Price

from ..views import (FilterByStatusMixin, StaffMemberOnlyMixin,
                     staff_member_required)
from ...order.models import Payment


class PaymentList(StaffMemberOnlyMixin, FilterByStatusMixin, ListView):
    model = Payment
    template_name = 'dashboard/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 30
    status_choices = PAYMENT_STATUS_CHOICES
    status_order = ['waiting', 'input', 'preauth', 'confirmed', 'refunded',
                    'rejected', 'error']

    def get_context_data(self, **kwargs):
        ctx = super(PaymentList, self).get_context_data(**kwargs)
        for payment in ctx['payments']:
            payment.total = Price(payment.total, currency=payment.currency)
            payment.captured_amount = Price(payment.captured_amount,
                                            currency=payment.currency)
        return ctx

    def get_queryset(self):
        qs = super(PaymentList, self).get_queryset()
        return qs.order_by('-created')


@staff_member_required
def payment_details(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    currency = payment.currency
    payment.total = Price(payment.total, currency=currency)
    payment.captured_amount = Price(payment.captured_amount, currency=currency)
    return TemplateResponse(request, 'dashboard/payments/detail.html',
                            {'payment': payment})
