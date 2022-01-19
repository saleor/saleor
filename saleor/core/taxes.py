from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional, Union

from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models import Q
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from saleor.app.models import App
from saleor.webhook.event_types import WebhookEventSyncType

if TYPE_CHECKING:
    from saleor.plugins.manager import PluginsManager
    from saleor.product.models import Product, ProductType


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

DEFAULT_TAX_CODE = "O9999999"
DEFAULT_TAX_DESCRIPTION = "Unmapped Other SKU - taxable default"


def _get_current_tax_app() -> App:
    """Return currently used tax app or None, if there aren't any."""
    q_app_is_not_tax = ~(
        Q(webhooks__events__event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES)
        & Q(webhooks__events__event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES)
    )
    return (
        App.objects.order_by("pk")
        .filter(is_active=True)
        .exclude(q_app_is_not_tax)
        .last()
    )


def _get_meta_code_key(app: App) -> str:
    return f"{app.name}.code"


def _get_meta_description_key(app: App) -> str:
    return f"{app.name}.description"


def _get_cached_tax_codes_or_fetch(manager: "PluginsManager") -> List[TaxType]:
    if cached_tax_codes := cache.get(WEBHOOK_TAX_CODES_CACHE_KEY):
        return cached_tax_codes

    if sync_tax_codes := manager.get_tax_codes():
        cache.set(WEBHOOK_TAX_CODES_CACHE_KEY, sync_tax_codes)
        return sync_tax_codes
    return []


def fetch_tax_codes(manager: "PluginsManager") -> List[TaxType]:
    return (
        _get_cached_tax_codes_or_fetch(manager) or manager.get_tax_rate_type_choices()
    )


def _find_tax_description_by_tax_code(
    tax_types: List[TaxType],
    tax_code: str,
) -> Optional[str]:
    return next(
        (tax_type.description for tax_type in tax_types if tax_type.code == tax_code),
        None,
    )


def set_tax_code(
    manager: "PluginsManager",
    obj: Union["Product", "ProductType"],
    tax_code: Optional[str],
) -> None:
    if not (tax_app := _get_current_tax_app()):
        manager.assign_tax_code_to_object_meta(obj, tax_code)
        return

    meta_code_key = _get_meta_code_key(tax_app)
    meta_description_key = _get_meta_description_key(tax_app)

    if not tax_code:
        obj.delete_value_from_metadata(meta_code_key)
        obj.delete_value_from_metadata(meta_description_key)
        return

    if not (tax_codes := _get_cached_tax_codes_or_fetch(manager)):
        return

    if not (tax_description := _find_tax_description_by_tax_code(tax_codes, tax_code)):
        return

    tax_item = {
        meta_code_key: tax_code,
        meta_description_key: tax_description,
    }
    obj.store_value_in_metadata(items=tax_item)


def get_tax_code(
    manager: "PluginsManager", obj: Union["Product", "ProductType"]
) -> TaxType:
    if not (tax_app := _get_current_tax_app()):
        return manager.get_tax_code_from_object_meta(obj)

    meta_code_key = _get_meta_code_key(tax_app)
    meta_description_key = _get_meta_description_key(tax_app)

    code = obj.get_value_from_metadata(meta_code_key, DEFAULT_TAX_CODE)
    description = obj.get_value_from_metadata(
        meta_description_key, DEFAULT_TAX_DESCRIPTION
    )

    return TaxType(
        code=code,
        description=description,
    )
