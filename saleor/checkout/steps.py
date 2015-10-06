from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from satchless.process import InvalidData

from .forms import DeliveryForm
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
        return ('checkout:details', (), {'step': str(self)})

    def add_to_order(self, order):
        raise NotImplementedError()


class BaseAddressStep(BaseCheckoutStep):
    template = 'checkout/address.html'

    def __init__(self, request, storage, address):
        super(BaseAddressStep, self).__init__(request, storage)
        self.address = address
        existing_selected = False
        address_form = AddressForm(request.POST or None, instance=self.address)
        if request.user.is_authenticated():
            addresses = list(request.user.addresses.all())
            for address in addresses:
                data = Address.objects.as_data(address)
                instance = Address(**data)
                address.form = AddressForm(instance=instance)
                address.is_selected = Address.objects.are_identical(
                    address, self.address)
                if address.is_selected:
                    existing_selected = True
        else:
            addresses = []
        self.existing_selected = existing_selected
        self.forms = {'address': address_form}
        self.addresses = addresses

    def forms_are_valid(self):
        address_form = self.forms['address']
        return address_form.is_valid()

    def validate(self):
        try:
            self.address.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['form'] = self.forms['address']
        context['addresses'] = self.addresses
        context['existing_address_selected'] = self.existing_selected
        return super(BaseAddressStep, self).process(extra_context=context)


class BillingAddressStep(BaseAddressStep):
    template = 'checkout/billing.html'
    title = _('Billing Address')

    def __init__(self, request, storage):
        address_data = storage.get('address', {})
        address = Address(**address_data)
        skip = False
        if not address_data and request.user.is_authenticated():
            if request.user.default_billing_address:
                address = request.user.default_billing_address
                skip = True
            elif request.user.addresses.count() == 1:
                address = request.user.addresses.all()[0].address
                skip = True
        super(BillingAddressStep, self).__init__(request, storage, address)
        if not request.user.is_authenticated():
            self.anonymous_user_email = self.storage.get(
                'anonymous_user_email')
            initial = {'email': self.anonymous_user_email}
            self.forms['anonymous'] = AnonymousEmailForm(request.POST or None,
                                                         initial=initial)
        else:
            self.anonymous_user_email = ''
        if skip:
            self.save()

    def __str__(self):
        return 'billing-address'

    def forms_are_valid(self):
        forms_are_valid = super(BillingAddressStep, self).forms_are_valid()
        if 'anonymous' not in self.forms:
            return forms_are_valid
        anonymous_form = self.forms['anonymous']
        if forms_are_valid and anonymous_form.is_valid():
            self.anonymous_user_email = anonymous_form.cleaned_data['email']
            return True
        return False

    def save(self):
        self.storage['anonymous_user_email'] = self.anonymous_user_email
        self.storage['address'] = Address.objects.as_data(self.address)

    def add_to_order(self, order):
        self.address.save()
        order.anonymous_user_email = self.anonymous_user_email
        order.billing_address = self.address
        if order.user:
            User.objects.store_address(order.user, self.address, billing=True)

    def validate(self):
        super(BillingAddressStep, self).validate()
        if 'anonymous' in self.forms and not self.anonymous_user_email:
            raise InvalidData()


class ShippingStep(BaseAddressStep):
    template = 'checkout/shipping.html'
    title = _('Shipping Address')

    def __init__(self, request, storage, cart,
                 default_address=None):
        self.cart = cart
        address_data = storage.get('address', {})
        self.billing_address = default_address
        if not address_data and default_address:
            address = default_address
        else:
            address = Address(**address_data)
        super(ShippingStep, self).__init__(request, storage, address)
        delivery_choices = list(
            (m.name, m) for m in get_delivery_options_for_items(
                self.cart, address=address))
        selected_method_name = storage.get('delivery_method')
        selected_method = None
        for method_name, method in delivery_choices:
            if method_name == selected_method_name:
                selected_method = method
                break
        if selected_method is None:
            # TODO: find cheapest not first
            selected_method_name, selected_method = delivery_choices[0]
        self.delivery_method = selected_method
        self.forms['delivery'] = DeliveryForm(
            delivery_choices, request.POST or None,
            initial={'method': selected_method_name})
        self.shipping_same_as_billing = request.POST.get(
            'shipping_same_as_billing')

    def __str__(self):
        return 'shipping-address'

    def save(self):
        delivery_form = self.forms['delivery']
        if self.shipping_same_as_billing:
            address = self.billing_address
        else:
            address = self.address
        self.storage['address'] = Address.objects.as_data(address)
        delivery_method = delivery_form.cleaned_data['method']
        self.storage['delivery_method'] = delivery_method

    def validate(self):
        super(ShippingStep, self).validate()
        if 'delivery_method' not in self.storage:
            raise InvalidData()

    def forms_are_valid(self):
        base_forms_are_valid = super(ShippingStep, self).forms_are_valid()
        delivery_form = self.forms['delivery']
        if base_forms_are_valid and delivery_form.is_valid():
            return True
        return False

    def add_to_order(self, order):
        self.address.save()
        order.shipping_method = self.delivery_method.name
        order.shipping_address = self.address
        if order.user:
            User.objects.store_address(order.user, self.address, shipping=True)

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['delivery_form'] = self.forms['delivery']
        return super(ShippingStep, self).process(extra_context=context)


class SummaryStep(BaseCheckoutStep):
    template = 'checkout/summary.html'
    title = _('Summary')

    def __init__(self, request, storage, checkout):
        self.checkout = checkout
        super(SummaryStep, self).__init__(request, storage)

    def __str__(self):
        return 'summary'

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['all_steps_valid'] = self.forms_are_valid()
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
        next_step = self.checkout.get_next_step()
        return next_step == self

    def save(self):
        pass

    def add_to_order(self, order):
        order.save()
        if self.checkout.is_shipping_required():
            method = self.checkout.shipping.delivery_method
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
