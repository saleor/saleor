from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.http.response import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from order.models import Order
from payment import authorizenet
from payment.forms import PaymentForm, PaymentMethodsForm
from payments import factory, RedirectNeeded, PaymentItem
from payments.models import Payment


def exists_order_or_404(*args, **kwargs):

    if not Order.objects.filter(*args, **kwargs).exists():
        raise Http404('Order does not exist')


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
    exists_order_or_404(token=token)
    form = PaymentMethodsForm(request.POST or None)
    if form.is_valid():
        payment_method = form.cleaned_data['method']
        return redirect('order:payment:details', token=token,
                        variant=payment_method)
    return TemplateResponse(request, 'payment/index.html', {'form': form})


def details(request, token, variant):
    order = get_object_or_404(Order, token=token)
    items = [PaymentItem(name=item.product_name, quantity=item.quantity,
                          price=item.unit_price_gross, sku=item.product.id,
                          currency=settings.SATCHLESS_DEFAULT_CURRENCY)
             for item in order.get_items()]
    try:
        provider = factory(variant, items)
    except ValueError as e:
        raise Http404(e)
    try:
        payment = order.payments.get(variant=variant)
    except Payment.DoesNotExist:
        total = order.get_total()
        delivery = order.get_delivery_total().gross
        payment = order.payments.create(variant=variant, total=total.gross,
                                        currency=total.currency,
                                        delivery=delivery, tax=Decimal(0))
        try:
            form = provider.get_form(payment)
        except RedirectNeeded as redirect_to:
            return redirect(str(redirect_to))
        return TemplateResponse(request, 'payment/details.html',
                                {'form': form, 'payment': payment,
                                 'provider': provider})
    else:
        return TemplateResponse(request, 'payment/details.html',
                                {'payment': payment})
