from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from satchless.item import Partitioner

from .forms import ReplaceCartLineFormSet
from .utils import cart_is_ready_to_checkout


def index(request):
    cart_partitioner = Partitioner(request.cart)
    formset = ReplaceCartLineFormSet(request.POST or None, cart=request.cart)

    # Cart check
    checkout_possible = cart_is_ready_to_checkout(request.cart)

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
