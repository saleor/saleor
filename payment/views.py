from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.utils.http import urlencode
from order.models import Order
from payment import authorizenet
from payment.forms import PaymentForm, PaymentMethodsForm
from payments import factory, RedirectNeeded, PaymentItem, get_payment_model

Payment = get_payment_model()


def authorizenet_payment(request, token):
    order = get_object_or_404(Order, token=token)
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        order.payment_status = 'complete'
        order.save()
        messages.success(request, 'Your order was successfully processed')
        authorizenet(order, form.cleaned_data)
        return redirect('home')
    return TemplateResponse(request, 'payment/authorizenet.html',
                            {'form': form})


def index(request, token):
    order = get_object_or_404(Order, token=token)
    form = PaymentMethodsForm(request.POST or None)
    if form.is_valid():
        payment_method = form.cleaned_data['method']
        return redirect('order:payment:details', token=token,
                        variant=payment_method)
    return TemplateResponse(request, 'payment/index.html',
                            {'form': form, 'payments': order.payments.all()})


def get_payment_items_from_order(order):
    items = [PaymentItem(name=item.product_name, quantity=item.quantity,
                          price=item.unit_price_gross, sku=item.product.id,
                          currency=settings.SATCHLESS_DEFAULT_CURRENCY)
             for item in order.get_items()]
    return items


def get_or_create_payment_from_order(variant, order):
    total = order.get_total()
    cancel_url = reverse('order:payment:index', kwargs={'token': order.token})
    success_url = reverse('order:success', kwargs={'token': order.token})
    defaults = {'variant': variant, 'total': total.gross, 'tax': Decimal(0),
                'delivery': order.get_delivery_total().gross,
                'currency': total.currency,
                'cancel_url': cancel_url,
                'success_url': success_url}
    return order.payments.get_or_create(variant=variant, defaults=defaults)


def details(request, token, variant):
    order = get_object_or_404(Order, token=token)
    items = get_payment_items_from_order(order)
    payment, _created = get_or_create_payment_from_order(variant, order)
    try:
        provider = factory(payment, variant, items)
    except ValueError as e:
        raise Http404(e)
    try:
        form = provider.get_form(request.POST or None)
    except RedirectNeeded as redirect_to:
        return redirect(str(redirect_to))
    if form.is_valid():
        order.status = 'completed'
        order.save()
        return redirect(form.cleaned_data['next'])
    return TemplateResponse(request, 'payment/%s.html' % variant,
                            {'form': form, 'payment': payment,
                             'provider': provider})
