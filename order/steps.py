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

    def __init__(self, order, request):
        super(BaseShippingStep, self).__init__(order, request)
        self.address = order.billing_address or Address()
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

    def validate(self):
        try:
            self.address.full_clean()
        except ValidationError as e:
            raise InvalidData(e.messages)

    def forms_are_valid(self):
        self.cleaned_data = {}
        if self.method == 'new' and self.forms['address'].is_valid():
            self.address = self.forms['address'].instance
            self.validate()
            return True
        elif self.method == 'select' and self.forms['address_list'].is_valid():
            address_book = self.forms['address_list'].cleaned_data['address']
            self.address = address_book.address
            self.validate()
            return True
        return False

    def save(self):
        self.address.save()


class BillingAddressStep(BaseShippingStep):

    def __str__(self):
        return 'billing-address'

    def save(self):
        super(BillingAddressStep, self).save()
        self.order.billing_address = self.address
        self.order.save()


class ShippingStep(BaseShippingStep):

    def __init__(self, order, request, group):
        super(ShippingStep, self).__init__(order, request)
        self.group = group

    def __str__(self):
        return 'delivery-%s' % (self.group.id,)

    def save(self):
        super(ShippingStep, self).save()
        self.group.address = self.address
        self.group.save()


class DigitalDeliveryStep(Step):

    template = 'order/digitaldelivery.html'

    def __init__(self, order, request, group):
        super(DigitalDeliveryStep, self).__init__(order, request)
        self.group = group
        self.forms['email'] = DigitalDeliveryForm(request.POST or None,
                                                  instance=self.group)

    def __str__(self):
        return 'digital-delivery-%s' % (self.group.id,)

    def validate(self):
        try:
            self.group.full_clean()
        except ValidationError as e:
            raise InvalidData(e.messages)
        if not self.group.email:
            raise InvalidData()

    def save(self):
        self.group.save()


class SuccessStep(BaseShippingStep):

    def process(self):
        messages.success(self.request, 'Your order was successfully processed')
        return redirect('home')

    def __str__(self):
        return 'success'

    def validate(self):
        raise InvalidData('Last step')
