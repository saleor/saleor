from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from satchless.item import Partitioner

from . import Cart
from .forms import ReplaceCartLineFormSet
from .utils import cart_is_ready_to_checkout


def index(request):
    cart = Cart.for_session_cart(request.cart)
    cart_partitioner = Partitioner(cart)
    formset = ReplaceCartLineFormSet(request.POST or None, cart=cart)

    # Cart check
    checkout_possible = cart_is_ready_to_checkout(cart)

    if formset.is_valid():
        msg = _('Successfully updated product quantities.')
        messages.success(request, msg)
        formset.save()
        return redirect('cart:index')

    return TemplateResponse(
        request, 'cart/index.html', {
            'cart': cart_partitioner,
            'formset': formset,
            'checkout_possible': checkout_possible})
