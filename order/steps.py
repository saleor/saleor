from . import Step
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from order.forms import ManagementForm, DigitalDeliveryForm, DeliveryForm
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

    template = 'order/shipping.html'
    delivery_method = None

    def __init__(self, order, request, group):
        if group.address:
            address = group.address
        else:
            address = order.billing_address or Address()
            address.id = None
        super(ShippingStep, self).__init__(order, request, address)
        self.forms['delivery'] = DeliveryForm(group, request.POST or None)
        self.group = group

    def __str__(self):
        return 'delivery-%s' % (self.group.id,)

    def __unicode__(self):
        return u'Shipping'

    def save(self):
        super(ShippingStep, self).save()
        self.group.address = self.address
        self.group.price = self.delivery_method.get_price_per_item()
        self.group.save()

    def validate(self):
        try:
            self.group.clean_fields()
        except ValidationError as e:
            raise InvalidData(e.messages)
        if not self.group.address:
            raise InvalidData()

    def forms_are_valid(self):
        base_forms_are_valid = super(ShippingStep, self).forms_are_valid()
        delivery_form = self.forms['delivery']
        if base_forms_are_valid and delivery_form.is_valid():
            self.delivery_method = delivery_form.cleaned_data['method']
            return True
        return False


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


class SummaryStep(Step):

    template = 'order/summary.html'

    def __str__(self):
        return 'summary'

    def __unicode__(self):
        return u'Summary'

    def validate(self):
        if self.order.status not in ('summary', 'completed'):
            raise InvalidData('Last step')

    def save(self):
        self.order.status = 'summary'
        self.order.save()


class SuccessStep(Step):

    def process(self):
        self.order.status = 'completed'
        self.order.save()
        messages.success(self.request, 'Your order was successfully processed')
        return redirect('home')

    def __str__(self):
        return 'success'

    def __unicode__(self):
        return u'Success'

    def validate(self):
        raise InvalidData('Last step')
