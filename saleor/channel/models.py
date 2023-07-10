from datetime import timedelta

from django.conf import settings
from django.db import models
from django_countries.fields import CountryField

from ..core.models import ModelWithMetadata
from ..permission.enums import ChannelPermissions
from . import AllocationStrategy, MarkAsPaidStrategy, TransactionFlowStrategy


class Channel(ModelWithMetadata):
    name = models.CharField(max_length=250)
    is_active = models.BooleanField(default=False)
    slug = models.SlugField(max_length=255, unique=True)
    currency_code = models.CharField(max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH)
    default_country = CountryField()
    allocation_strategy = models.CharField(
        max_length=255,
        choices=AllocationStrategy.CHOICES,
        default=AllocationStrategy.PRIORITIZE_SORTING_ORDER,
    )
    order_mark_as_paid_strategy = models.CharField(
        max_length=255,
        choices=MarkAsPaidStrategy.CHOICES,
        default=MarkAsPaidStrategy.PAYMENT_FLOW,
    )

    default_transaction_flow_strategy = models.CharField(
        max_length=255,
        choices=TransactionFlowStrategy.CHOICES,
        default=TransactionFlowStrategy.CHARGE,
    )

    automatically_confirm_all_new_orders = models.BooleanField(default=True, null=True)
    automatically_fulfill_non_shippable_gift_card = models.BooleanField(
        default=True,
        null=True,
    )
    expire_orders_after = models.IntegerField(default=None, null=True, blank=True)

    delete_expired_orders_after = models.DurationField(
        default=timedelta(days=60),
    )

    class Meta(ModelWithMetadata.Meta):
        ordering = ("slug",)
        app_label = "channel"
        permissions = (
            (
                ChannelPermissions.MANAGE_CHANNELS.codename,
                "Manage channels.",
            ),
        )

    def __str__(self):
        return self.slug
