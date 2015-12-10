from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.generic import ListView
from payments.models import PAYMENT_STATUS_CHOICES

from ..views import (FilterByStatusMixin, StaffMemberOnlyMixin,
                     staff_member_required)
from ...order.models import Payment
from ..order.forms import PaymentFilterForm


class PaymentList(StaffMemberOnlyMixin, FilterByStatusMixin, ListView):
    model = Payment
    template_name = 'dashboard/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 30
    form_class = PaymentFilterForm
    status_choices = PAYMENT_STATUS_CHOICES
    status_order = ['waiting', 'input', 'preauth', 'confirmed', 'refunded',
                    'rejected', 'error']

    def get_queryset(self):
        qs = super(PaymentList, self).get_queryset()
        return qs.order_by('-created').select_related('order')


@staff_member_required
def payment_details(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return TemplateResponse(request, 'dashboard/payments/detail.html',
                            {'payment': payment})
