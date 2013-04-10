from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
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
    order = get_object_or_404(Order, token=token)
    form = PaymentMethodsForm(request.POST or None)
    if form.is_valid():
        payment_method = form.cleaned_data['method']
        return redirect('order:payment:details', token=token,
                        variant=payment_method)
    return TemplateResponse(request, 'payment/index.html',
                            {'form': form, 'payments': order.payments.all()})


def details(request, token, variant):
    order = get_object_or_404(Order, token=token)
    items = [PaymentItem(name=item.product_name, quantity=item.quantity,
                          price=item.unit_price_gross, sku=item.product.id,
                          currency=settings.SATCHLESS_DEFAULT_CURRENCY)
             for item in order.get_items()]
    total = order.get_total()
    url = reverse('order:payment:index', kwargs={'token': token})
    defaults = {'variant': variant, 'total': total.gross, 'tax': Decimal(0),
                'delivery': order.get_delivery_total().gross,
                'currency': total.currency,
                'cancel_url': url,
                'success_url': url}
    payment, _created = order.payments.get_or_create(variant=variant,
                                                     defaults=defaults)
    try:
        provider = factory(payment, variant, items)
    except ValueError as e:
        raise Http404(e)
    try:
        form = provider.get_form(request.POST or None)
    except RedirectNeeded as redirect_to:
        return redirect(str(redirect_to))
    if form.is_valid():
        return redirect(form.cleaned_data['next'])
    return TemplateResponse(request, 'payment/%s.html' % variant,
                            {'form': form, 'payment': payment,
                             'provider': provider})
