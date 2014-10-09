import json
from django.views.generic import ListView, DetailView
from payments.models import PAYMENT_STATUS_CHOICES

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

    def get_queryset(self):
        qs = super(PaymentList, self).get_queryset()
        return qs.order_by('-created')


class PaymentDetails(DetailView):
    model = Payment
    template_name = 'dashboard/payments/detail.html'
    context_object_name = 'payment'

    def get_context_data(self, **kwargs):
        ctx = super(PaymentDetails, self).get_context_data(**kwargs)
        extra_data = self.get_object().extra_data
        if extra_data:
            extra_data = json.dumps(
                json.loads(self.get_object().extra_data), indent=2)
        ctx['extra_data'] = extra_data
        return ctx
