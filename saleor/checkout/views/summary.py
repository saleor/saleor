from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext, pgettext_lazy

from ...account.models import Address
from ...core import analytics
from ...core.exceptions import InsufficientStock
from ...order.emails import send_order_confirmation
from ..forms import CartNoteForm
from ..utils import (
    create_order, get_cart_data_for_checkout, get_taxes_for_cart,
    update_billing_address_in_anonymous_cart, update_billing_address_in_cart,
    update_billing_address_in_cart_with_shipping)


def handle_order_placement(request, cart):
    """Try to create an order and redirect the user as necessary.

    This is a helper function.
    """
    try:
        order = create_order(
            cart=cart,
            tracking_code=analytics.get_client_id(request),
            discounts=request.discounts,
            taxes=get_taxes_for_cart(cart, request.taxes))
    except InsufficientStock:
        return redirect('cart:index')

    if not order:
        msg = pgettext('Checkout warning', 'Please review your checkout.')
        messages.warning(request, msg)
        return redirect('checkout:summary')

    user = cart.user
    cart.delete()
    msg = pgettext_lazy('Order status history entry', 'Order was placed')
    order.history.create(user=user, content=msg)
    send_order_confirmation.delay(order.pk)
    return redirect('order:payment', token=order.token)


def summary_with_shipping_view(request, cart):
    """Display order summary with billing forms for a logged in user.

    Will create an order if all data is valid.
    """
    note_form = CartNoteForm(request.POST or None, instance=cart)
    if note_form.is_valid():
        note_form.save()

    user_addresses = (
        cart.user.addresses.all() if cart.user else Address.objects.none())

    addresses_form, address_form, updated = (
        update_billing_address_in_cart_with_shipping(
            cart, user_addresses, request.POST or None, request.country))

    if updated:
        return handle_order_placement(request, cart)

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_cart_data_for_checkout(cart, request.discounts, taxes)
    ctx.update({
        'additional_addresses': user_addresses,
        'address_form': address_form,
        'addresses_form': addresses_form,
        'note_form': note_form})
    return TemplateResponse(request, 'checkout/summary.html', ctx)


def anonymous_summary_without_shipping(request, cart):
    """Display order summary with billing forms for an unauthorized user.

    Will create an order if all data is valid.
    """
    note_form = CartNoteForm(request.POST or None, instance=cart)
    if note_form.is_valid():
        note_form.save()

    user_form, address_form, updated = (
        update_billing_address_in_anonymous_cart(
            cart, request.POST or None, request.country))

    if updated:
        return handle_order_placement(request, cart)

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_cart_data_for_checkout(cart, request.discounts, taxes)
    ctx.update({
        'address_form': address_form,
        'note_form': note_form,
        'user_form': user_form})
    return TemplateResponse(
        request, 'checkout/summary_without_shipping.html', ctx)


def summary_without_shipping(request, cart):
    """Display order summary for cases where shipping is not required.

    Will create an order if all data is valid.
    """
    note_form = CartNoteForm(request.POST or None, instance=cart)
    if note_form.is_valid():
        note_form.save()

    user_addresses = cart.user.addresses.all()

    addresses_form, address_form, updated = update_billing_address_in_cart(
        cart, user_addresses, request.POST or None, request.country)

    if updated:
        return handle_order_placement(request, cart)

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_cart_data_for_checkout(cart, request.discounts, taxes)
    ctx.update({
        'additional_addresses': user_addresses,
        'address_form': address_form,
        'addresses_form': addresses_form,
        'note_form': note_form})
    return TemplateResponse(
        request, 'checkout/summary_without_shipping.html', ctx)
