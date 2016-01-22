from django.shortcuts import redirect
from django.template.response import TemplateResponse


from .core import load_checkout
from .forms import (ShippingAddressesForm, AnonymousUserShippingForm,
                    ShippingMethodForm, BillingAddressesForm)
from .validators import (
    validate_cart, validate_shipping_address, validate_shipping_method)
from ..userprofile.forms import AddressForm
from ..userprofile.models import Address

STORAGE_SESSION_KEY = 'checkout_storage'


def get_user_shipping_forms(data, additional_addresses, shipping_address):
    if shipping_address.id:
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
            address = Address.objects.get(id=address_id)
            return address_form, addresses_form, address
        elif address_form.is_valid():
            address = address_form.instance
            return address_form, addresses_form, address
    return address_form, addresses_form, None


def get_anonymous_user_shipping_forms(data, shipping_address, email):
    address_form = AddressForm(
        data, instance=shipping_address, autocomplete_type='shipping')
    user_form = AnonymousUserShippingForm(data, initial={'email': email})
    if user_form.is_valid() and address_form.is_valid():
        address = address_form.instance
        email = user_form.cleaned_data['email']
    else:
        address = None
        email = None
    return address_form, user_form, address, email


def get_billing_forms(data, additional_addresses, billing_address, shipping_address):
    if Address.objects.are_identical(billing_address, shipping_address):
        address_form = AddressForm(data, autocomplete_type='billing')
        addresses_form = BillingAddressesForm(
            data, additional_addresses=additional_addresses, initial={
                'address': BillingAddressesForm.SHIPPING_ADDRESS})
    elif billing_address.id is None:
        address_form = AddressForm(
            data, instance=billing_address, autocomplete_type='billing')
        addresses_form = BillingAddressesForm(
            data, additional_addresses=additional_addresses, initial={
                'address': BillingAddressesForm.NEW_ADDRESS})
    else:
        address_form = AddressForm(data, autocomplete_type='billing')
        addresses_form = BillingAddressesForm(
            data, additional_addresses=additional_addresses, initial={
                'address': billing_address.id})
    if addresses_form.is_valid():
        address_id = addresses_form.cleaned_data['address']
        if address_id == BillingAddressesForm.SHIPPING_ADDRESS:
            return address_form, addresses_form, shipping_address
        elif address_id != BillingAddressesForm.NEW_ADDRESS:
            address = additional_addresses.get(id=address_id)
            return address_form, addresses_form, address
        elif address_form.is_valid():
            return address_form, addresses_form, address_form.instance
    return address_form, addresses_form, None


@load_checkout
@validate_cart
def index_view(request, checkout):
    return redirect('checkout:shipping-address')


@load_checkout
@validate_cart
def shipping_address_view(request, checkout):
    data = request.POST or None
    if request.user.is_authenticated():
        additional_addresses = request.user.addresses.all()
        email = request.user.email
        address_form, user_form, address = get_user_shipping_forms(
            data, additional_addresses, checkout.shipping_address)
    else:
        additional_addresses = Address.objects.none()
        address_form, user_form, address, email = get_anonymous_user_shipping_forms(
            data, checkout.shipping_address, checkout.email)
    if address is not None and email is not None:
        checkout.shipping_address = address
        checkout.email = email
        return redirect('checkout:shipping-method')
    return TemplateResponse(
        request, 'checkout/shipping_address.html', context={
            'address_form': address_form, 'user_form': user_form, 'checkout': checkout,
            'additional_addresses': additional_addresses})


@load_checkout
@validate_cart
@validate_shipping_address
def shipping_method_view(request, checkout):
    country_code = checkout.shipping_address.country.code
    shipping_method_form = ShippingMethodForm(
        country_code, request.POST or None, initial={'method': checkout.shipping_method})
    if shipping_method_form.is_valid():
        checkout.shipping_method = shipping_method_form.cleaned_data['method']
        return redirect('checkout:summary')
    return TemplateResponse(request, 'checkout/shipping_method.html', context={
        'shipping_method_form': shipping_method_form, 'checkout': checkout})


@load_checkout
@validate_cart
@validate_shipping_address
@validate_shipping_method
def summary_view(request, checkout):
    user = request.user
    data = request.POST or None
    if user.is_authenticated():
        additional_addresses = user.addresses.all()
    else:
        additional_addresses = Address.objects.none()
    address_form, addresses_form, address = get_billing_forms(
        data, additional_addresses, checkout.billing_address, checkout.shipping_address)
    if address is not None:
        checkout.billing_address = address
        order = checkout.create_order()
        checkout.clear_storage()
        request.cart.clear()
        order.create_history_entry()
        order.send_confirmation_email()
        return redirect('order:payment', token=order.token)
    return TemplateResponse(
        request, 'checkout/summary.html', context={
            'addresses_form': addresses_form, 'address_form': address_form,
            'checkout': checkout, 'additional_addresses': additional_addresses})



