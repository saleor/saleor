from .forms import ManagementForm
from cart import get_cart_from_request, CartPartitioner
from django.forms.models import model_to_dict
from django.template.response import TemplateResponse
from order import get_order_from_request
from userprofile.forms import AddressForm, UserAddressesForm


class BillingFormManager(object):

    method = None

    def __init__(self, request, instance=None):
        self.instance = instance
        self.managment_form = ManagementForm(request.user.is_authenticated(),
                                             request.POST or None)
        self.address_list_form = UserAddressesForm(user=request.user)
        self.address_form = AddressForm(instance=instance)

        if self.managment_form.is_valid():
            self.method = self.managment_form.cleaned_data['choice_method']

            if self.method == 'new':
                self.address_form = AddressForm(request.POST,
                                                instance=instance)
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
                self.instance = self.address_form.instance
                return True
            elif self.method == 'select' and self.address_list_form.is_valid():
                self.instance = self.address_list_form.cleaned_data['address']
                self.cleaned_data = model_to_dict(self.instance,
                                                  exclude=['id', 'user',
                                                           'alias'])
                return True

        return False


def billing_address(request):
    cart = get_cart_from_request(request)
    order = get_order_from_request(request, CartPartitioner(cart))
    manager = BillingFormManager(request, instance=order.get_billing_address())

    if manager.is_valid():
        order.set_billing_address(manager.instance)
        order.save()

    return TemplateResponse(request, 'order/address.html', {
        'managment_form': manager.managment_form,
        'address_list_form': manager.address_list_form,
        'address_form': manager.address_form,
        'order': order
    })
