from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from order.models import Order
from payment import authorizenet
from payment.forms import PaymentForm


def payment(request, token):
    order = get_object_or_404(Order, token=token)
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        order.payment_status = 'complete'
        order.save()
        messages.success(request, 'Your order was successfully processed')
        authorizenet(order, form.cleaned_data)
        return redirect('home')
    return TemplateResponse(request, 'order/payment.html', {'form': form})
