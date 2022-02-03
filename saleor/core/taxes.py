from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Union

from django.contrib.sites.models import Site
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ..app.models import App
from ..webhook.event_types import WebhookEventSyncType


class TaxError(Exception):
    """Default tax error."""


def zero_money(currency: str) -> Money:
    """Return a money object set to zero.

    This is a function used as a model's default.
    """
    return Money(0, currency)


def zero_taxed_money(currency: str) -> TaxedMoney:
    zero = zero_money(currency)
    return TaxedMoney(net=zero, gross=zero)


def include_taxes_in_prices() -> bool:
    return Site.objects.get_current().settings.include_taxes_in_prices


def display_gross_prices() -> bool:
    return Site.objects.get_current().settings.display_gross_prices


def charge_taxes_on_shipping() -> bool:
    return Site.objects.get_current().settings.charge_taxes_on_shipping


def get_display_price(
    base: Union[TaxedMoney, TaxedMoneyRange], display_gross: bool = False
) -> Money:
    """Return the price amount that should be displayed based on settings."""
    if not display_gross:
        display_gross = display_gross_prices()
    if isinstance(base, TaxedMoneyRange):
        if display_gross:
            base = MoneyRange(start=base.start.gross, stop=base.stop.gross)
        else:
            base = MoneyRange(start=base.start.net, stop=base.stop.net)

    if isinstance(base, TaxedMoney):
        base = base.gross if display_gross else base.net
    return base


@dataclass(frozen=True)
class TaxType:
    """Dataclass for unifying tax type object that comes from tax gateway."""

    code: str
    description: str


@dataclass
class TaxLineData:
    id: int
    currency: str
    tax_rate: Decimal
    unit_net_amount: Decimal
    unit_gross_amount: Decimal
    total_gross_amount: Decimal
    total_net_amount: Decimal


@dataclass
class TaxData:
    currency: str
    total_net_amount: Decimal
    total_gross_amount: Decimal
    subtotal_net_amount: Decimal
    subtotal_gross_amount: Decimal
    shipping_price_gross_amount: Decimal
    shipping_price_net_amount: Decimal
    shipping_tax_rate: Decimal
    lines: List[TaxLineData]


WEBHOOK_TAX_CODES_CACHE_KEY = "webhook_tax_codes"

DEFAULT_TAX_CODE = "SA0000"
DEFAULT_TAX_DESCRIPTION = "Unmapped Product/Product Type"


def get_current_tax_app() -> Optional[App]:
    """Return currently used tax app or None, if there aren't any."""
    return (
        App.objects.order_by("pk")
        .for_event_type(WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES)
        .for_event_type(WebhookEventSyncType.ORDER_CALCULATE_TAXES)
        .for_event_type(WebhookEventSyncType.FETCH_TAX_CODES)
        .last()
    )


def get_meta_code_key(app: App) -> str:
    return f"{app.identifier}.code"


def get_meta_description_key(app: App) -> str:
    return f"{app.identifier}.description"
