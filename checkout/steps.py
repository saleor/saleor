from . import Step
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from order.forms import ManagementForm, DigitalDeliveryForm, DeliveryForm
from cart import DigitalGroup
from satchless.process import InvalidData, ProcessManager
from userprofile.forms import AddressForm, UserAddressesForm
from userprofile.models import Address


class CheckoutProcessManager(ProcessManager):

    def __init__(self, cart_partitions, checkout, request):
        self.steps = [BillingAddressStep(checkout, request)]
        for index, delivery_group in enumerate(cart_partitions):
            step_class = ShippingStep
            if isinstance(delivery_group, DigitalGroup):
                step_class = DigitalDeliveryStep
            step = step_class(checkout, request,
                              delivery_group.get_delivery_methods(), index)
            self.steps.append(step)
        self.steps.append(SummaryStep(checkout, request))
        self.steps.append(SuccessStep(checkout, request))

    def __iter__(self):
        return iter(self.steps)


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


class ShippingStep(BaseShippingStep):

    template = 'checkout/shipping.html'
    delivery_method = None

    def __init__(self, checkout, request, delivery_methods=None, _id=None):
        self.id = _id
        self.group = checkout.get_group(str(self))
        if 'address' in self.group:
            address = self.group['address']
        else:
            address = checkout.billing_address or Address()
        super(ShippingStep, self).__init__(checkout, request, address)
        self.forms['delivery'] = DeliveryForm(delivery_methods,
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
        self.group['delivery_method'] = delivery_form.clean_data['method']
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


class DigitalDeliveryStep(Step):

    template = 'checkout/digitaldelivery.html'

    def __init__(self, checkout, request, delivery_methods=None, _id=None):
        super(DigitalDeliveryStep, self).__init__(checkout, request)
        self.id = _id
        self.group = checkout.get_group(str(self))
        self.forms['email'] = DigitalDeliveryForm(request.POST or None,
                                                  initial=self.group)

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
        self.group = self.forms['email'].cleaned_data
        self.checkout.save()


class SummaryStep(Step):

    template = 'checkout/summary.html'

    def __str__(self):
        return 'summary'

    def __unicode__(self):
        return u'Summary'

    def validate(self):
        raise InvalidData('Last step')

    def save(self):
        pass


class SuccessStep(Step):

    def process(self):
        self.checkout.status = 'completed'
        self.checkout.save()
        messages.success(self.request, 'Your order was successfully processed')
        return redirect('home')

    def __str__(self):
        return 'success'

    def __unicode__(self):
        return u'Payment'

    def validate(self):
        raise InvalidData('Redirect to peyment')
