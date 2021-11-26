from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from ...core.taxes import TaxData, TaxLineData
from ...plugins.base_plugin import BasePlugin

if TYPE_CHECKING:
    from ..models import Checkout


class SampleTaxPlugin(BasePlugin):
    def get_taxes_for_checkout(
        self, checkout: "Checkout", previous_value
    ) -> Optional["TaxData"]:
        currency = checkout.currency
        tax = Decimal("1.23")
        tax_lines = [
            TaxLineData(
                id=line.variant_id,
                currency=currency,
                unit_net_amount=line.unit_price_net_amount,
                unit_gross_amount=line.unit_price_gross_amount * tax,
                total_net_amount=line.total_price_net_amount,
                total_gross_amount=line.total_price_gross_amount * tax,
            )
            for line in checkout.lines.all()
        ]
        return TaxData(
            currency=currency,
            total_net_amount=checkout.total_net_amount,
            total_gross_amount=checkout.total_gross_amount * tax,
            subtotal_net_amount=checkout.subtotal_net_amount,
            subtotal_gross_amount=checkout.subtotal_gross_amount * tax,
            shipping_price_net_amount=checkout.shipping_price_net_amount,
            shipping_price_gross_amount=checkout.shipping_price_gross_amount * tax,
            lines=tax_lines,
        )
