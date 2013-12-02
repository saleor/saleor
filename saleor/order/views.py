from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from payments import RedirectNeeded

from . import check_order_status
from .forms import PaymentDeleteForm, PaymentMethodsForm
from .models import Order, Payment


def success(request, token):
    order = get_object_or_404(Order, token=token)
    if order.status == 'fully-paid':
        return TemplateResponse(request, 'order/success.html',
                                {'order': order})
    return redirect('order:payment:index', token=order.token)


def details(request, token):
    order = get_object_or_404(Order, token=token)
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
    payment_form = PaymentMethodsForm(form_data)
    if payment_form.is_valid():
        payment_method = payment_form.cleaned_data['method']
        return redirect('order:payment', token=order.token,
                        variant=payment_method)
    return TemplateResponse(request, 'order/details.html',
                            {'order': order, 'groups': groups,
                             'payment_form': payment_form,
                             'waiting_payment': waiting_payment,
                             'waiting_payment_form': waiting_payment_form,
                             'payments': payments})


@check_order_status
def start_payment(request, order, variant):
    waiting_payments = order.payments.filter(status='waiting').exists()
    if waiting_payments:
        return redirect('order:details', token=order.token)
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
                'billing_country_area': billing.country_area}
    with transaction.atomic():
        order.change_status('payment-pending')
        payment, _created = Payment.objects.get_or_create(variant=variant,
                                                          status='waiting',
                                                          order=order,
                                                          defaults=defaults)
        try:
            form = payment.get_form(data=request.POST or None)
        except ValueError as e:
            raise Http404(e)
        except RedirectNeeded as redirect_to:
            return redirect(str(redirect_to))
    template = 'order/payment/%s.html' % variant
    return TemplateResponse(request, [template, 'order/payment/default.html'],
                            {'form': form, 'payment': payment})


@check_order_status
def cancel_payment(request, order):
    form = PaymentDeleteForm(request.POST or None, order=order)
    if form.is_valid():
        with transaction.atomic():
            form.save()
        return redirect('order:details', token=order.token)
    return HttpResponseForbidden()
