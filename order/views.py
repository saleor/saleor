from django.template.response import TemplateResponse
from . import get_order_from_request
from .forms import ManagementForm
from userprofile.forms import AddressForm, UserAddressesForm
from django.forms.models import model_to_dict


class BillingFormManager(object):

    method = None

    def __init__(self, request):
        self.managment_form = ManagementForm(request.POST or None)
        self.address_list_form = UserAddressesForm(user=request.user)
        self.address_form = AddressForm()

        if self.managment_form.is_valid():
            self.method = self.managment_form.cleaned_data['choice_method']

            if self.method == 'new':
                self.address_form = AddressForm(request.POST)
            elif self.method == 'select':
                self.address_list_form = UserAddressesForm(request.POST,
                                                           user=request.user)
            else:
                raise ValueError(self.method)

    def is_valid(self):
        self.cleaned_data = {}
        if self.method:
            if self.method == 'new' and self.address_form.is_valid():
                self.cleaned_data = self.address_form.cleaned_data
                return True
            elif self.method == 'select' and self.address_list_form.is_valid():
                address = self.address_list_form.cleaned_data['address']
                self.cleaned_data = model_to_dict(
                                      address,exclude=['id', 'user', 'alias'])
                return True

        return False


def billing_address(request):
    order = get_order_from_request(request)

    manager = BillingFormManager(request)

    if manager.is_valid():
        print manager.cleaned_data


    return TemplateResponse(request, 'order/address.html', {
        'order': order,
        'managment_form': manager.managment_form,
        'address_list_form': manager.address_list_form,
        'address_form': manager.address_form
    })
