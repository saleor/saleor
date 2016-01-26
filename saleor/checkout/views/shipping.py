from django.shortcuts import redirect
from django.template.response import TemplateResponse
from saleor.checkout.forms import AnonymousUserShippingForm, ShippingAddressesForm
from saleor.userprofile.forms import AddressForm
from saleor.userprofile.models import Address


def anonymous_user_shipping_address_view(request, checkout):
    data = request.POST or None
    address_form = AddressForm(
        data, instance=checkout.shipping_address, autocomplete_type='shipping')
    user_form = AnonymousUserShippingForm(data, initial={'email': checkout.email})
    if user_form.is_valid() and address_form.is_valid():
        checkout.shipping_address = address_form.instance
        checkout.email = user_form.cleaned_data['email']
        return redirect('checkout:shipping-method')
    return TemplateResponse(
        request, 'checkout/shipping_address.html', context={
            'address_form': address_form, 'user_form': user_form, 'checkout': checkout})


def user_shipping_address_view(request, checkout):
    data = request.POST or None
    additional_addresses = request.user.addresses.all()
    checkout.email = request.user.email
    shipping_address = checkout.shipping_address

    if shipping_address is not None and shipping_address.id:
        address_form = AddressForm(data, autocomplete_type='shipping')
        addresses_form = ShippingAddressesForm(
            data, additional_addresses=additional_addresses,
            initial={'address': shipping_address.id})
    else:
        address_form = AddressForm(data, instance=shipping_address)
        addresses_form = ShippingAddressesForm(
            data, additional_addresses=additional_addresses)

    if addresses_form.is_valid():
        if addresses_form.cleaned_data['address'] != ShippingAddressesForm.NEW_ADDRESS:
            address_id = addresses_form.cleaned_data['address']
            checkout.shipping_address = Address.objects.get(id=address_id)
            return redirect('checkout:shipping-method')
        elif address_form.is_valid():
            checkout.shipping_address = address_form.instance
            return redirect('checkout:shipping-method')
    return TemplateResponse(
        request, 'checkout/shipping_address.html', context={
            'address_form': address_form, 'user_form': addresses_form,
            'checkout': checkout, 'additional_addresses': additional_addresses})
