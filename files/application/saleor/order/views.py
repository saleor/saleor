import logging

from django.conf import settings
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from payments import PaymentStatus, RedirectNeeded

from .forms import PaymentDeleteForm, PaymentMethodsForm, PasswordForm
from .models import Order, Payment
from .utils import check_order_status, attach_order_to_user
from ..core.utils import get_client_ip
from ..registration.forms import LoginForm
from ..userprofile.models import User
from . import OrderStatus

logger = logging.getLogger(__name__)


def details(request, token):
    orders = Order.objects.prefetch_related('groups__items',
                                            'groups__items__product')
    orders = orders.select_related('billing_address', 'shipping_address',
                                   'user')
    order = get_object_or_404(orders, token=token)
    groups = order.groups.all()
    return TemplateResponse(request, 'order/details.html',
                            {'order': order, 'groups': groups})


def payment(request, token):
    orders = Order.objects.prefetch_related('groups__items__product')
    orders = orders.select_related('billing_address', 'shipping_address',
                                   'user')
    order = get_object_or_404(orders, token=token)
    groups = order.groups.all()
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
    waiting_payments = order.payments.filter(status=PaymentStatus.WAITING).exists()
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
                'billing_country_code': billing.country.code,
                'billing_email': order.user_email,
                'description': pgettext_lazy(
                    'Payment description', 'Order %(order_number)s') % {
                        'order_number': order},
                'billing_country_area': billing.country_area,
                'customer_ip_address': get_client_ip(request)}
    variant_choices = settings.CHECKOUT_PAYMENT_CHOICES
    if variant not in [code for code, dummy_name in variant_choices]:
        raise Http404('%r is not a valid payment variant' % (variant,))
    with transaction.atomic():
        order.change_status(OrderStatus.PAYMENT_PENDING)
        payment, dummy_created = Payment.objects.get_or_create(
            variant=variant, status=PaymentStatus.WAITING, order=order,
            defaults=defaults)
        try:
            form = payment.get_form(data=request.POST or None)
        except RedirectNeeded as redirect_to:
            return redirect(str(redirect_to))
        except Exception:
            logger.exception('Error communicating with the payment gateway')
            messages.error(
                request,
                pgettext_lazy(
                    'Payment gateway error',
                    'Oops, it looks like we were unable to contact the selected'
                    ' payment service'))
            payment.change_status(PaymentStatus.ERROR)
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


def create_password(request, token):
    if request.user.is_authenticated():
        return redirect('order:details', token=token)
    order = get_object_or_404(Order, token=token)
    email = order.user_email
    form_data = request.POST.copy()
    if form_data:
        form_data.update({'email': email})
    register_form = PasswordForm(form_data or None)
    if User.objects.filter(email=email).exists():
        login_form = LoginForm(initial={'login': email})
    else:
        login_form = None
    if register_form.is_valid():
        register_form.save()
        password = register_form.cleaned_data.get('password')
        user = auth.authenticate(email=email, password=password)
        auth.login(request, user)
        attach_order_to_user(order, user)
        return redirect('order:details', token=token)
    ctx = {'form': register_form, 'email': email, 'order': order,
           'login_form': login_form}
    return TemplateResponse(request, 'order/create_password.html', ctx)


@login_required
def connect_order_with_user(request, token):
    order = get_object_or_404(
        Order.objects.filter(user_email=request.user.email, token=token))
    attach_order_to_user(order, request.user)
    messages.success(
        request, pgettext_lazy(
            'storefront message',
            'You\'ve successfully connected order with your account'))
    return redirect('order:details', token=order.token)
