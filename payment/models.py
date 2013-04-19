from django.core.urlresolvers import reverse
from django.db import models
from order.models import Order
from payments.models import BasePayment


class Payment(BasePayment):

    order = models.ForeignKey(Order, related_name='payments')

    def get_cancel_url(self):
        return reverse('order:payment:index', kwargs={'token':
                                                      self.order.token})

    def get_success_url(self):
        return reverse('order:success', kwargs={'token': self.order.token})
