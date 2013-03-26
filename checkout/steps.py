from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from order.forms import ManagementForm, DigitalDeliveryForm, DeliveryForm
from order.models import DigitalDeliveryGroup, ShippedDeliveryGroup
from satchless import process
from satchless.process import InvalidData
from userprofile.forms import AddressForm, UserAddressesForm
from userprofile.models import Address


class Step(process.Step):

    forms = None
    template = ''

    def __init__(self, checkout, request):
        self.forms = {}
        self.checkout = checkout
        self.request = request

    def __unicode__(self):
        return u'Step'

    def __nonzero__(self):
        try:
            self.validate()
        except InvalidData:
            return False
        return True

    def save(self):
        raise NotImplementedError()

    def forms_are_valid(self):
        for form in self.forms.values():
            if not form.is_valid():
                return False
        return True

    def validate(self):
        if not self.forms_are_valid():
            raise InvalidData()

    def process(self):
        if not self.forms_are_valid() or self.request.method == 'GET':
            return TemplateResponse(self.request, self.template, {
                'step': self
            })
        self.save()

    @models.permalink
    def get_absolute_url(self):
        return ('checkout:details', (), {'step': str(self)})

    def add_to_order(self, order):
        raise NotImplementedError()


class BaseShippingStep(Step):

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
        if self.forms['management'].is_valid():
            self.method = self.forms['management'].cleaned_data['choice_method']
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

    def __init__(self, checkout, request):
        address = checkout.billing_address or Address()
        super(BillingAddressStep, self).__init__(checkout, request, address)

    def __str__(self):
        return 'billing-address'

    def __unicode__(self):
        return u'Billing Address'

    def save(self):
        self.checkout.billing_address = self.address
        self.checkout.save()

    def add_to_order(self, order):
        self.address.save()
        order.billing_address = self.address
        order.save()


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
        super(ShippingStep, self).__init__(checkout, request, address)
        self.forms['delivery'] = DeliveryForm(delivery_group.get_delivery_methods(),
                                              request.POST or None)

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


class DigitalDeliveryStep(Step):

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


class SummaryStep(Step):

    template = 'checkout/summary.html'

    def __str__(self):
        return 'summary'

    def __unicode__(self):
        return u'Summary'

    def validate(self):
        if not self.checkout.storage['summary']:
            raise InvalidData()

    def save(self):
        self.checkout.storage['summary'] = True
        self.checkout.save()

    def add_to_order(self, order):
        order.status = 'summary'


class SuccessStep(Step):

    def process(self):
        self.checkout.create_order()
        messages.success(self.request, 'Your order was successfully processed')
        return redirect('home')

    def __str__(self):
        return 'success'

    def __unicode__(self):
        return u'Payment'

    def validate(self):
        raise InvalidData('Redirect to peyment')

    def add_to_order(self, order):
        self.checkout.clear_storage()
