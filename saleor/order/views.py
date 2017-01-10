import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
from payments import RedirectNeeded

from .forms import PaymentDeleteForm, PaymentMethodsForm
from .models import Order, Payment
from ..core.utils import get_client_ip
from .utils import check_order_status

logger = logging.getLogger(__name__)


def details(request, token):
    orders = Order.objects.prefetch_related('groups__items')
    order = get_object_or_404(orders, token=token)
    groups = order.groups.all()
    return TemplateResponse(request, 'order/details.html',
                            {'order': order, 'groups': groups})


def payment(request, token):
    orders = Order.objects.prefetch_related('groups__items')
    order = get_object_or_404(orders, token=token)
    groups = order.groups.all()
    payments = order.payments.all()
    form_data = request.POST or None
    try:
        waiting_payment = order.payments.get(status='waiting')
    except Payment.DoesNotExist:
        waiting_payment = None
        waiting_payment_form = None
    else:
        form_data = None
        waiting_payment_form = PaymentDeleteForm(
            None, order=order, initial={'payment_id': waiting_payment.id})
    if order.is_fully_paid():
        form_data = None
    payment_form = None
    if not order.is_pre_authorized():
        payment_form = PaymentMethodsForm(form_data)
        # FIXME: redirect if there is only one payment method
        if payment_form.is_valid():
            payment_method = payment_form.cleaned_data['method']
            return redirect('order:payment', token=order.token,
                            variant=payment_method)
    return TemplateResponse(request, 'order/payment.html',
                            {'order': order, 'groups': groups,
                             'payment_form': payment_form,
                             'waiting_payment': waiting_payment,
                             'waiting_payment_form': waiting_payment_form,
                             'payments': payments})


@check_order_status
def start_payment(request, order, variant):
    waiting_payments = order.payments.filter(status='waiting').exists()
    if waiting_payments:
        return redirect('order:payment', token=order.token)
    billing = order.billing_address
    total = order.get_total()
    defaults = {'total': total.gross,
                'tax': total.tax, 'currency': total.currency,
                'delivery': order.get_delivery_total().gross,
                'billing_first_name': billing.first_name,
                'billing_last_name': billing.last_name,
                'billing_address_1': billing.street_address_1,
                'billing_address_2': billing.street_address_2,
                'billing_city': billing.city,
                'billing_postcode': billing.postal_code,
                'billing_country_code': billing.country,
                'billing_email': order.user_email,
                'description': _('Order %(order_number)s') % {
                    'order_number': order},
                'billing_country_area': billing.country_area,
                'customer_ip_address': get_client_ip(request)}
    variant_choices = settings.CHECKOUT_PAYMENT_CHOICES
    if variant not in [code for code, dummy_name in variant_choices]:
        raise Http404('%r is not a valid payment variant' % (variant,))
    with transaction.atomic():
        order.change_status('payment-pending')
        payment, dummy_created = Payment.objects.get_or_create(
            variant=variant, status='waiting', order=order, defaults=defaults)
        try:
            form = payment.get_form(data=request.POST or None)
        except RedirectNeeded as redirect_to:
            return redirect(str(redirect_to))
        except Exception:
            logger.exception('Error communicating with the payment gateway')
            messages.error(
                request,
                _('Oops, it looks like we were unable to contact the selected'
                  ' payment service'))
            payment.change_status('error')
            return redirect('order:payment', token=order.token)
    template = 'order/payment/%s.html' % variant
    return TemplateResponse(request, [template, 'order/payment/default.html'],
                            {'form': form, 'payment': payment})


@check_order_status
def cancel_payment(request, order):
    form = PaymentDeleteForm(request.POST or None, order=order)
    if form.is_valid():
        with transaction.atomic():
            form.save()
        return redirect('order:payment', token=order.token)
    return HttpResponseForbidden()
