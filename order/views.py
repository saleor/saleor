from .forms import ManagementForm
from cart import (get_cart_from_request, remove_cart_from_request,
                  CartPartitioner)
from django.forms.models import model_to_dict
from django.http.response import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from order.models import Order
from userprofile.forms import AddressForm, UserAddressesForm
from satchless.process import Step, ProcessManager, InvalidData
from django.db import models


class BillingAddressStep(Step):

    def __init__(self, order, request):
        self.manager = BillingFormManager(request,
                                          instance=order.get_billing_address())
        self.order = order

    def __str__(self):
        return 'billing-address'

    def validate(self):
        if not self.manager.is_valid():
            raise InvalidData()

    def save(self):
        self.order.set_billing_address(self.manager.instance)
        self.order.save()

    @models.permalink
    def get_absolute_url(self):
        return ('order:details', (), {'token': self.order.token, 'step':str(self)})

class CheckoutProcessManager(ProcessManager):

    steps = []

    def __init__(self, order, request):
        self.steps.append(BillingAddressStep(order, request))

    def __iter__(self):
        return iter(self.steps)


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


def index(request, token=None):
    cart = get_cart_from_request(request)
    if not cart:
        return redirect('cart:index')
    order = Order.objects.create_from_partitions(CartPartitioner(cart))
    remove_cart_from_request(request)

    checkout = CheckoutProcessManager(order, request)

    return redirect(checkout.get_next_step().get_absolute_url())


def details(request, token, step):
    try:
        order = Order.objects.get(token=token)
    except Order.DoesNotExist:
        raise Http404()

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
