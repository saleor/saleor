from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now

from .. import OrderEvents
from ...core.utils.json_serializer import CustomJsonEncoder
from ...order.models import Order


class OrderEvent(models.Model):
    """Model used to store events that happened during the order lifecycle.

    Args:
        parameters: Values needed to display the event on the storefront
        type: Type of an order
    """

    date = models.DateTimeField(default=now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=[(
            type_name.upper(), type_name)
            for type_name, _ in OrderEvents.CHOICES])
    order = models.ForeignKey(
        Order, related_name='events', on_delete=models.CASCADE)
    parameters = JSONField(
        blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ('date', )

    def __repr__(self):
        return 'OrderEvent(type=%r, user=%r)' % (self.type, self.user)
