from communication.mail import send_email
from django.core.urlresolvers import reverse
from django.db import models
from order.models import Order
from payments.models import BasePayment
from saleor.utils import build_absolute_uri


class Payment(BasePayment):

    order = models.ForeignKey(Order, related_name='payments')

    def get_cancel_url(self):
        return build_absolute_uri(
            reverse('order:payment:index', kwargs={'token': self.order.token}))

    def get_success_url(self):
        return build_absolute_uri(
            reverse('order:success', kwargs={'token': self.order.token}))

    def send_confirmation_email(self):
        email = self.order.get_user_email()
        order_url = build_absolute_uri(
            reverse('order:details', kwargs={'token': self.order.token}))
        context = {'order_url': order_url}
        send_email(email, 'payment/emails/confirm_email.txt', context)
