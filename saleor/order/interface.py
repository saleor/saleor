from dataclasses import dataclass

from prices import TaxedMoney


@dataclass
class OrderTaxedPricesData:
    """Store an order prices data with applied taxes.

    'price_with_discounts' includes voucher discount and sale discount if any valid
    exists.
    'undiscounted_price' is a price without any sale and voucher.
    """

    undiscounted_price: TaxedMoney
    price_with_discounts: TaxedMoney
