from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext, pgettext_lazy

from ....account.forms import get_address_form
from ....account.models import Address
from ....core import analytics
from ....core.exceptions import InsufficientStock
from ....order.emails import send_order_confirmation
from ..forms import (
    AddressChoiceForm, AnonymousUserBillingForm, BillingAddressChoiceForm,
    CartNoteForm)
from ..utils import (
    get_checkout_data, get_taxes_for_cart, save_billing_address_in_cart)
from .. import utils


def create_order(cart, tracking_code, discounts, taxes):
    """Finalize a checkout process and create an order.

    This is a helper function.
    """
    order = utils.create_order(cart, tracking_code, discounts, taxes)
    if not order:
        return None, redirect('cart:checkout-summary')
    user = cart.user
    cart.clear()
    msg = pgettext_lazy('Order status history entry', 'Order was placed')
    order.history.create(user=user, content=msg)
    send_order_confirmation.delay(order.pk)
    return order, redirect('order:payment', token=order.token)


def handle_order_placement(request, cart):
    """Try to create an order and redirect the user as necessary.

    This is a helper function.
    """
    tracking_code = analytics.get_client_id(request)
    taxes = get_taxes_for_cart(cart, request.taxes)
    try:
        order, redirect_url = create_order(
            cart, tracking_code, request.discounts, taxes)
    except InsufficientStock:
        return redirect('cart:index')
    if not order:
        msg = pgettext('Checkout warning', 'Please review your checkout.')
        messages.warning(request, msg)
    return redirect_url


def get_billing_forms_with_shipping(
        data, addresses, billing_address, shipping_address):
    """Get billing form based on a the current billing and shipping data."""
    if not billing_address.id or billing_address == shipping_address:
        address_form, preview = get_address_form(
            data, country_code=shipping_address.country.code,
            autocomplete_type='billing',
            initial={'country': shipping_address.country.code})
        addresses_form = BillingAddressChoiceForm(
            data, addresses=addresses, initial={
                'address': BillingAddressChoiceForm.SHIPPING_ADDRESS})
    elif billing_address in addresses:
        address_form, preview = get_address_form(
            data, country_code=billing_address.country.code,
            autocomplete_type='billing',
            initial={'country': billing_address.country})
        addresses_form = BillingAddressChoiceForm(
            data, additional_addresses=addresses, initial={
                'address': billing_address.id})
    else:
        address_form, preview = get_address_form(
            data, country_code=billing_address.country.code,
            autocomplete_type='billing',
            initial={'country': billing_address.country.code},
            instance=billing_address)
        addresses_form = BillingAddressChoiceForm(
            data, addresses=addresses, initial={
                'address': BillingAddressChoiceForm.NEW_ADDRESS})

    if addresses_form.is_valid() and not preview:
        address_id = addresses_form.cleaned_data['address']
        if address_id == BillingAddressChoiceForm.SHIPPING_ADDRESS:
            return address_form, addresses_form, shipping_address
        elif address_id != BillingAddressChoiceForm.NEW_ADDRESS:
            address = addresses.get(id=address_id)
            return address_form, addresses_form, address
        elif address_form.is_valid():
            return address_form, addresses_form, address_form.save()
    return address_form, addresses_form, None


def summary_with_shipping_view(request, cart):
    """Display order summary with billing forms for a logged in user.

    Will create an order if all data is valid.
    """
    note_form = CartNoteForm(request.POST or None, instance=cart)
    if note_form.is_valid():
        note_form.save()

    if request.user.is_authenticated:
        additional_addresses = request.user.addresses.all()
    else:
        additional_addresses = Address.objects.none()

    address_form, addresses_form, address = get_billing_forms_with_shipping(
        request.POST or None, additional_addresses,
        cart.billing_address or Address(country=request.country),
        cart.shipping_address)

    if address is not None:
        save_billing_address_in_cart(cart, address)
        return handle_order_placement(request, cart)

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_checkout_data(cart, request.discounts, taxes)
    ctx.update({
        'additional_addresses': additional_addresses,
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

    user_form = AnonymousUserBillingForm(request.POST or None, instance=cart)
    billing_address = cart.billing_address
    if billing_address:
        address_form, preview = get_address_form(
            request.POST or None, country_code=billing_address.country.code,
            autocomplete_type='billing', instance=billing_address)
    else:
        address_form, preview = get_address_form(
            request.POST or None, country_code=request.country.code,
            autocomplete_type='billing', initial={'country': request.country})

    if all([user_form.is_valid(), address_form.is_valid()]) and not preview:
        user_form.save()
        address = address_form.save()
        save_billing_address_in_cart(cart, address)
        return handle_order_placement(request, cart)

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_checkout_data(cart, request.discounts, taxes)
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

    billing_address = cart.billing_address
    user_addresses = request.user.addresses.all()
    if billing_address and billing_address in user_addresses:
        address_form, preview = get_address_form(
            request.POST or None, autocomplete_type='billing',
            country_code=billing_address.country.code,
            initial={'country': billing_address.country.code})
        addresses_form = AddressChoiceForm(
            request.POST or None, addresses=user_addresses,
            initial={'address': billing_address.id})
    elif billing_address:
        address_form, preview = get_address_form(
            request.POST or None, autocomplete_type='billing',
            initial={'country': billing_address.country.code},
            instance=billing_address,
            country_code=billing_address.country.code)
        addresses_form = AddressChoiceForm(
            request.POST or None, addresses=user_addresses,
            initial={'address': AddressChoiceForm.NEW_ADDRESS})
    else:
        address_form, preview = get_address_form(
            request.POST or None, autocomplete_type='billing',
            initial={'country': request.country},
            country_code=request.country.code)

        if request.user.is_authenticated:
            initial_address = (
                request.user.default_billing_address.id
                if request.user.default_billing_address
                else AddressChoiceForm.NEW_ADDRESS)
        else:
            initial_address = AddressChoiceForm.NEW_ADDRESS

        addresses_form = AddressChoiceForm(
            request.POST or None, addresses=user_addresses,
            initial={'address': initial_address})

    if addresses_form.is_valid():
        use_existing_address = (
            addresses_form.cleaned_data['address'] !=
            AddressChoiceForm.NEW_ADDRESS)

        if use_existing_address:
            address_id = addresses_form.cleaned_data['address']
            address = Address.objects.get(id=address_id)
            save_billing_address_in_cart(cart, address)
            return handle_order_placement(request, cart)

        elif address_form.is_valid():
            address = address_form.save()
            save_billing_address_in_cart(cart, address)
            return handle_order_placement(request, cart)

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_checkout_data(cart, request.discounts, taxes)
    ctx.update({
        'additional_addresses': user_addresses,
        'address_form': address_form,
        'addresses_form': addresses_form,
        'note_form': note_form})
    return TemplateResponse(
        request, 'checkout/summary_without_shipping.html', ctx)
