from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ..utils import (
    get_cart_data_for_checkout, get_taxes_for_cart,
    update_shipping_address_in_anonymous_cart, update_shipping_address_in_cart)


def anonymous_user_shipping_address_view(request, cart):
    """Display the shipping step for a user who is not logged in."""
    user_form, address_form, updated = (
        update_shipping_address_in_anonymous_cart(
            cart, request.POST or None, request.country))

    if updated:
        return redirect('checkout:shipping-method')

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_cart_data_for_checkout(cart, request.discounts, taxes)
    ctx.update({
        'address_form': address_form,
        'user_form': user_form})
    return TemplateResponse(request, 'checkout/shipping_address.html', ctx)


def user_shipping_address_view(request, cart):
    """Display the shipping step for a logged in user.

    In addition to entering a new address the user has an option of selecting
    one of the existing entries from their address book.
    """
    cart.email = request.user.email
    cart.save(update_fields=['email'])
    user_addresses = cart.user.addresses.all()

    addresses_form, address_form, updated = update_shipping_address_in_cart(
        cart, user_addresses, request.POST or None, request.country)

    if updated:
        return redirect('checkout:shipping-method')

    taxes = get_taxes_for_cart(cart, request.taxes)
    ctx = get_cart_data_for_checkout(cart, request.discounts, taxes)
    ctx.update({
        'additional_addresses': user_addresses,
        'address_form': address_form,
        'user_form': addresses_form})
    return TemplateResponse(request, 'checkout/shipping_address.html', ctx)
