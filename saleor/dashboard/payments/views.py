import json
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.generic import ListView
from payments.models import PAYMENT_STATUS_CHOICES
from prices import Price

from ..views import FilterByStatusMixin
from ...order.models import Payment


class PaymentList(FilterByStatusMixin, ListView):
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


def payment_details(request, pk):
    payment = get_object_or_404(Payment.objects.all(), pk=pk)
    currency = payment.currency
    payment.total = Price(payment.total, currency=currency)
    payment.captured_amount = Price(payment.captured_amount, currency=currency)
    ctx = {'payment': payment}
    if payment.extra_data:
        payment.extra_data = json.dumps(json.loads(payment.extra_data),
                                        indent=2)
    return TemplateResponse(request, 'dashboard/payments/detail.html', ctx)
