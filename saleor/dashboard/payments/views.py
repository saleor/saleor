import json
from django.views.generic import ListView, DetailView
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


class PaymentDetails(DetailView):
    model = Payment
    template_name = 'dashboard/payments/detail.html'
    context_object_name = 'payment'

    def get_object(self, queryset=None):
        obj = super(PaymentDetails, self).get_object(queryset)
        currency = obj.currency
        obj.total = Price(obj.total, currency=currency)
        obj.captured_amount = Price(obj.captured_amount, currency=currency)
        return obj

    def get_context_data(self, **kwargs):
        ctx = super(PaymentDetails, self).get_context_data(**kwargs)
        extra_data = self.get_object().extra_data
        if extra_data:
            extra_data = json.dumps(
                json.loads(self.get_object().extra_data), indent=2)
        ctx['extra_data'] = extra_data
        return ctx
