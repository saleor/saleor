from .forms import ManagementForm, DigitalDeliveryForm, DeliveryForm
from checkout.forms import AnonymousEmailForm
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import redirect
from order.models import DigitalDeliveryGroup, ShippedDeliveryGroup
from saleor.utils import BaseStep
from satchless.process import InvalidData
from userprofile.forms import AddressForm, UserAddressesForm
from userprofile.models import Address


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
        context = extra_context or {}
        context['checkout'] = self.checkout
        return super(BaseCheckoutStep, self).process(extra_context=context)


class BaseShippingStep(BaseCheckoutStep):

    method = None
    address = None
    template = 'checkout/address.html'

    def __init__(self, checkout, request, address):
        super(BaseShippingStep, self).__init__(checkout, request)
        self.address = address
        self.forms = {
            'management': ManagementForm(request.user.is_authenticated(),
                                        request.POST or None),
            'address_list': UserAddressesForm(user=request.user),
            'address': AddressForm(instance=self.address)}
        management_form = self.forms['management']
        if management_form.is_valid():
            self.method = management_form.cleaned_data['choice_method']
            if self.method == 'new':
                self.forms['address'] = AddressForm(request.POST,
                                                    instance=self.address)
            elif self.method == 'select':
                self.forms['address_list'] = UserAddressesForm(request.POST,
                                                           user=request.user)

    def forms_are_valid(self):
        self.cleaned_data = {}
        if self.method == 'new' and self.forms['address'].is_valid():
            return True
        elif self.method == 'select' and self.forms['address_list'].is_valid():
            address_book = self.forms['address_list'].cleaned_data['address']
            address_book.address.id = None
            self.address = address_book.address
            return True
        return False

    def validate(self):
        try:
            self.address.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)


class BillingAddressStep(BaseShippingStep):

    template = 'checkout/billing.html'
    anonymous_user_email = ''

    def __init__(self, checkout, request):
        address = checkout.billing_address or Address()
        super(BillingAddressStep, self).__init__(checkout, request, address)
        if not request.user.is_authenticated():
            self.anonymous_user_email = self.checkout.anonymous_user_email
            initial = {'email': self.anonymous_user_email}
            self.forms['anonymous'] = AnonymousEmailForm(request.POST or None,
                                                         initial=initial)

    def __str__(self):
        return 'billing-address'

    def __unicode__(self):
        return u'Billing Address'

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

    def validate(self):
        super(BillingAddressStep, self).validate()
        if 'anonymous' in self.forms and not self.anonymous_user_email:
            raise InvalidData()


class ShippingStep(BaseShippingStep):

    template = 'checkout/shipping.html'
    delivery_method = None

    def __init__(self, checkout, request, delivery_group, _id=None):
        self.id = _id
        self.group = checkout.get_group(str(self))
        self.delivery_group = delivery_group
        if 'address' in self.group:
            address = self.group['address']
        else:
            address = checkout.billing_address or Address()
            address.id = None
        super(ShippingStep, self).__init__(checkout, request, address)
        self.forms['delivery'] = DeliveryForm(
            delivery_group.get_delivery_methods(), request.POST or None)

    def __str__(self):
        if self.id:
            return 'delivery-%s' % (self.id,)
        return 'delivery'

    def __unicode__(self):
        return u'Shipping'

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
            price=delivery_method.get_price())
        group.add_items_from_partition(self.delivery_group)


class DigitalDeliveryStep(BaseCheckoutStep):

    template = 'checkout/digitaldelivery.html'

    def __init__(self, checkout, request, delivery_group=None, _id=None):
        super(DigitalDeliveryStep, self).__init__(checkout, request)
        self.id = _id
        self.delivery_group = delivery_group
        self.group = checkout.get_group(str(self))
        self.forms['email'] = DigitalDeliveryForm(request.POST or None,
                                                  initial=self.group)
        delivery_methods = list(delivery_group.get_delivery_methods())
        self.group['delivery_method'] = delivery_methods[0]

    def __str__(self):
        if self.id:
            return 'digital-delivery-%s' % (self.id,)
        return 'delivery'

    def __unicode__(self):
        return u'Digital delivery'

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
            price=delivery_method.get_price())
        group.add_items_from_partition(self.delivery_group)


class SummaryStep(BaseCheckoutStep):

    template = 'checkout/summary.html'

    def __str__(self):
        return 'summary'

    def __unicode__(self):
        return u'Summary'

    def process(self, extra_context=None):
        response = super(SummaryStep, self).process(extra_context)
        if not response:
            order = self.checkout.create_order()
            return redirect('order:payment:index', token=order.token)
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


class PaymentStep(BaseCheckoutStep):

    def __str__(self):
        return 'payment'

    def __unicode__(self):
        return u'Payment'

    def validate(self):
        raise InvalidData('Redirect to peyment')

    def add_to_order(self, order):
        pass

    def save(self):
        pass
