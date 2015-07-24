from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from .forms import ReplaceCartLineFormSet
from . import Cart
from ..cart.utils import has_available_products, remove_unavailable_products


def index(request):
    cart = Cart.for_session_cart(request.cart, discounts=request.discounts)
    cart_partitioner = cart.partition()
    if not has_available_products(cart):
        msg = _('Sorry. We don\'t have that many items in stock. '
                'Quantity was set to maximum available for now.')
        messages.warning(request, msg)
        cart = remove_unavailable_products(cart)
    formset = ReplaceCartLineFormSet(request.POST or None,
                                     cart=cart)
    if formset.is_valid():
        msg = _('Successfully updated product quantities.')
        messages.success(request, msg)
        formset.save()
        return redirect('cart:index')
    return TemplateResponse(
        request, 'cart/index.html', {
            'cart': cart_partitioner,
            'formset': formset})
