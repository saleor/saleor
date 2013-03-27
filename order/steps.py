from django.contrib import messages
from django.db import models
from django.shortcuts import redirect
from payment.forms import PaymentForm
from saleor.utils import BaseStep
from satchless.process import InvalidData, ProcessManager


class OrderProcessManager(ProcessManager):

    def __init__(self, order, request):
        self.steps = [PaymentStep(order, request)]

    def __iter__(self):
        return iter(self.steps)


class BaseOrderStep(BaseStep):

    def __init__(self, order, request):
        super(BaseOrderStep, self).__init__(request)
        self.order = order

    @models.permalink
    def get_absolute_url(self):
        return ('order:details', (), {'token': self.order.token,
                                      'step': str(self)})


class PaymentStep(BaseOrderStep):

    template = 'order/payment.html'

    def __init__(self, order, request):
        super(PaymentStep, self).__init__(order, request)
        self.forms['payment'] = PaymentForm(request.POST or None)

    def __str__(self):
        return 'payment'

    def __unicode__(self):
        return u'Payment'

    def process(self):
        response = super(PaymentForm, self).process()
        if not response:
            self.order.save()
            messages.success(self.request,
                             'Your order was successfully processed')
            return redirect('home')
        return response

    def validate(self):
        if not self.order.status == 'payment-pending':
            raise InvalidData()

    def save(self):
        self.order.status = 'payment-pending'
        self.order.save()

