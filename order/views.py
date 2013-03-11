from .forms import ManagementForm
from cart import (get_cart_from_request, remove_cart_from_request,
                  CartPartitioner)
from django.db import models
from django.forms.models import model_to_dict
from django.http.response import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from order.models import Order
from satchless.process import Step, ProcessManager, InvalidData
from userprofile.forms import AddressForm, UserAddressesForm


class CheckoutProcessManager(ProcessManager):

    def __init__(self, order, request):
        self.order = order
        self.request = request

    def __iter__(self):
        yield BillingAddressStep(self.order, self.request)


class BillingAddressStep(Step):

    method = None
    instance = None
    forms = None
    template = 'order/address.html'

    def __init__(self, order, request):
        self.request = request
        self.order = order
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
        self.cleaned_data = {}
        if self.method == 'new' and self.forms['address'].is_valid():
            self.cleaned_data = self.forms['address'].cleaned_data
            self.instance = self.forms['address'].instance
            return
        elif self.method == 'select' and self.forms['address_list'].is_valid():
            self.instance = self.forms['address_list'].cleaned_data['address']
            self.cleaned_data = model_to_dict(
                self.instance, exclude=['id', 'user', 'alias'])
            return

        raise InvalidData()

    def save(self):
        self.order.set_billing_address(self.instance)
        self.order.save()

    def process(self):
        try:
            self.validate()
        except InvalidData:
            pass
        else:
            self.save()

        return TemplateResponse(self.request, self.template, {
            'forms': self.forms,
            'order': self.order
        })

    @models.permalink
    def get_absolute_url(self):
        return ('order:details', (),
                {'token': self.order.token, 'step': str(self)})


def index(request, token=None):
    try:
        order = Order.objects.get(token=token)
    except Order.DoesNotExist:
        cart = get_cart_from_request(request)
        if not cart:
            return redirect('cart:index')
        order = Order.objects.create_from_partitions(CartPartitioner(cart))
    remove_cart_from_request(request)
    checkout = CheckoutProcessManager(order, request)
    return redirect(checkout.get_next_step().get_absolute_url())


def details(request, token, step):
    order = get_object_or_404(Order, token=token)
    checkout = CheckoutProcessManager(order, request)
    try:
        step = checkout[step]
    except KeyError:
        raise Http404()
    return step.process()


