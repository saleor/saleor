from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import NoReverseMatch
from django.http.response import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from order.models import Order
from payment import authorizenet
from payment.forms import PaymentForm, PaymentMethodsForm, PaypalForm


def authorizenet_payment(request, token):
    order = get_object_or_404(Order, token=token)
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        order.payment_status = 'complete'
        order.save()
        messages.success(request, 'Your order was successfully processed')
        authorizenet(order, form.cleaned_data)
        return redirect('home')
    return TemplateResponse(request, 'order/authorizenet.html', {'form': form})


@csrf_exempt
def paypal_payment(request, token):
    order = get_object_or_404(Order, token=token)
    #if request.method == 'GET':
    #    redirect()
    address = order.billing_address
    initial = {
        'first_name': address.first_name,
        'last_name': address.last_name,
        'city': address.city,
        'state': address.country_area,
        'zip': address.postal_code,
        'country': address.country,
        'currency_code': order.get_total().currency,
        'amount': order.get_total().gross,
        'email': getattr(settings, 'PAYPAL_EMAIL')
    }
    form = PaypalForm(request.POST or None, initial=initial)
    if form.is_valid():
        order.payment_status = 'complete'
        order.save()
        messages.success(request, 'Your order was successfully processed')
        authorizenet(order, form.cleaned_data)
        return redirect('home')
    return TemplateResponse(request, 'order/paypal.html', {'form': form,
        'action': 'https://www.sandbox.paypal.com/cgi-bin/webscr'})


def index(request, token):
    order = get_object_or_404(Order, token=token)
    form = PaymentMethodsForm(request.POST or None)
    if form.is_valid():
        payment_method = form.cleaned_data['method']
        try:
            return redirect('order:payment:%s' % (payment_method,),
                            token=token)
        except NoReverseMatch:
            raise Http404()
    return TemplateResponse(request, 'order/payment.html',
                            {'form': form, 'order': order})
