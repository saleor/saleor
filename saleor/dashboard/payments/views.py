from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect
from payments import PaymentError
from payments.models import PAYMENT_STATUS_CHOICES

from ..views import FilterByStatusMixin
from ...order.models import Payment
from .forms import CaptureForm


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
    form_class = CaptureForm

    def get_context_data(self, **kwargs):
        ctx = super(PaymentDetails, self).get_context_data(**kwargs)
        ctx['capture_form'] = self.get_capture_form()
        ctx['refund_available'] = self.object.status == 'confirmed'
        ctx['release_available'] = self.object.status == 'preauth'
        return ctx

    def get_capture_form(self):
        if self.object.status == 'preauth':
            return self.form_class(initial={'amount': self.object.total})
        else:
            return None

    def post(self, *args, **kwargs):
        form = self.form_class(self.request.POST)
        payment = self.get_object()
        error_msg = None

        if form.is_valid():
            try:
                payment.capture(amount=form.cleaned_data['amount'])
            except PaymentError as e:
                error_msg = _('Payment gateway error: ') + e.message
            else:
                messages.success(self.request, _('Funds captured'))

        if 'refund' in self.request.POST and payment.status == 'confirmed':
            try:
                payment.refund(amount=payment.captured_amount)
            except PaymentError as e:
                error_msg = _('Payment gateway error: ') + e.message
            else:
                messages.success(self.request, _('Refund successful'))

        if 'release' in self.request.POST and payment.status == 'preauth':
            try:
                payment.release()
            except PaymentError as e:
                error_msg = _('Payment gateway error: ') + e.message
            else:
                messages.success(self.request, _('Release successful'))

        if error_msg:
            messages.error(self.request, error_msg)
        return redirect('dashboard:payment-details', pk=payment.pk)
