from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ....account.forms import get_address_form
from ....account.models import Address
from ..forms import AddressChoiceForm, AnonymousUserShippingForm
from ..utils import (
    get_checkout_data, get_taxes_for_cart, save_shipping_address_in_cart)


def anonymous_user_shipping_address_view(request, cart):
    """Display the shipping step for a user who is not logged in."""
    address_form, preview = get_address_form(
        request.POST or None, country_code=request.country.code,
        autocomplete_type='shipping',
        initial={'country': request.country.code},
        instance=cart.shipping_address)

    user_form = AnonymousUserShippingForm(
        not preview and request.POST or None,
        request.POST.dict() if preview else None, instance=cart)
    if all([user_form.is_valid(), address_form.is_valid()]):
        user_form.save()
        address = address_form.save()
        save_shipping_address_in_cart(cart, address)
        return redirect('cart:checkout-shipping-method')

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_checkout_data(cart, request.discounts, taxes)
    ctx.update({
        'address_form': address_form,
        'user_form': user_form})
    return TemplateResponse(request, 'checkout/shipping_address.html', ctx)


def get_shipping_address_forms(cart, user_addresses, data, country):
    """Forms initialized with data depending on current address in cart."""
    shipping_address = cart.shipping_address

    if shipping_address and shipping_address in user_addresses:
        address_form, preview = get_address_form(
            data, country_code=country.code,
            initial={'country': country})
        addresses_form = AddressChoiceForm(
            data, addresses=user_addresses,
            initial={'address': shipping_address.id})
    elif shipping_address:
        address_form, preview = get_address_form(
            data, country_code=shipping_address.country.code,
            instance=shipping_address)
        addresses_form = AddressChoiceForm(
            data, addresses=user_addresses)
    else:
        address_form, preview = get_address_form(
            data, country_code=country.code,
            initial={'country': country})
        addresses_form = AddressChoiceForm(
            data, addresses=user_addresses)

    return address_form, addresses_form, preview


def update_shipping_address_in_cart(cart, user_addresses, data, country):
    """Return shipping address choice forms and if and address was updated."""
    address_form, addresses_form, preview = (
        get_shipping_address_forms(cart, user_addresses, data, country))

    updated = False

    if addresses_form.is_valid() and not preview:
        use_existing_address = (
            addresses_form.cleaned_data['address'] !=
            AddressChoiceForm.NEW_ADDRESS)

        if use_existing_address:
            address_id = addresses_form.cleaned_data['address']
            address = Address.objects.get(id=address_id)
            save_shipping_address_in_cart(cart, address)
            updated = True

        elif address_form.is_valid():
            address = address_form.save()
            save_shipping_address_in_cart(cart, address)
            updated = True

    return addresses_form, address_form, updated


def user_shipping_address_view(request, cart):
    """Display the shipping step for a logged in user.

    In addition to entering a new address the user has an option of selecting
    one of the existing entries from their address book.
    """
    cart.user_email = request.user.email
    cart.save()
    user_addresses = cart.user.addresses.all()

    addresses_form, address_form, updated = update_shipping_address_in_cart(
        cart, user_addresses, request.POST or None, request.country)

    if updated:
        return redirect('cart:checkout-shipping-method')

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_checkout_data(cart, request.discounts, taxes)
    ctx.update({
        'additional_addresses': user_addresses,
        'address_form': address_form,
        'user_form': addresses_form})
    return TemplateResponse(request, 'checkout/shipping_address.html', ctx)
