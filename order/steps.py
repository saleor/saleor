from . import Step
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from order.forms import ManagementForm
from satchless.process import InvalidData
from userprofile.forms import AddressForm, UserAddressesForm


class BillingAddressStep(Step):

    method = None
    instance = None
    template = 'order/address.html'

    def __init__(self, order, request):
        super(BillingAddressStep, self).__init__(order, request)
        self.instance = order.get_billing_address()
        self.forms = {
            'managment': ManagementForm(request.user.is_authenticated(),
                                        request.POST or None),
            'address_list': UserAddressesForm(user=request.user),
            'address': AddressForm(instance=self.instance)}
        if self.forms['managment'].is_valid():
            self.method = self.forms['managment'].cleaned_data['choice_method']
            if self.method == 'new':
                self.forms['address'] = AddressForm(request.POST,
                                                    instance=self.instance)
            elif self.method == 'select':
                self.forms['address_list'] = UserAddressesForm(request.POST,
                                                           user=request.user)
            else:
                raise ValueError(self.method)

    def __str__(self):
        return 'billing-address'

    def validate(self):
        try:
            self.instance.full_clean(exclude=['user'])
        except ValidationError as e:
            raise InvalidData(e.messages)

    def forms_are_valid(self):
        self.cleaned_data = {}
        if self.method == 'new' and self.forms['address'].is_valid():
            self.instance = self.forms['address'].instance
            self.validate()
            return True
        elif self.method == 'select' and self.forms['address_list'].is_valid():
            self.instance = self.forms['address_list'].cleaned_data['address']
            self.validate()
            return True
        return False

    def save(self):
        self.order.set_billing_address(self.instance)
        self.order.save()


class SuccessStep(Step):

    def process(self):
        messages.success(self.request, 'Your order was successfully processed')
        return redirect('home')

    def __str__(self):
        return 'success'

    def validate(self):
        raise InvalidData('Last step')
