from django.shortcuts import redirect
from django.template.response import TemplateResponse

from ...account.forms import get_address_form
from ...account.models import Address
from ..forms import AnonymousUserShippingForm, ShippingAddressesForm


def anonymous_user_shipping_address_view(request, checkout):
    """Display the shipping step for a user who is not logged in."""
    address_form, preview = get_address_form(
        request.POST or None, country_code=request.country.code,
        autocomplete_type='shipping',
        initial={'country': request.country.code},
        instance=checkout.shipping_address)

    user_form = AnonymousUserShippingForm(
        not preview and request.POST or None, initial={'email': checkout.email}
        if not preview else request.POST.dict())
    if all([user_form.is_valid(), address_form.is_valid()]):
        checkout.shipping_address = address_form.instance
        checkout.email = user_form.cleaned_data['email']
        return redirect('checkout:shipping-method')
    return TemplateResponse(
        request, 'checkout/shipping_address.html', context={
            'address_form': address_form, 'user_form': user_form,
            'checkout': checkout})


def user_shipping_address_view(request, checkout):
    """Display the shipping step for a logged in user.

    In addition to entering a new address the user has an option of selecting
    one of the existing entries from their address book.
    """
    data = request.POST or None
    additional_addresses = request.user.addresses.all()
    checkout.email = request.user.email
    shipping_address = checkout.shipping_address

    if shipping_address is not None and shipping_address.id:
        address_form, preview = get_address_form(
            data, country_code=request.country.code,
            initial={'country': request.country})
        addresses_form = ShippingAddressesForm(
            data, additional_addresses=additional_addresses,
            initial={'address': shipping_address.id})
    elif shipping_address:
        address_form, preview = get_address_form(
            data, country_code=shipping_address.country.code,
            instance=shipping_address)
        addresses_form = ShippingAddressesForm(
            data, additional_addresses=additional_addresses)
    else:
        address_form, preview = get_address_form(
            data, initial={'country': request.country},
            country_code=request.country.code)
        addresses_form = ShippingAddressesForm(
            data, additional_addresses=additional_addresses)

    if addresses_form.is_valid() and not preview:
        if (addresses_form.cleaned_data['address'] !=
                ShippingAddressesForm.NEW_ADDRESS):
            address_id = addresses_form.cleaned_data['address']
            checkout.shipping_address = Address.objects.get(id=address_id)
            return redirect('checkout:shipping-method')
        elif address_form.is_valid():
            checkout.shipping_address = address_form.instance
            return redirect('checkout:shipping-method')
    return TemplateResponse(
        request, 'checkout/shipping_address.html', context={
            'address_form': address_form, 'user_form': addresses_form,
            'checkout': checkout,
            'additional_addresses': additional_addresses})
