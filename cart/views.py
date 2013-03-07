from . import get_cart_from_request
from .forms import ReplaceCartLineFormSet
from cart import Partitioner
from django.shortcuts import redirect
from django.template.response import TemplateResponse


def index(request):
    cart = get_cart_from_request(request)
    partitioner = Partitioner(cart)
    formset = ReplaceCartLineFormSet(request.POST or None, cart=cart)
    if formset.is_valid():
        formset.save()
        return redirect('cart:index')
    return TemplateResponse(
        request, 'cart/index.html', {
            'cart': partitioner,
            'formset': formset})
