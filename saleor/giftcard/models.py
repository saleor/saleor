import os

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import JSONField, Q
from django.utils import timezone
from django_prices.models import MoneyField

from ..app.models import App
from ..core.models import ModelWithMetadata
from ..core.utils.json_serializer import CustomJsonEncoder
from ..permission.enums import GiftcardPermissions
from . import GiftCardEvents


class GiftCardTag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ("name",)
        indexes = [
            GinIndex(
                name="gift_card_tag_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            ),
        ]


class GiftCardQueryset(models.QuerySet):
    def active(self, date):
        return self.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=date),
            is_active=True,
        )


GiftCardManager = models.Manager.from_queryset(GiftCardQueryset)


class GiftCard(ModelWithMetadata):
    code = models.CharField(
        max_length=16, unique=True, validators=[MinLengthValidator(8)], db_index=True
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="gift_cards",
    )
    created_by_email = models.EmailField(null=True, blank=True)
    used_by_email = models.EmailField(null=True, blank=True)
    app = models.ForeignKey(
        App,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    expiry_date = models.DateField(null=True, blank=True)

    tags = models.ManyToManyField(GiftCardTag, "gift_cards")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_used_on = models.DateTimeField(null=True, blank=True)
    product = models.ForeignKey(
        "product.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="gift_cards",
    )
    fulfillment_line = models.ForeignKey(
        "order.FulfillmentLine",
        related_name="gift_cards",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
        default=os.environ.get("DEFAULT_CURRENCY", "USD"),
    )

    initial_balance_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    initial_balance = MoneyField(
        amount_field="initial_balance_amount", currency_field="currency"
    )

    current_balance_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    current_balance = MoneyField(
        amount_field="current_balance_amount", currency_field="currency"
    )

    objects = GiftCardManager()

    class Meta(ModelWithMetadata.Meta):
        ordering = ("code",)
        permissions = (
            (GiftcardPermissions.MANAGE_GIFT_CARD.codename, "Manage gift cards."),
        )

    @property
    def display_code(self):
        return self.code[-4:]


class GiftCardEvent(models.Model):
    date = models.DateTimeField(default=timezone.now, editable=False)
    type = models.CharField(max_length=255, choices=GiftCardEvents.CHOICES)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="gift_card_events",
        on_delete=models.SET_NULL,
        null=True,
    )
    app = models.ForeignKey(
        App, related_name="gift_card_events", on_delete=models.SET_NULL, null=True
    )
    order = models.ForeignKey("order.Order", null=True, on_delete=models.SET_NULL)
    gift_card = models.ForeignKey(
        GiftCard, related_name="events", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("date",)
