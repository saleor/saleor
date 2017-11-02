from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext

from ..forms import (
    AnonymousUserBillingForm, BillingAddressesForm,
    BillingWithoutShippingAddressForm)
from ...userprofile.forms import get_address_form
from ...userprofile.models import Address


def create_order(checkout):
    """Finalize a checkout session and create an order.

    This is a helper function.

    `checkout` is a `saleor.checkout.core.Checkout` instance.
    """
    order = checkout.create_order()
    if not order:
        return None, redirect('checkout:summary')
    checkout.clear_storage()
    checkout.cart.clear()
    order.create_history_entry()
    order.send_confirmation_email()
    return order, redirect('order:payment', token=order.token)


def handle_order_placement(request, checkout):
    """Try to create an order and redirect the user as necessary.

    This is a helper function.
    """
    order, redirect = create_order(checkout)
    if not order:
        msg = pgettext('Checkout warning', 'Please review your checkout.')
        messages.warning(request, msg)
    return redirect


def get_billing_forms_with_shipping(
        data, addresses, billing_address, shipping_address):
    """Get billing form based on a the current billing and shipping data."""
    if Address.objects.are_identical(billing_address, shipping_address):
        address_form, preview = get_address_form(
            data, country_code=shipping_address.country.code,
            autocomplete_type='billing',
            initial={'country': shipping_address.country.code},
            instance=None)
        addresses_form = BillingAddressesForm(
            data, additional_addresses=addresses, initial={
                'address': BillingAddressesForm.SHIPPING_ADDRESS})
    elif billing_address.id is None:
        address_form, preview = get_address_form(
            data, country_code=billing_address.country.code,
            autocomplete_type='billing',
            initial={'country': billing_address.country.code},
            instance=billing_address)
        addresses_form = BillingAddressesForm(
            data, additional_addresses=addresses, initial={
                'address': BillingAddressesForm.NEW_ADDRESS})
    else:
        address_form, preview = get_address_form(
            data, country_code=billing_address.country.code,
            autocomplete_type='billing',
            initial={'country': billing_address.country})
        addresses_form = BillingAddressesForm(
            data, additional_addresses=addresses, initial={
                'address': billing_address.id})
    if addresses_form.is_valid() and not preview:
        address_id = addresses_form.cleaned_data['address']
        if address_id == BillingAddressesForm.SHIPPING_ADDRESS:
            return address_form, addresses_form, shipping_address
        elif address_id != BillingAddressesForm.NEW_ADDRESS:
            address = addresses.get(id=address_id)
            return address_form, addresses_form, address
        elif address_form.is_valid():
            return address_form, addresses_form, address_form.instance
    return address_form, addresses_form, None


def summary_with_shipping_view(request, checkout):
    """Display order summary with billing forms for a logged in user.

    Will create an order if all data is valid.
    """
    if request.user.is_authenticated:
        additional_addresses = request.user.addresses.all()
    else:
        additional_addresses = Address.objects.none()
    address_form, addresses_form, address = get_billing_forms_with_shipping(
        request.POST or None, additional_addresses,
        checkout.billing_address or Address(country=request.country),
        checkout.shipping_address)
    if address is not None:
        checkout.billing_address = address
        return handle_order_placement(request, checkout)
    return TemplateResponse(
        request, 'checkout/summary.html', context={
            'addresses_form': addresses_form, 'address_form': address_form,
            'checkout': checkout,
            'additional_addresses': additional_addresses})


def anonymous_summary_without_shipping(request, checkout):
    """Display order summary with billing forms for an unauthorized user.

    Will create an order if all data is valid.
    """
    user_form = AnonymousUserBillingForm(
        request.POST or None, initial={'email': checkout.email})
    billing_address = checkout.billing_address
    if billing_address:
        address_form, preview = get_address_form(
            request.POST or None, country_code=billing_address.country.code,
            autocomplete_type='billing', instance=billing_address)
    else:
        address_form, preview = get_address_form(
            request.POST or None, country_code=request.country.code,
            autocomplete_type='billing', initial={'country': request.country})
    if all([user_form.is_valid(), address_form.is_valid()]) and not preview:
        checkout.email = user_form.cleaned_data['email']
        checkout.billing_address = address_form.instance
        return handle_order_placement(request, checkout)
    return TemplateResponse(
        request, 'checkout/summary_without_shipping.html', context={
            'user_form': user_form, 'address_form': address_form,
            'checkout': checkout})


def summary_without_shipping(request, checkout):
    """Display order summary for cases where shipping is not required.

    Will create an order if all data is valid.
    """
    billing_address = checkout.billing_address
    user_addresses = request.user.addresses.all()
    if billing_address and billing_address.id:
        address_form, preview = get_address_form(
            request.POST or None, autocomplete_type='billing',
            initial={'country': request.country},
            country_code=billing_address.country.code,
            instance=billing_address)
        addresses_form = BillingWithoutShippingAddressForm(
            request.POST or None, additional_addresses=user_addresses,
            initial={'address': billing_address.id})
    elif billing_address:
        address_form, preview = get_address_form(
            request.POST or None, autocomplete_type='billing',
            instance=billing_address,
            country_code=billing_address.country.code)
        addresses_form = BillingWithoutShippingAddressForm(
            request.POST or None, additional_addresses=user_addresses)
    else:
        address_form, preview = get_address_form(
            request.POST or None, autocomplete_type='billing',
            initial={'country': request.country},
            country_code=request.country.code)
        addresses_form = BillingWithoutShippingAddressForm(
            request.POST or None, additional_addresses=user_addresses)

    if addresses_form.is_valid():
        address_id = addresses_form.cleaned_data['address']
        if address_id != BillingWithoutShippingAddressForm.NEW_ADDRESS:
            checkout.billing_address = user_addresses.get(id=address_id)
            return handle_order_placement(request, checkout)
        elif address_form.is_valid() and not preview:
            checkout.billing_address = address_form.instance
            return handle_order_placement(request, checkout)
    return TemplateResponse(
        request, 'checkout/summary_without_shipping.html', context={
            'addresses_form': addresses_form, 'address_form': address_form,
            'checkout': checkout, 'additional_addresses': user_addresses})
