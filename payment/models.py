from django.db import models
from order.models import Order
from payments.models import BasePayment


class Payment(BasePayment):

    order = models.ForeignKey(Order, related_name='payments')
