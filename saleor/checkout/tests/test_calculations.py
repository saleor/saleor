from decimal import Decimal

from saleor.checkout.calculations import _apply_tax_data
from saleor.checkout.models import Checkout
from saleor.core.taxes import TaxData, TaxLineData


def test_apply_tax_data(checkout: Checkout):
    # given
    net = Decimal("10.00")
    gross = Decimal("12.30")
    tax_data = TaxData(
        currency=checkout.currency,
        shipping_price_net_amount=checkout.shipping_price.net.amount + net,
        shipping_price_gross_amount=checkout.shipping_price.gross.amount + gross,
        subtotal_net_amount=checkout.subtotal.net.amount + net,
        subtotal_gross_amount=checkout.subtotal.gross.amount + gross,
        total_net_amount=checkout.shipping_price.net.amount + net,
        total_gross_amount=checkout.shipping_price.gross.amount + gross,
        lines=[
            TaxLineData(
                id=i,
                currency=checkout.currency,
                unit_net_amount=line.unit_price.net.amount,
                unit_gross_amount=line.unit_price.gross.amount,
                total_net_amount=line.total_price.net.amount,
                total_gross_amount=line.total_price.gross.amount,
            )
            for i, line in enumerate(checkout.lines.all())
        ],
    )

    # when
    _apply_tax_data(checkout, tax_data)

    # then
    assert checkout.total.net.amount == tax_data.total_net_amount
    assert checkout.total.gross.amount == tax_data.total_gross_amount

    assert checkout.subtotal.net.amount == tax_data.subtotal_net_amount
    assert checkout.subtotal.gross.amount == tax_data.subtotal_gross_amount

    assert checkout.shipping_price.net.amount == tax_data.shipping_price_net_amount
    assert checkout.shipping_price.gross.amount == tax_data.shipping_price_gross_amount

    for line, tax_line in zip(checkout.lines.all(), tax_data.lines):
        assert line.unit_price.net.amout == tax_line.unit_net_amount
        assert line.unit_price.gross.amout == tax_line.unit_gross_amount

        assert line.total_price.net.amout == tax_line.total_net_amount
        assert line.total_price.gross.amout == tax_line.total_gross_amount
