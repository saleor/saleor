from __future__ import unicode_literals

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from satchless.item import Partitioner, InsufficientStock

from .forms import ReplaceCartLineFormSet


def index(request):
    cart_partitioner = Partitioner(request.cart)
    formset = ReplaceCartLineFormSet(request.POST or None, cart=request.cart)

    # Cart check
    checkout_possible = True
    for cartline in request.cart:
        variant_class = cartline.product.__class__
        variant = variant_class.objects.get(pk=cartline.product.pk)
        try:
            request.cart.check_quantity(
                product=variant,
                quantity=cartline.quantity,
                data=None
            )
        except InsufficientStock as e:
            cartline.error = _(
                "Sorry, only %d remaining in stock." % e.item.stock)
            checkout_possible = False

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
