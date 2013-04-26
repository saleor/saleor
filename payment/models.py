from communication.mail import send_email
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from order.models import Order
from payments.models import BasePayment
from saleor.utils import build_absolute_uri
from payments import PurchasedItem


class Payment(BasePayment):

    order = models.ForeignKey(Order, related_name='payments')

    def get_failure_url(self):
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

    def get_purchased_items(self):
        items = [PurchasedItem(name=item.product_name, quantity=item.quantity,
                             price=item.unit_price_gross, sku=item.product.sku,
                             currency=settings.SATCHLESS_DEFAULT_CURRENCY)
                 for item in self.order.get_items()]
        return items
