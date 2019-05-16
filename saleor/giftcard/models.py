from datetime import date

from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy
from django_prices.models import MoneyField


class GiftCard(models.Model):
    code = models.CharField(max_length=16, unique=True, db_index=True)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="gift_cards",
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL
    )
    created = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(default=date.today)
    expiration_date = models.DateField(null=True, blank=True)
    last_used_on = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    initial_balance = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    current_balance = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )

    class Meta:
        permissions = (
            (
                "manage_gift_card",
                pgettext_lazy("Permission description", "Manage gift cards."),
            ),
        )
