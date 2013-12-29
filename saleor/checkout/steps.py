from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.shortcuts import redirect
from django.utils.encoding import smart_text
from satchless.process import InvalidData

from .forms import DigitalDeliveryForm, DeliveryForm
from ..checkout.forms import AnonymousEmailForm
from ..core.utils import BaseStep
from ..order.models import DigitalDeliveryGroup, ShippedDeliveryGroup
from ..userprofile.forms import AddressForm
from ..userprofile.models import Address, User


class BaseCheckoutStep(BaseStep):

    def __init__(self, checkout, request):
        super(BaseCheckoutStep, self).__init__(request)
        self.checkout = checkout

    @models.permalink
    def get_absolute_url(self):
        return ('checkout:details', (), {'step': str(self)})

    def add_to_order(self, order):
        raise NotImplementedError()

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['checkout'] = self.checkout
        return super(BaseCheckoutStep, self).process(extra_context=context)


class BaseAddressStep(BaseCheckoutStep):

    method = None
    address = None
    template = 'checkout/address.html'
    address_purpose = None

    def __init__(self, checkout, request, address):
        super(BaseAddressStep, self).__init__(checkout, request)
        if address:
            address_dict = Address.objects.as_data(address)
            self.address = Address(**address_dict)
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
        self.cleaned_data = {}
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
    anonymous_user_email = ''
    address_purpose = 'billing'

    def __init__(self, checkout, request):
        address = checkout.billing_address
        skip = False
        if not address and request.user.is_authenticated():
            if request.user.default_billing_address:
                address = request.user.default_billing_address.address
                skip = True
            elif request.user.address_book.count() == 1:
                address = request.user.address_book.all()[0].address
                skip = True
        super(BillingAddressStep, self).__init__(checkout, request, address)
        if not request.user.is_authenticated():
            self.anonymous_user_email = self.checkout.anonymous_user_email
            initial = {'email': self.anonymous_user_email}
            self.forms['anonymous'] = AnonymousEmailForm(request.POST or None,
                                                         initial=initial)
        if skip:
            self.save()

    def __str__(self):
        return 'billing-address'

    def __unicode__(self):
        return 'Billing Address'

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
        self.checkout.anonymous_user_email = self.anonymous_user_email
        self.checkout.billing_address = self.address
        self.checkout.save()

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
    delivery_method = None
    address_purpose = 'shipping'

    def __init__(self, checkout, request, delivery_group, _id=None):
        self.id = _id
        self.group = checkout.get_group(str(self))
        self.delivery_group = delivery_group
        if 'address' in self.group:
            address = self.group['address']
        else:
            address = checkout.billing_address
        super(ShippingStep, self).__init__(checkout, request, address)
        self.forms['delivery'] = DeliveryForm(
            delivery_group.get_delivery_methods(),
            data=request.POST or None,
            current_delivery_method=self.group.get('delivery_method'))

    def __str__(self):
        return 'delivery-%s' % (self.id,)

    def __unicode__(self):
        return 'Shipping'

    def save(self):
        delivery_form = self.forms['delivery']
        self.group['address'] = self.address
        self.group['delivery_method'] = delivery_form.cleaned_data['method']
        self.checkout.save()

    def validate(self):
        super(ShippingStep, self).validate()
        if 'delivery_method' not in self.group:
            raise InvalidData()

    def forms_are_valid(self):
        base_forms_are_valid = super(ShippingStep, self).forms_are_valid()
        delivery_form = self.forms['delivery']
        if base_forms_are_valid and delivery_form.is_valid():
            return True
        return False

    def add_to_order(self, order):
        self.address.save()
        delivery_method = self.group['delivery_method']
        group = ShippedDeliveryGroup.objects.create(
            order=order, address=self.address,
            price=delivery_method.get_price(),
            method=smart_text(delivery_method))
        group.add_items_from_partition(self.delivery_group)
        if order.user:
            alias = '%s, %s' % (order, self)
            User.objects.store_address(order.user, self.address, alias,
                                       shipping=True)

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['items'] = self.delivery_group
        context['delivery_form'] = self.forms['delivery']
        return super(ShippingStep, self).process(extra_context=context)


class DigitalDeliveryStep(BaseCheckoutStep):

    template = 'checkout/digitaldelivery.html'

    def __init__(self, checkout, request, delivery_group=None, _id=None):
        super(DigitalDeliveryStep, self).__init__(checkout, request)
        self.id = _id
        self.delivery_group = delivery_group
        self.group = checkout.get_group(str(self))
        self.forms['email'] = DigitalDeliveryForm(request.POST or None,
                                                  initial=self.group,
                                                  user=request.user)
        delivery_methods = list(delivery_group.get_delivery_methods())
        self.group['delivery_method'] = delivery_methods[0]

    def __str__(self):
        return 'digital-delivery-%s' % (self.id,)

    def __unicode__(self):
        return 'Digital delivery'

    def validate(self):
        if not 'email' in self.group:
            raise InvalidData()

    def save(self):
        self.group.update(self.forms['email'].cleaned_data)
        self.checkout.save()

    def add_to_order(self, order):
        delivery_method = self.group['delivery_method']
        group = DigitalDeliveryGroup.objects.create(
            order=order, email=self.group['email'],
            price=delivery_method.get_price(),
            method=smart_text(delivery_method))
        group.add_items_from_partition(self.delivery_group)

    def process(self, extra_context=None):
        context = dict(extra_context or {})
        context['form'] = self.forms['email']
        context['items'] = self.delivery_group
        return super(DigitalDeliveryStep, self).process(extra_context=context)


class SummaryStep(BaseCheckoutStep):

    template = 'checkout/summary.html'

    def __str__(self):
        return 'summary'

    def __unicode__(self):
        return 'Summary'

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
