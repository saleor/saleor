import logging
import os
import requests

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import pgettext_lazy
from django.views.decorators.csrf import csrf_exempt

from ..account.forms import LoginForm
from ..account.models import User
from ..core.utils import get_client_ip
from ..payment import ChargeStatus, TransactionKind, get_payment_gateway
from ..payment.utils import (
    create_payment, create_payment_information, gateway_process_payment)
from . import FulfillmentStatus
from .forms import (
    CustomerNoteForm, PasswordForm, PaymentDeleteForm, PaymentsForm)
from .models import Order
from saleor.payment.models import Payment
from .utils import attach_order_to_user, check_order_status

# Paystack Payment
from python_paystack.paystack_config import PaystackConfig
from python_paystack.objects.transactions import Transaction
from python_paystack.managers import TransactionsManager

PaystackConfig.SECRET_KEY  = os.environ.get('PAYSTACK_SECRET_KEY', '')
PaystackConfig.PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
transactionManager = TransactionsManager()

# Ravepay
RAVEPAY_PUBLIC_KEY = os.environ.get('RAVE_PUBLIC_KEY', '')
RAVEPAY_SECRET_KEY = os.environ.get('RAVE_SECRET_KEY', '')

logger = logging.getLogger(__name__)

PAYMENT_TEMPLATE = 'order/payment/%s.html'


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
    fulfillments = order.fulfillments.exclude(
        status=FulfillmentStatus.CANCELED)
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
    # This is for all payments related to an order
    payments = order.payments.all()
    form_data = request.POST or None

    # This is for payments that hasn't been charged
    waiting_payment = payments.filter(
        is_active=True,
        charge_status=ChargeStatus.NOT_CHARGED,
        transactions__kind=TransactionKind.AUTH).first()
    if not waiting_payment:
        waiting_payment_form = None
    else:
        form_data = None
        waiting_payment_form = PaymentDeleteForm(
            None, order=order, initial={'payment_id': waiting_payment.id})
    if order.is_fully_paid() or not order.billing_address:
        form_data = None
    payment_form = None

    # Set PayStack Payment to be Successful
    # Payment.objects.create(gateway='paystack', order_id=order.id, charge_status='fully-charged')
    # Set Order to be fully paid
    
    if not order.is_pre_authorized():
        payment_form = PaymentsForm(form_data)
        # FIXME: redirect if there is only one payment
        if payment_form.is_valid():
            payment = payment_form.cleaned_data['gateway']
            return redirect(
                'order:payment', token=order.token, gateway=payment)
    ctx = {
        'order': order, 'payment_form': payment_form, 'payments': payments,
        'waiting_payment': waiting_payment,
        'waiting_payment_form': waiting_payment_form,
        'success_url': '/order/' + token + '/payment-success/' }
    return TemplateResponse(request, 'order/payment.html', ctx)


@check_order_status
def start_payment(request, order, gateway):
    payment_gateway, connection_params = get_payment_gateway(gateway)
    extra_data = {'customer_user_agent': request.META.get('HTTP_USER_AGENT')}
    with transaction.atomic():
        payment = create_payment(
            gateway=gateway,
            currency=order.total.gross.currency,
            email=order.user_email,
            billing_address=order.billing_address,
            customer_ip_address=get_client_ip(request),
            total=order.total.gross.amount,
            order=order,
            extra_data=extra_data)

        if (order.is_fully_paid()
                or payment.charge_status == ChargeStatus.FULLY_REFUNDED):
            return redirect(order.get_absolute_url())

        payment_info = create_payment_information(payment)

        if (gateway=='paystack'):
            transactionz = Transaction(order.total.gross.amount*100, order.user_email)
            c_url = 'http://' + request.META['HTTP_HOST'] + '/order/' + order.token + '/payment-confirm/'
            currentTransaction = transactionManager.initialize_transaction('STANDARD', transactionz, c_url)
            return redirect(currentTransaction.authorization_url)
        
        if (gateway=='ravepay'):
            print(str(RAVEPAY_PUBLIC_KEY))
            c_url = 'http://' + request.META['HTTP_HOST'] + '/order/' + order.token + '/payment-confirm/'
            return TemplateResponse(request, 'order/ravepay.html', {'RPK': str(RAVEPAY_PUBLIC_KEY), 'AMT': order.total.gross.amount,
                                                    'EMAIL': order.user_email, 'PHN': order.billing_address.phone, 'TOKEN': order.token})
            # return redirect('order:payment', token=order.token)
            # c_url = 'http://' + request.META['HTTP_HOST'] + '/order/' + order.token + '/payment-confirm/'
            # url = "https://api.ravepay.co/flwv3-pug/getpaidx/api/v2/hosted/pay"
            # querystring = {"PBFPubKey": RAVE_PUBLIC_KEY,"txref": order.token,
            #                 "customer_phone": order.billing_address.phone,"customer_email": order.user_email,
            #                 "amount": order.total.gross.amount, "redirect_url": c_url}
            # response = requests.request("POST", url, params=querystring)
            # return redirect(response.text.data.link)

    client_token = payment_gateway.get_client_token(
        connection_params=connection_params)
    ctx = {
        'form': form,
        'payment': payment,
        'client_token': client_token,
        'order': order}
    return TemplateResponse(request, payment_gateway.TEMPLATE_PATH, ctx)


@check_order_status
def cancel_payment(request, order):
    form = PaymentDeleteForm(request.POST or None, order=order)
    if form.is_valid():
        with transaction.atomic():
            form.save()
        return redirect('order:payment', token=order.token)
    return HttpResponseForbidden()


@csrf_exempt
def payment_confirm(request, token):
    """Receive request from payment gateway after paying for an order.

    Verifies the user payment! Still for PayStack!

    Else goto payment page
    """
    ref = str(request.GET.get('reference', ''))
    if (transactionManager.verify_transaction(ref).status == 'success'):
        order = Order.objects.get(token=token)
        payment = order.get_last_payment()
        payment.charge_status = ChargeStatus.FULLY_CHARGED
        payment.captured_amount = order.total.gross.amount
        payment.save(update_fields=['captured_amount', 'charge_status'])
        url = reverse('order:checkout-success', kwargs={'token': token})
        return redirect(url)
    else:
        
        return redirect('order:payment', token=order.token)


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
