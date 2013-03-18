from . import Step
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from order.forms import ManagementForm, DigitalDeliveryForm
from satchless.process import InvalidData
from userprofile.forms import AddressForm, UserAddressesForm
from userprofile.models import Address


class BaseShippingStep(Step):

    method = None
    address = None
    template = 'order/address.html'

    def __init__(self, order, request, address):
        super(BaseShippingStep, self).__init__(order, request)
        self.address = address
        self.forms = {
            'managment': ManagementForm(request.user.is_authenticated(),
                                        request.POST or None),
            'address_list': UserAddressesForm(user=request.user),
            'address': AddressForm(instance=self.address)}
        if self.forms['managment'].is_valid():
            self.method = self.forms['managment'].cleaned_data['choice_method']
            if self.method == 'new':
                self.forms['address'] = AddressForm(request.POST,
                                                    instance=self.address)
            elif self.method == 'select':
                self.forms['address_list'] = UserAddressesForm(request.POST,
                                                           user=request.user)
            else:
                raise ValueError(self.method)

    def forms_are_valid(self):
        self.cleaned_data = {}
        if self.method == 'new' and self.forms['address'].is_valid():
            self.address = self.forms['address'].instance
            return True
        elif self.method == 'select' and self.forms['address_list'].is_valid():
            address_book = self.forms['address_list'].cleaned_data['address']
            address_book.address.id = self.address.id
            self.address = address_book.address
            return True
        return False

    def save(self):
        self.address.save()


class BillingAddressStep(BaseShippingStep):

    def __init__(self, order, request):
        address = order.billing_address or Address()
        super(BillingAddressStep, self).__init__(order, request, address)

    def __str__(self):
        return 'billing-address'

    def __unicode__(self):
        return u'Billing Address'

    def save(self):
        super(BillingAddressStep, self).save()
        self.order.billing_address = self.address
        self.order.save()

    def validate(self):
        try:
            self.address.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)


class ShippingStep(BaseShippingStep):

    def __init__(self, order, request, group):
        if group.address:
            address = group.address
        else:
            address = order.billing_address or Address()
            address.id = None
        super(ShippingStep, self).__init__(order, request, address)
        self.group = group

    def __str__(self):
        return 'delivery-%s' % (self.group.id,)

    def __unicode__(self):
        return u'Shipping'

    def save(self):
        super(ShippingStep, self).save()
        self.group.address = self.address
        self.group.save()

    def validate(self):
        try:
            self.group.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)
        if not self.group.address:
            raise InvalidData()


class DigitalDeliveryStep(Step):

    template = 'order/digitaldelivery.html'

    def __init__(self, order, request, group):
        super(DigitalDeliveryStep, self).__init__(order, request)
        self.group = group
        self.forms['email'] = DigitalDeliveryForm(request.POST or None,
                                                  instance=self.group)

    def __str__(self):
        return 'digital-delivery-%s' % (self.group.id,)

    def __unicode__(self):
        return u'Digital delivery'

    def validate(self):
        try:
            self.group.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)
        if not self.group.email:
            raise InvalidData()

    def save(self):
        self.group.save()


class SuccessStep(Step):

    def process(self):
        self.order.status = 'completed'
        self.order.save()
        messages.success(self.request, 'Your order was successfully processed')
        return redirect('home')

    def __str__(self):
        return 'summary'

    def __unicode__(self):
        return u'Summary'

    def validate(self):
        raise InvalidData('Last step')
