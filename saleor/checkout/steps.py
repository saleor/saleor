from __future__ import unicode_literals
from django.core.exceptions import ValidationError

from django.db import models
from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from satchless.process import InvalidData

from .forms import DeliveryForm, CopyShippingAddressForm
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
        return 'checkout:details', tuple(), {'step': str(self)}

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
        self.existing_selected = False
        address_form = self.address_form_class(
            request.POST or None, instance=self.address)
        self.forms = {'address': address_form}
        self.authenticated_user = False

        if request.user.is_authenticated():
            self.addresses = list(request.user.addresses.all())
            for address in self.addresses:
                data = Address.objects.as_data(address)
                instance = Address(**data)
                address.form = self.address_form_class(instance=instance)
                if Address.objects.are_identical(address, self.address):
                    self.existing_selected = True
            self.email = request.user.email
            self.authenticated_user = True
        else:
            self.addresses = []
            email = storage.get('email', '')

            self.forms['email'] = AnonymousEmailForm(request.POST or None,
                                                     initial={'email': email})
            self.email = email

    def __str__(self):
        return 'shipping-address'

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['addresses'] = self.addresses
        context['existing_address_selected'] = self.existing_selected
        return super(BaseCheckoutStep, self).process(extra_context=context)

    def save(self):
        if not self.authenticated_user:
            self.email = self.forms['email'].cleaned_data['email']
        self.storage['email'] = self.email
        address = self.forms['address'].cleaned_data
        self.address = Address(**address)
        self.storage['address'] = Address.objects.as_data(self.address)

    def add_to_order(self, order):
        self.address.save()
        order.shipping_address = self.address
        if order.user:
            User.objects.store_address(order.user, self.address, shipping=True)

    def validate(self):
        try:
            self.address.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)

        if not self.email:
            raise InvalidData()

    def forms_are_valid(self):
        return self.forms['address'].is_valid() and (
            self.authenticated_user or self.forms['email'].is_valid())


class ShippingMethodStep(BaseCheckoutStep):
    template = 'checkout/shipping_method.html'
    title = _('Shipping Method')
    forms = {}

    def __str__(self):
        return 'shipping-method'

    def __init__(self, request, storage, cart):
        super(ShippingMethodStep, self).__init__(request, storage)
        self.cart = cart
        address_data = storage.get('address', {})
        address = Address(**address_data)
        delivery_choices = [(method.name, method) for method
                            in get_delivery_options_for_items(self.cart,
                                                              address=address)]
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

    def __init__(self, request, whole_storage, checkout):
        self.same_blling_as_shipping = False
        self.whole_storage = whole_storage
        storage = whole_storage['summary']
        super(SummaryStep, self).__init__(request, storage)
        self.checkout = checkout
        self.forms['copy_shipping_address'] = CopyShippingAddressForm(
            request.POST or None)
        self.forms['billing_address'] = AddressForm(request.POST or None)

    def __str__(self):
        return 'summary'

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['billing_address'] = self.forms['billing_address']
        context['copy_shipping_address'] = self.forms['copy_shipping_address']

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
        copy_address_form = self.forms['copy_shipping_address']
        if (copy_address_form.is_valid()
            and copy_address_form.cleaned_data['billing_same_as_shipping']):
            self.same_blling_as_shipping = True
        else:
            if not self.forms['billing_address'].is_valid():
                return False

        next_step = self.checkout.get_next_step()
        return next_step == self

    def save(self):
        if self.same_blling_as_shipping:
            shipping_address = self.whole_storage['shipping']['address'].copy()
            address = Address(**shipping_address)
            self.billing_address = address
        else:
            billing_address = Address(
                **self.forms['billing_address'].cleaned_data)
            self.billing_address = billing_address
        billing_addres = Address.objects.as_data(self.billing_address)
        self.whole_storage['billing'] = {'address': billing_addres}

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
