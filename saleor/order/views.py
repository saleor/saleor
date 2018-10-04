import logging

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import pgettext_lazy
from django.views.decorators.csrf import csrf_exempt
from payments import PaymentStatus

from . import FulfillmentStatus
from ..account.forms import LoginForm
from ..account.models import User
from ..core.utils import get_client_ip
from ..payment.forms import PaymentMethodForm
from ..payment.models import PaymentMethod
from .forms import (
    CustomerNoteForm, PasswordForm, PaymentDeleteForm, PaymentMethodsForm)
from .models import Order, Payment
from .utils import attach_order_to_user, check_order_status

logger = logging.getLogger(__name__)


def details(request, token):
    note_form = None
    orders = Order.objects.confirmed().prefetch_related(
        'lines__variant__images', 'lines__variant__product__images',
        'fulfillments__lines__order_line')
    orders = orders.select_related(
        'billing_address', 'shipping_address', 'user')
    order = get_object_or_404(orders, token=token)
    if order.is_open() and not order.customer_note:
        note_form = CustomerNoteForm(request.POST or None, instance=order)
        if request.method == 'POST':
            if note_form.is_valid():
                note_form.save()
                return redirect('order:details', token=order.token)
    fulfillments = order.fulfillments.filter(
        status=FulfillmentStatus.FULFILLED)
    ctx = {
        'order': order, 'fulfillments': fulfillments, 'note_form': note_form}
    return TemplateResponse(request, 'order/details.html', ctx)


def payment(request, token):
    orders = Order.objects.confirmed().filter(billing_address__isnull=False)
    orders = orders.prefetch_related(
        'lines__variant__images', 'lines__variant__product__images')
    orders = orders.select_related(
        'billing_address', 'shipping_address', 'user')
    order = get_object_or_404(orders, token=token)
    payments = order.payments.all()
    form_data = request.POST or None
    try:
        waiting_payment = order.payments.get(status=PaymentStatus.WAITING)
    except Payment.DoesNotExist:
        waiting_payment = None
        waiting_payment_form = None
    else:
        form_data = None
        waiting_payment_form = PaymentDeleteForm(
            None, order=order, initial={'payment_id': waiting_payment.id})
    if order.is_fully_paid() or not order.billing_address:
        form_data = None
    payment_form = None
    if not order.is_pre_authorized():
        payment_form = PaymentMethodsForm(form_data)
        # FIXME: redirect if there is only one payment method
        if payment_form.is_valid():
            payment_method = payment_form.cleaned_data['method']
            return redirect(
                'order:payment', token=order.token, variant=payment_method)
    ctx = {
        'order': order, 'payment_form': payment_form, 'payments': payments,
        'waiting_payment': waiting_payment,
        'waiting_payment_form': waiting_payment_form}
    return TemplateResponse(request, 'order/payment.html', ctx)


@check_order_status
def start_payment(request, order, variant):
    waiting_payments = order.payments.filter(
        status=PaymentStatus.WAITING).exists()
    if waiting_payments:
        return redirect('order:payment', token=order.token)
    billing = order.billing_address
    total = order.total
    defaults = {
        'total': total.gross.amount,
        'tax': total.tax.amount,
        'currency': total.currency,
        'billing_first_name': billing.first_name,
        'billing_last_name': billing.last_name,
        'billing_address_1': billing.street_address_1,
        'billing_address_2': billing.street_address_2,
        'billing_city': billing.city,
        'billing_postcode': billing.postal_code,
        'billing_country_code': billing.country.code,
        'billing_email': order.user_email,
        'billing_country_area': billing.country_area,
        'customer_ip_address': get_client_ip(request)}
    variant_choices = settings.CHECKOUT_PAYMENT_CHOICES
    if variant not in [code for code, dummy_name in variant_choices]:
        raise Http404('%r is not a valid payment variant' % (variant,))
    with transaction.atomic():
        # FIXME: temporary solution, should be adapted to new API
        payment_method, _ = PaymentMethod.objects.get_or_create(
            variant=variant, is_active=True, order=order, defaults=defaults)
        form = PaymentMethodForm(
            data=request.POST or None, instance=payment_method)
        form.method = "POST"
        if form.is_valid():
            form.save()
            form.authorize_payment()
            return redirect(order.get_absolute_url())
    template = 'order/payment/%s.html' % variant
    ctx = {'form': form, 'payment': payment_method}
    return TemplateResponse(
        request, [template, 'order/payment/default.html'], ctx)


@check_order_status
def cancel_payment(request, order):
    form = PaymentDeleteForm(request.POST or None, order=order)
    if form.is_valid():
        with transaction.atomic():
            form.save()
        return redirect('order:payment', token=order.token)
    return HttpResponseForbidden()


@csrf_exempt
def payment_success(request, token):
    """Receive request from payment gateway after paying for an order.

    Redirects user to payment success.
    All post data and query strings are dropped.
    """
    url = reverse('order:checkout-success', kwargs={'token': token})
    return redirect(url)


def checkout_success(request, token):
    """Redirect user after placing an order.

    Anonymous users are redirected to the checkout success page.
    Registered users are redirected to order details page and the order
    is attached to their account.
    """
    order = get_object_or_404(Order, token=token)
    email = order.user_email
    ctx = {'email': email, 'order': order}
    if request.user.is_authenticated:
        return TemplateResponse(request, 'order/checkout_success.html', ctx)
    form_data = request.POST.copy()
    if form_data:
        form_data.update({'email': email})
    register_form = PasswordForm(form_data or None)
    if register_form.is_valid():
        register_form.save()
        password = register_form.cleaned_data.get('password')
        user = auth.authenticate(
            request=request, email=email, password=password)
        auth.login(request, user)
        attach_order_to_user(order, user)
        return redirect('order:details', token=token)
    user_exists = User.objects.filter(email=email).exists()
    login_form = LoginForm(
        initial={'username': email}) if user_exists else None
    ctx.update({'form': register_form, 'login_form': login_form})
    return TemplateResponse(
        request, 'order/checkout_success_anonymous.html', ctx)


@login_required
def connect_order_with_user(request, token):
    """Connect newly created order to an authenticated user."""
    try:
        order = Order.objects.get(user_email=request.user.email, token=token)
    except Order.DoesNotExist:
        order = None
    if not order:
        msg = pgettext_lazy(
            'Connect order with user warning message',
            "We couldn't assign the order to your account as the email"
            " addresses don't match")
        messages.warning(request, msg)
        return redirect('account:details')
    attach_order_to_user(order, request.user)
    msg = pgettext_lazy(
        'storefront message',
        'The order is now assigned to your account')
    messages.success(request, msg)
    return redirect('order:details', token=order.token)
