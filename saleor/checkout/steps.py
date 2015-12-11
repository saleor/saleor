from __future__ import unicode_literals
from operator import itemgetter

from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from satchless.process import InvalidData

from .forms import ShippingForm, UserAddressesForm
from ..checkout.forms import AnonymousEmailForm
from ..core.utils import BaseStep
from ..delivery import get_delivery_options_for_items
from ..userprofile.forms import AddressForm
from ..userprofile.models import Address, User


def find_address_book_entry(addresses, address):
    for own_address in addresses:
        if Address.objects.are_identical(address, own_address):
            return own_address


class BaseCheckoutStep(BaseStep):
    is_step_valid = False
    is_step_available = False
    forms = {}

    def __init__(self, request, storage, checkout):
        super(BaseCheckoutStep, self).__init__(request)
        self.storage = storage
        self.checkout = checkout

    @models.permalink
    def get_absolute_url(self):
        return 'checkout:details', (), {'step': str(self)}

    def add_to_order(self, order):
        raise NotImplementedError()

    def __str__(self):
        return self.step_name


class ShippingAddressStep(BaseCheckoutStep):
    template = 'checkout/shipping_address.html'
    title = _('Shipping Address')
    step_name = 'shipping-address'
    is_new_address = True
    addresses = []

    def __init__(self, request, storage, checkout):
        super(ShippingAddressStep, self).__init__(request, storage, checkout)
        address_data = storage.get('address', {})
        address = Address(**address_data)
        self.address = address
        self.address_id = storage.get('address_id')
        initial_address = 'new'
        if request.user.is_authenticated():
            self.email = request.user.email
            addresses_queryset = request.user.addresses.all()
            self.addresses = list(addresses_queryset)
            selected_address = find_address_book_entry(self.addresses, address)
            if selected_address:
                address = None
                initial_address = selected_address.id
            elif not address_data:
                default_address = request.user.default_shipping_address
                if default_address:
                    initial_address = default_address.id
                elif self.addresses:
                    initial_address = self.addresses[0].id
        else:
            email = storage.get('email', '')
            self.email = email
            self.forms['email'] = AnonymousEmailForm(request.POST or None,
                                                     initial={'email': email})
            addresses_queryset = None

        self.forms['addresses_form'] = UserAddressesForm(
            data=request.POST or None, queryset=addresses_queryset,
            prefix=self.step_name, initial={'address': initial_address})
        self.forms['new_address'] = AddressForm(
            request.POST or None, prefix=self.step_name, instance=address)

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['addresses'] = self.addresses
        return super(ShippingAddressStep, self).process(extra_context=context)

    def forms_are_valid(self):
        address = None
        addresses_form = self.forms['addresses_form']
        if addresses_form.is_valid():
            choice = addresses_form.cleaned_data['address']
            if choice == 'new':
                new_address_form = self.forms['new_address']
                if new_address_form.is_valid():
                    address = Address(**new_address_form.cleaned_data)
            else:
                address = choice

            if address:
                own_address = find_address_book_entry(self.addresses, address)
                if own_address:
                    self.address = own_address
                    self.address_id = own_address.id
                else:
                    self.address = address
                    self.address_id = None

        email_form = self.forms.get('email')
        if email_form:
            valid_email = False
            if email_form.is_valid():
                valid_email = True
                self.email = self.forms['email'].cleaned_data['email']
            return address and valid_email
        return address

    def validate(self):
        try:
            self.address.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)

        if not self.email:
            raise InvalidData()

    def save(self):
        self.storage['email'] = self.email
        self.storage['address'] = Address.objects.as_data(self.address)
        self.storage['address_id'] = self.address_id

    def add_to_order(self, order):
        self.address.save()
        order.shipping_address = self.address
        if order.user:
            User.objects.store_address(order.user, self.address, shipping=True)


class ShippingMethodStep(BaseCheckoutStep):
    template = 'checkout/shipping_method.html'
    title = _('Shipping Method')
    step_name = 'shipping-method'

    def __init__(self, request, storage, shipping_address, cart, checkout):
        super(ShippingMethodStep, self).__init__(request, storage, checkout)
        self.shipping_method = None
        selected_method_name = storage.get('shipping_method')
        available_shipping = [
            {'method': method, 'cost': method.get_delivery_total(cart)}
            for method in get_delivery_options_for_items(
                cart, address=shipping_address)]

        shipping_choices = [(shipping['method'].name, shipping['method'].name)
                            for shipping in available_shipping]

        if available_shipping:
            for shipping in available_shipping:
                if shipping['method'].name == selected_method_name:
                    self.shipping_method = shipping['method']
                    break
            else:
                cheapest_shipping = min(available_shipping,
                                        key=itemgetter('cost'))
                selected_method_name = cheapest_shipping['method'].name
        self.available_shipping = available_shipping
        shipping_form = ShippingForm(shipping_choices, request.POST or None,
                                     initial={'method': selected_method_name})
        self.forms['shipping'] = shipping_form
        self.selected_method_name = selected_method_name

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['available_shipping'] = self.available_shipping
        context['selected_method_name'] = self.selected_method_name
        return super(ShippingMethodStep, self).process(extra_context=context)

    def save(self):
        shipping_form = self.forms['shipping']
        self.storage['shipping_method'] = shipping_form.cleaned_data['method']

    def add_to_order(self, order):
        order.shipping_method = self.shipping_method

    def validate(self):
        selected_method_name = self.storage.get('shipping_method')
        valid_methods = [d['method'].name for d in self.available_shipping]
        if selected_method_name not in valid_methods:
            raise InvalidData(_('Select a valid shipping method'))


class SummaryStep(BaseCheckoutStep):
    template = 'checkout/summary.html'
    title = _('Summary')
    step_name = 'summary'
    addresses = []
    select_copy_shipping_address = True

    def __init__(self, request, storage, shipping_address, checkout):
        super(SummaryStep, self).__init__(request, storage, checkout)
        self.billing_address = storage.get('billing_address')
        self.shipping_address = shipping_address
        without_shipping = not checkout.is_shipping_required()
        initial_address = 'copy' if shipping_address else 'new'
        if request.user.is_authenticated():
            queryset = request.user.addresses.all()
            self.addresses = list(queryset)
            default_billing_address = request.user.default_billing_address
            if default_billing_address:
                initial_address = default_billing_address.id
            elif without_shipping and self.addresses:
                initial_address = self.addresses[0].id
        else:
            queryset = None
            if without_shipping:
                self.forms['email'] = AnonymousEmailForm(request.POST or None)
        self.forms['new_address'] = AddressForm(request.POST or None,
                                                prefix=self.step_name)
        self.forms['addresses_form'] = UserAddressesForm(
            data=request.POST or None, queryset=queryset,
            prefix=self.step_name, initial={'address': initial_address},
            can_copy=shipping_address)

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['shipping_address'] = self.shipping_address
        context['addresses'] = self.addresses
        context['display_email_form'] = self.forms.get('email')
        response = super(SummaryStep, self).process(context)

        if not response:
            with transaction.atomic():
                order = self.checkout.create_order()
                order.create_history_entry()
                order.send_confirmation_email()
            return redirect('order:payment', token=order.token)
        return response

    def forms_are_valid(self):
        addresses_form = self.forms['addresses_form']
        new_address_form = self.forms['new_address']
        if addresses_form.is_valid():
            choice = addresses_form.cleaned_data['address']
            if choice == 'copy':
                self.billing_address = self.shipping_address
            elif choice in self.addresses:
                own_address = find_address_book_entry(self.addresses, choice)
                if own_address:
                    self.billing_address = own_address
                else:
                    self.billing_address = choice
            elif choice == 'new' and new_address_form.is_valid():
                self.billing_address = Address(**new_address_form.cleaned_data)

        email_form = self.forms.get('email')
        if email_form:
            return email_form.is_valid() and self.billing_address
        else:
            return self.billing_address

    def validate(self):
        raise InvalidData()

    def save(self):
        billing_addres_data = Address.objects.as_data(self.billing_address)
        self.storage = {'billing_address': billing_addres_data}
        if self.forms.get('email'):
            self.storage['email'] = self.forms['email'].cleaned_data['email']

    def add_to_order(self, order):
        self.billing_address.save()
        order.billing_address = self.billing_address
        if order.user:
            User.objects.store_address(
                order.user, self.billing_address, billing=True)
        order.save()
        method = order.shipping_method
        for partition in self.checkout.cart.partition():
            shipping_required = partition.is_shipping_required()
            if shipping_required and method:
                shipping_price = method.get_delivery_total(partition)
            else:
                shipping_price = 0
            group = order.groups.create(
                shipping_required=shipping_required,
                shipping_price=shipping_price,
                shipping_method=method)
            group.add_items_from_partition(partition)
        self.checkout.clear_storage()
