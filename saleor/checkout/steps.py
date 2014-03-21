from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.shortcuts import redirect
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from satchless.process import InvalidData

from .forms import DigitalDeliveryForm, DeliveryForm
from ..checkout.forms import AnonymousEmailForm
from ..core.utils import BaseStep
from ..delivery import get_delivery_choices_for_group
from ..order.models import DigitalDeliveryGroup, ShippedDeliveryGroup
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
        if address:
            self.address = Address(**address)
        else:
            self.address = Address()
        existing_selected = False
        address_form = AddressForm(request.POST or None, instance=self.address)
        if request.user.is_authenticated():
            address_book = list(request.user.address_book.all())
            for entry in address_book:
                data = Address.objects.as_data(entry.address)
                instance = Address(**data)
                entry.form = AddressForm(instance=instance)
                entry.is_selected = Address.objects.are_identical(
                    entry.address, self.address)
                if entry.is_selected:
                    existing_selected = True
        else:
            address_book = []
        self.existing_selected = existing_selected
        self.forms = {'address': address_form}
        self.address_book = address_book

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
        context['address_book'] = self.address_book
        context['existing_address_selected'] = self.existing_selected
        return super(BaseAddressStep, self).process(extra_context=context)


class BillingAddressStep(BaseAddressStep):

    template = 'checkout/billing.html'
    title = _('Billing Address')

    def __init__(self, request, storage):
        address = storage.get('address')
        skip = False
        if not address and request.user.is_authenticated():
            if request.user.default_billing_address:
                address = request.user.default_billing_address.address
                skip = True
            elif request.user.address_book.count() == 1:
                address = request.user.address_book.all()[0].address
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
        order.save()
        if order.user:
            alias = '%s, %s' % (order, self)
            User.objects.store_address(order.user, self.address, alias,
                                       billing=True)

    def validate(self):
        super(BillingAddressStep, self).validate()
        if 'anonymous' in self.forms and not self.anonymous_user_email:
            raise InvalidData()


class ShippingStep(BaseAddressStep):

    template = 'checkout/shipping.html'
    title = _('Shipping Details')

    def __init__(self, request, storage, purchased_items, _id=None,
                 default_address=None):
        self.id = _id
        address_data = storage.get('address', default_address)
        if address_data is None:
            address_data = {}
        address = Address(**address_data)
        super(ShippingStep, self).__init__(request, storage, address_data)
        delivery_choices = list(
            get_delivery_choices_for_group(purchased_items, address=address))
        selected_delivery_name = storage.get('delivery_method')
        # TODO: find cheapest not first
        (selected_delivery_group_name,
         selected_delivery_group) = delivery_choices[0]
        for delivery_name, delivery in delivery_choices:
            if delivery_name == selected_delivery_name:
                selected_delivery_group = delivery
                selected_delivery_group_name = delivery_name
                break
        self.group = selected_delivery_group
        self.forms['delivery'] = DeliveryForm(
            delivery_choices, request.POST or None,
            initial={'method': selected_delivery_group_name})

    def __str__(self):
        return 'delivery-%s' % (self.id,)

    def save(self):
        delivery_form = self.forms['delivery']
        self.storage['address'] = Address.objects.as_data(self.address)
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
        group = ShippedDeliveryGroup.objects.create(
            order=order, address=self.address,
            price=self.group.get_delivery_total(),
            method=smart_text(self.group))
        group.add_items_from_partition(self.group)
        if order.user:
            alias = '%s, %s' % (order, self)
            User.objects.store_address(order.user, self.address, alias,
                                       shipping=True)

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['items'] = self.group
        context['delivery_form'] = self.forms['delivery']
        return super(ShippingStep, self).process(extra_context=context)


class DigitalDeliveryStep(BaseCheckoutStep):

    template = 'checkout/digitaldelivery.html'
    title = _('Digital Delivery')

    def __init__(self, request, storage, items_group=None, _id=None):
        super(DigitalDeliveryStep, self).__init__(request, storage)
        self.id = _id
        self.forms['email'] = DigitalDeliveryForm(request.POST or None,
                                                  initial=self.storage,
                                                  user=request.user)
        email = self.storage.get('email')
        delivery_choices = list(
            get_delivery_choices_for_group(items_group, email=email))
        selected_delivery_group = delivery_choices[0][1]
        self.storage['delivery_method'] = selected_delivery_group
        self.group = selected_delivery_group

    def __str__(self):
        return 'digital-delivery-%s' % (self.id,)

    def validate(self):
        if not 'email' in self.storage:
            raise InvalidData()

    def save(self):
        self.storage.update(self.forms['email'].cleaned_data)

    def add_to_order(self, order):
        group = DigitalDeliveryGroup.objects.create(
            order=order, email=self.storage['email'],
            price=self.group.get_delivery_total(),
            method=smart_text(self.group))
        group.add_items_from_partition(self.group)

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['form'] = self.forms['email']
        context['items'] = self.group
        return super(DigitalDeliveryStep, self).process(extra_context=context)


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
                order.send_confirmation_email()
            return redirect('order:details', token=order.token)
        return response

    def validate(self):
        raise InvalidData()

    def forms_are_valid(self):
        next_step = self.checkout.get_next_step()
        return next_step == self

    def save(self):
        pass

    def add_to_order(self, _order):
        self.checkout.clear_storage()
