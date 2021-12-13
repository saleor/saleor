from dataclasses import dataclass

from prices import Money, TaxedMoney

from ..core.taxes import zero_money


@dataclass
class TaxedPricesData:
    undiscounted_price: TaxedMoney
    price_with_voucher: TaxedMoney
    price: TaxedMoney

    def sale_amount(self, tax_included: bool) -> Money:
        if tax_included:
            return max(
                self.undiscounted_price.gross - self.price.gross,
                zero_money(self.price.currency),
            )
        return max(
            self.undiscounted_price.net - self.price.net,
            zero_money(self.price.currency),
        )

    def voucher_amount(self, tax_included: bool) -> Money:
        if tax_included:
            return max(
                self.price.gross - self.price_with_voucher.gross,
                zero_money(self.price.currency),
            )
        return max(
            self.price.net - self.price_with_voucher.net,
            zero_money(self.price.currency),
        )


@dataclass
class PricesData:
    undiscounted_price: Money
    price_with_voucher: Money
    price: Money
