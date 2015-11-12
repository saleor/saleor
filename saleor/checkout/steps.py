from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from satchless.process import InvalidData

from .forms import DeliveryForm, CopyShippingAddressForm, UserAddressesForm
from ..checkout.forms import AnonymousEmailForm
from ..core.utils import BaseStep
from ..delivery import get_delivery_options_for_items
from ..userprofile.forms import AddressForm
from ..userprofile.models import Address, User


class BaseCheckoutStep(BaseStep):

    def __init__(self, request, storage):
        super(BaseCheckoutStep, self).__init__(request)
        self.storage = storage

    @models.permalink
    def get_absolute_url(self):
        return 'checkout:details', (), {'step': str(self)}

    def add_to_order(self, order):
        raise NotImplementedError()


class ShippingAddressStep(BaseCheckoutStep):
    template = 'checkout/shipping_address.html'
    title = _('Shipping Address')
    address_form_class = AddressForm

    def __init__(self, request, storage):
        super(ShippingAddressStep, self).__init__(request, storage)
        address_data = storage.get('address', {})
        self.address = Address(**address_data)

        new_address_form = self.address_form_class(request.POST or None,
                                                   instance=self.address)
        self.forms = {'new_address': new_address_form}

        if request.user.is_authenticated():
            self.authenticated_user = True
            self.email = request.user.email
            existing_addresses = UserAddressesForm(request.user.addresses.all(),
                                                   data=request.POST or None)
            self.forms['existing_addresses'] = existing_addresses
            addresses = list(existing_addresses.fields['address']._queryset)
            self.addresses = addresses
            for address in addresses:
                 address.is_selected = Address.objects.are_identical(
                     address, self.address)
        else:
            self.authenticated_user = False
            self.addresses = []
            email = storage.get('email', '')
            self.email = email
            self.forms['email'] = AnonymousEmailForm(request.POST or None,
                                                     initial={'email': email})

    def __str__(self):
        return 'shipping-address'

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['addresses'] = self.addresses
        return super(BaseCheckoutStep, self).process(extra_context=context)

    def forms_are_valid(self):
        address_is_valid = False
        if self.addresses:
            addresses_form = self.forms['existing_addresses']
            if addresses_form.is_valid():
                # addresses = [a.id for a in self.addresses]
                address_id = addresses_form.cleaned_data['address']
                if address_id in self.addresses:
                    # self.address = Address.objects.get(pk=address_id.pk)
                    self.address = address_id
                    address_is_valid = True

        if not address_is_valid and self.forms['new_address'].is_valid():
            address_is_valid = True
            self.address = Address(**self.forms['new_address'].cleaned_data)

        return ((self.authenticated_user or self.forms['email'].is_valid())
                and address_is_valid)

    def validate(self):
        try:
            self.address.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)

        if not self.email:
            raise InvalidData()

    def save(self):
        if not self.authenticated_user:
            self.email = self.forms['email'].cleaned_data['email']

        self.storage['email'] = self.email
        # self.address = Address(**self.address)
        self.storage['address'] = Address.objects.as_data(self.address)

    def add_to_order(self, order):
        self.address.save()
        order.shipping_address = self.address
        if order.user:
            User.objects.store_address(order.user, self.address, shipping=True)


class ShippingMethodStep(BaseCheckoutStep):
    template = 'checkout/shipping_method.html'
    title = _('Shipping Method')
    forms = {}

    def __str__(self):
        return 'shipping-method'

    def __init__(self, request, storage, shipping_address, cart):
        super(ShippingMethodStep, self).__init__(request, storage)
        self.cart = cart
        delivery_choices = [
            (method.name, method) for method in get_delivery_options_for_items(
                self.cart, address=shipping_address)]
        self.valid_delivery_methods = [name for name, method
                                       in delivery_choices]
        selected_method_name = storage.get('delivery_method')
        for method_name, method in delivery_choices:
            if method_name == selected_method_name:
                delivery_method = method
                break
        else:
            # TODO: find cheapest not first
            selected_method_name, delivery_method = delivery_choices[0]
        self.delivery_method = delivery_method
        self.forms['delivery'] = DeliveryForm(
            delivery_choices,
            request.POST or None,
            initial={'method': selected_method_name})

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['form'] = self.forms['delivery']
        return super(ShippingMethodStep, self).process(extra_context=context)

    def save(self):
        delivery_form = self.forms['delivery']
        self.storage['delivery_method'] = delivery_form.cleaned_data['method']

    def add_to_order(self, order):
        order.delivery_method = self.delivery_method

    def validate(self):
        selected_method_name = self.storage.get('delivery_method')
        if selected_method_name not in self.valid_delivery_methods:
            raise InvalidData('Select a valid delivery method')


class SummaryStep(BaseCheckoutStep):
    template = 'checkout/summary.html'
    title = _('Summary')
    forms = {}
    billing_address = None

    def __init__(self, request, storage, shipping_address, checkout):
        self.same_blling_as_shipping = False
        self.shipping_address = shipping_address
        super(SummaryStep, self).__init__(request, storage)
        self.checkout = checkout
        if shipping_address:
            self.forms['copy_shipping_address'] = CopyShippingAddressForm(
                request.POST or None)
        self.forms['billing_address'] = AddressForm(request.POST or None)

    def __str__(self):
        return 'summary'

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['shipping_address'] = self.shipping_address
        print "--------------"
        print self.shipping_address
        print "--------------"
        context['billing_address'] = self.forms['billing_address']
        copy_address_form = self.forms.get('copy_shipping_address')
        if copy_address_form:
            context['copy_shipping_address'] = copy_address_form

        response = super(SummaryStep, self).process(context)

        if not response:
            with transaction.atomic():
                order = self.checkout.create_order()
                order.create_history_entry()
                order.send_confirmation_email()
            return redirect('order:payment', token=order.token)
        return response

    def validate(self):
        raise InvalidData()

    def forms_are_valid(self):
        copy_address_form = self.forms.get('copy_shipping_address')
        if (copy_address_form
            and copy_address_form.is_valid()
            and copy_address_form.cleaned_data['billing_same_as_shipping']):
            self.same_blling_as_shipping = True
        else:
            if not self.forms['billing_address'].is_valid():
                return False
        next_step = self.checkout.get_next_step()
        return next_step == self

    def save(self):
        if self.same_blling_as_shipping:
            billing_addres_data = Address.objects.as_data(self.shipping_address)
        else:
            billing_addres_data = self.forms['billing_address'].cleaned_data
        self.storage = {'billing_address': billing_addres_data}
        self.billing_address = Address(**billing_addres_data)


    def billing_address_add_to_order(self, order):
        self.billing_address.save()
        order.billing_address = self.billing_address
        if order.user:
            User.objects.store_address(
                order.user, self.billing_address, billing=True)

    def add_to_order(self, order):
        self.billing_address_add_to_order(order)
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
