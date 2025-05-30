from typing import Any

from ...app.models import App
from ...core.taxes import TaxData, TaxLineData
from ..event_types import WebhookEventSyncType
from ..response_schemas.taxes import CalculateTaxesSchema

DEFAULT_TAX_CODE = "UNMAPPED"
DEFAULT_TAX_DESCRIPTION = "Unmapped Product/Product Type"


def get_current_tax_app() -> App | None:
    """Return currently used tax app or None, if there aren't any."""
    return (
        App.objects.order_by("pk")
        .filter(removed_at__isnull=True)
        .for_event_type(WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES)
        .for_event_type(WebhookEventSyncType.ORDER_CALCULATE_TAXES)
        .last()
    )


def parse_tax_data(
    response_data: Any,
    lines_count: int,
) -> TaxData:
    calculated_taxes_model = CalculateTaxesSchema.model_validate(
        response_data,
        context={"expected_line_count": lines_count},
    )
    return TaxData(
        shipping_price_gross_amount=calculated_taxes_model.shipping_price_gross_amount,
        shipping_price_net_amount=calculated_taxes_model.shipping_price_net_amount,
        shipping_tax_rate=calculated_taxes_model.shipping_tax_rate,
        lines=[
            TaxLineData(
                tax_rate=tax_line.tax_rate,
                total_gross_amount=tax_line.total_gross_amount,
                total_net_amount=tax_line.total_net_amount,
            )
            for tax_line in calculated_taxes_model.lines
        ],
    )
