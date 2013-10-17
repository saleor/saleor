from django.shortcuts import redirect
from django.template.response import TemplateResponse

from . import CartPartitioner
from .forms import ReplaceCartLineFormSet


def index(request):
    partitioner = CartPartitioner(request.cart)
    formset = ReplaceCartLineFormSet(request.POST or None, cart=request.cart)
    if formset.is_valid():
        formset.save()
        return redirect('cart:index')
    return TemplateResponse(
        request, 'cart/index.html', {
            'cart': partitioner,
            'formset': formset})
