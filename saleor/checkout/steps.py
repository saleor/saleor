from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from satchless.process import InvalidData

from .forms import DeliveryForm, UserAddressesForm
from ..checkout.forms import AnonymousEmailForm
from ..core.utils import BaseStep
from ..delivery import get_delivery_options_for_items
from ..userprofile.forms import AddressForm
from ..userprofile.models import Address, User


class BaseCheckoutStep(BaseStep):
    is_step_valid = False
    is_step_available = False

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
    forms = {}

    def __init__(self, request, storage, checkout):

        super(ShippingAddressStep, self).__init__(request, storage, checkout)
        address_data = storage.get('address', {})
        self.address = Address(**address_data)
        self.address_id = storage.get('address_id')
        self.available_address_choices = [('new', _('Enter a new address'))]

        if request.user.is_authenticated():
            self.email = request.user.email
            queryset = request.user.addresses.all()
            addresses = list(queryset)
            self.addresses = addresses

            if not self.get_same_own_address(self.address):
                address = self.address
            else:
                address = None
            new_address_form = AddressForm(request.POST or None,
                                           prefix=self.step_name,
                                           instance=address)

            f = UserAddressesForm(
                queryset=queryset, possibilities=self.available_address_choices,
                data=request.POST or None, prefix=self.step_name)


            self.forms['addresses_form'] = f

            if not new_address_form.is_bound:
                selected_address = self.get_same_own_address(self.address)
                if selected_address:
                    selected_address.is_selected = True
                    self.is_new_address = False
                elif not address_data:
                    default_address = request.user.default_shipping_address
                    if default_address:
                        address = self.get_same_own_address(default_address)
                        if address:
                            address.is_selected = True
                            self.is_new_address = False
                    elif addresses:
                        addresses[0].is_selected = True
                        self.is_new_address = False
        else:
            new_address_form = AddressForm(request.POST or None,
                                           prefix=self.step_name,
                                           instance=self.address)
            email = storage.get('email', '')
            self.email = email
            self.forms['email'] = AnonymousEmailForm(request.POST or None,
                                                     initial={'email': email})
        self.forms['new_address'] = new_address_form

    def get_same_own_address(self, address):
        for own_address in self.addresses:
            if Address.objects.are_identical(address, own_address):
                return own_address

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['addresses'] = self.addresses
        context['new_address'] = self.is_new_address
        context['button_label'] = _('Ship to this address')
        return super(BaseCheckoutStep, self).process(extra_context=context)

    def forms_are_valid(self):
        address_is_valid = False
        if self.addresses:
            addresses_form = self.forms['addresses_form']
            if addresses_form.is_valid():
                selected_address = addresses_form.cleaned_data['address']
                special_values = [value for value, label
                                  in self.available_address_choices]
                if selected_address not in special_values:
                    own_address = self.get_same_own_address(selected_address)
                    if own_address:
                        self.address = own_address
                        self.address_id = own_address.id
                        address_is_valid = True

        if not address_is_valid and self.forms['new_address'].is_valid():
            self.address = Address(**self.forms['new_address'].cleaned_data)
            self.address_id = None
            address_is_valid = True

        email_form = self.forms.get('email')
        if email_form:
            return email_form.is_valid() and address_is_valid
        else:
            return address_is_valid

    def validate(self):
        try:
            self.address.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)

        if not self.email:
            raise InvalidData()

    def save(self):
        if self.forms.get('email'):
            self.email = self.forms['email'].cleaned_data['email']

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
        self.delivery_method = None
        selected_method_name = storage.get('delivery_method')
        available_deliveries = [
            {'method': method, 'cost': method.get_delivery_total(cart)}
            for method in get_delivery_options_for_items(
                cart, address=shipping_address)]

        # import pytest; pytest.set_trace()
        delivery_choices = [(delivery['method'].name, delivery['method'].name)
                            for delivery in available_deliveries]

        if available_deliveries:
            cheapest_delivery = available_deliveries[0]

        for delivery in available_deliveries:
            if delivery['method'].name == selected_method_name:
                self.delivery_method = delivery['method']
                break
            if delivery['cost'] < cheapest_delivery['cost']:
                cheapest_delivery = delivery
        else:
            selected_method_name = cheapest_delivery['method'].name
        self.available_deliveries = available_deliveries
        delivery_form = DeliveryForm(delivery_choices, request.POST or None,
                                     initial={'method': selected_method_name})
        self.forms = {'delivery': delivery_form}
        self.selected_method_name = selected_method_name

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['available_deliveries'] = self.available_deliveries
        context['selected_method_name'] = self.selected_method_name
        return super(ShippingMethodStep, self).process(extra_context=context)

    def save(self):
        delivery_form = self.forms['delivery']
        self.storage['delivery_method'] = delivery_form.cleaned_data['method']

    def add_to_order(self, order):
        order.delivery_method = self.delivery_method

    def validate(self):
        selected_method_name = self.storage.get('delivery_method')
        valid_methods = [d['method'].name for d in self.available_deliveries]
        if selected_method_name not in valid_methods:
            raise InvalidData('Select a valid delivery method')


class SummaryStep(BaseCheckoutStep):
    template = 'checkout/summary.html'
    title = _('Summary')
    step_name = 'summary'
    addresses = []
    select_copy_shipping_address = True
    available_address_choices = [('new', _('Enter a new address'))]

    def __init__(self, request, storage, shipping_address, checkout):
        super(SummaryStep, self).__init__(request, storage, checkout)
        self.billing_address = storage.get('billing_address')
        self.shipping_address = shipping_address
        self.forms = {'new_address': AddressForm(request.POST or None,
                                                 prefix=self.step_name)}
        if shipping_address:
            self.available_address_choices.append(
                ('copy', _('Copy shipping address')))

        if request.user.is_authenticated():
            queryset = request.user.addresses.all()
            self.addresses = list(queryset)
            addresses_form = UserAddressesForm(
                queryset=queryset, possibilities=self.available_address_choices,
                data=request.POST or None, prefix=self.step_name)

            if not self.forms['new_address'].is_bound:
                default_billing_address = request.user.default_billing_address
                if default_billing_address:
                    for address in self.addresses:
                        if Address.objects.are_identical(
                                address, default_billing_address):
                            address.is_selected = True
                            self.select_copy_shipping_address = False
                            break
        else:
            addresses_form = UserAddressesForm(
                queryset=None, possibilities=self.available_address_choices,
                data=request.POST or None, prefix=self.step_name)
            if not checkout.is_shipping_required():
                self.forms['email'] = AnonymousEmailForm(request.POST or None)

        self.forms['addresses_form'] = addresses_form

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['shipping_address'] = self.shipping_address
        context['addresses'] = self.addresses
        context['button_label'] = _('Bill to this address')
        context['display_email_form'] = self.forms.get('email')
        context['new_address'] = self.forms['new_address'].is_bound
        context['copy_shipping_address'] = self.select_copy_shipping_address
        response = super(SummaryStep, self).process(context)

        if not response:
            with transaction.atomic():
                order = self.checkout.create_order()
                order.create_history_entry()
                order.send_confirmation_email()
            return redirect('order:payment', token=order.token)
        return response

    def forms_are_valid(self):
        billing_address = None
        addresses_form = self.forms['addresses_form']
        new_address_form = self.forms['new_address']
        if addresses_form.is_valid():
            choice = addresses_form.cleaned_data['address']
            if choice == "copy":
                billing_address = self.shipping_address
            elif choice in self.addresses:
                billing_address = choice

        if not billing_address and new_address_form.is_valid():
            billing_address = Address(**new_address_form.cleaned_data)

        if billing_address:
            self.billing_address = billing_address

        email_form = self.forms.get('email')
        if email_form:
            return email_form.is_valid() and billing_address
        else:
            return billing_address

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
        if self.checkout.is_shipping_required():
            method = order.delivery_method
        else:
            method = None
        for partition in self.checkout.cart.partition():
            shipping_required = partition.is_shipping_required()
            if shipping_required and method:
                shipping_price = method.get_delivery_total(partition)
            else:
                shipping_price = 0
            group = order.groups.create(
                shipping_required=shipping_required,
                shipping_price=shipping_price)
            group.add_items_from_partition(partition)
        self.checkout.clear_storage()
