from . import get_cart_from_request
from .forms import ReplaceCartLineFormSet
from cart import cart_partition
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from prices import Price
from django.conf import settings

def index(request):
    cart = get_cart_from_request(request)
    cart_deliveries = cart_partition(cart)
    cart_delivery_prices = [delivery.get_min_delivery_method().get_price()
                            for delivery in cart_deliveries]
    zero = Price(0, currency=settings.SATCHLESS_DEFAULT_CURRENCY)

    formset = ReplaceCartLineFormSet(request.POST or None, cart=cart)

    if formset.is_valid():
        formset.save()
        return redirect('cart:index')

    return TemplateResponse(request, 'cart/index.html', {
        'cart': cart,
        'formset': formset,
        'shipping': sum(cart_delivery_prices, zero)
    })
