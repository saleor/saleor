from decimal import Decimal

from prices import Money, TaxedMoney

from saleor.tax.models import TaxClassCountryRate

from ...core.prices import quantize_price
from ...core.taxes import zero_money, zero_taxed_money
from ...discount import DiscountValueType, OrderDiscountType
from ...order.utils import get_order_country
from .. import TaxCalculationStrategy
from ..calculations.order import (
    update_order_prices_with_flat_rates,
    update_taxes_for_order_lines,
)


def _enable_flat_rates(order, prices_entered_with_tax):
    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()


def test_calculations_calculate_order_total(order_with_lines):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("65.04", "USD"), gross=Money("80.00", "USD")
    )


def test_calculations_calculate_order_undiscounted_total(
    order_with_lines, voucher_shipping_type
):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=10,
    )
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal(5.0),
        name=voucher_shipping_type.code,
        currency=order.currency,
        amount_value=Decimal(5.0),
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.undiscounted_total == TaxedMoney(
        net=Money("80.00", "USD"), gross=Money("80.00", "USD")
    )


def test_calculations_calculate_order_total_use_product_type_tax_class(
    order_with_lines,
):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()
    for line in lines:
        line.variant.product.tax_class = None
        line.variant.product.save()

    country = get_order_country(order)
    TaxClassCountryRate.objects.filter(tax_class=None, country=country).delete()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("65.04", "USD"), gross=Money("80.00", "USD")
    )


def test_calculations_calculate_order_total_no_rates(order_with_lines):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    TaxClassCountryRate.objects.all().delete()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("80.00", "USD"), gross=Money("80.00", "USD")
    )


def test_calculations_calculate_order_total_default_country_rate(order_with_lines):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    country = get_order_country(order)
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    TaxClassCountryRate.objects.all().delete()
    TaxClassCountryRate.objects.create(country=country, rate=23)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("65.04", "USD"), gross=Money("80.00", "USD")
    )


def test_calculations_calculate_order_total_voucher(order_with_lines):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    discount_amount = 10
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=10,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("56.92", "USD"), gross=Money("70.01", "USD")
    )


def test_calculations_calculate_order_total_with_manual_discount(order_with_lines):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=10,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("56.92", "USD"), gross=Money("70.01", "USD")
    )


def test_calculations_calculate_order_total_with_discount_for_order_total(
    order_with_lines,
):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=80,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=80,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(net=Money("0", "USD"), gross=Money("0", "USD"))


def test_calculations_calculate_order_total_with_discount_for_subtotal_and_shipping(
    order_with_lines,
):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=75,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=75,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("3.13", "USD"), gross=Money("5.00", "USD")
    )


def test_calculations_calculate_order_total_with_discount_for_more_than_order_total(
    order_with_lines,
):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=100,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=100,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(net=Money("0", "USD"), gross=Money("0", "USD"))


def test_calculations_calculate_order_total_with_manual_discount_and_voucher(
    order_with_lines,
):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=10,
    )
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=10,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("48.78", "USD"), gross=Money("60.00", "USD")
    )


def test_calculate_order_shipping(order_line, shipping_zone):
    # given
    order = order_line.order
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.base_shipping_price = method.channel_listings.get(channel=order.channel).price
    order.save()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    price = order.shipping_price
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("8.13", "USD"), gross=Money("10.00", "USD"))


def test_calculate_order_shipping_for_order_without_shipping(order_line, shipping_zone):
    # given
    order = order_line.order
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.shipping_method = None
    order.save()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    price = order.shipping_price
    assert price == zero_taxed_money(order.currency)


def test_calculate_order_shipping_voucher_on_shipping(
    order_line, shipping_zone, voucher_shipping_type
):
    # given
    order = order_line.order
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()
    currency = order.currency
    discount_amount = Decimal("5.0")

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.base_shipping_price = method.channel_listings.get(
        channel=order.channel
    ).price - Money(discount_amount, currency)
    order.voucher = voucher_shipping_type
    order.save()

    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name=voucher_shipping_type.code,
        currency=currency,
        amount_value=discount_amount,
    )
    channel = order.channel
    shipping_channel_listings = method.channel_listings.get(channel=channel)
    shipping_price = shipping_channel_listings.price

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    price = order.shipping_price
    price = quantize_price(price, price.currency)
    expected_gross_amount = shipping_price.amount - discount_amount
    assert price == TaxedMoney(
        net=quantize_price(
            Money(expected_gross_amount / Decimal("1.23"), currency), currency
        ),
        gross=Money(expected_gross_amount, currency),
    )


def test_calculate_order_shipping_free_shipping_voucher(
    order_line, shipping_zone, voucher_shipping_type
):
    # given
    order = order_line.order
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.base_shipping_price = zero_money(order.currency)
    order.voucher = voucher_shipping_type
    order.save()

    currency = order.currency
    channel = order.channel
    shipping_channel_listings = method.channel_listings.get(channel=channel)
    shipping_price = shipping_channel_listings.price

    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("100.0"),
        name=voucher_shipping_type.code,
        currency=currency,
        amount_value=shipping_price.amount,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    price = order.shipping_price
    price = quantize_price(price, price.currency)
    assert price == zero_taxed_money(currency)


def test_update_taxes_for_order_lines(order_with_lines):
    # given
    order = order_with_lines
    currency = order.currency
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()
    country_code = get_order_country(order)

    # when
    lines, _ = update_taxes_for_order_lines(
        order, lines, country_code, Decimal(23), prices_entered_with_tax
    )

    # then

    for line in lines:
        assert line.unit_price == TaxedMoney(
            net=quantize_price(line.base_unit_price / Decimal("1.23"), currency),
            gross=line.base_unit_price,
        )
        assert line.undiscounted_unit_price == line.unit_price
        assert line.total_price == TaxedMoney(
            net=quantize_price(
                line.base_unit_price / Decimal("1.23") * line.quantity, currency
            ),
            gross=line.base_unit_price * line.quantity,
        )
        assert line.undiscounted_total_price == line.total_price
        assert line.tax_rate == Decimal("0.23")


def test_update_taxes_for_order_lines_voucher_on_entire_order(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    currency = order.currency
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()
    country_code = get_order_country(order)

    order.voucher = voucher
    lines = list(order.lines.all())
    total_amount = sum([line.base_unit_price.amount * line.quantity for line in lines])
    order.undiscounted_total_gross_amount = total_amount
    order.undiscounted_total_net_amount = total_amount
    order.save(
        update_fields=[
            "voucher",
            "undiscounted_total_gross_amount",
            "undiscounted_total_net_amount",
        ]
    )

    order_discount_amount = Decimal("5.0")
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=order_discount_amount,
        name=voucher.code,
        currency=currency,
        amount_value=order_discount_amount,
    )

    # when
    lines, _ = update_taxes_for_order_lines(
        order, lines, country_code, Decimal(23), prices_entered_with_tax
    )

    # then
    for line in lines:
        total_line_price = line.base_unit_price * line.quantity
        discount_amount = quantize_price(
            total_line_price.amount / total_amount * order_discount_amount, currency
        )
        unit_gross = quantize_price(
            (total_line_price - Money(discount_amount, currency)) / line.quantity,
            currency,
        )
        assert line.unit_price == TaxedMoney(
            net=quantize_price(unit_gross / Decimal("1.23"), currency),
            gross=quantize_price(unit_gross, currency),
        )
        assert line.undiscounted_unit_price == TaxedMoney(
            net=quantize_price(line.base_unit_price / Decimal("1.23"), currency),
            gross=line.base_unit_price,
        )
        assert line.total_price == TaxedMoney(
            net=quantize_price(unit_gross / Decimal("1.23") * line.quantity, currency),
            gross=quantize_price(unit_gross * line.quantity, currency),
        )
        assert line.undiscounted_total_price == TaxedMoney(
            net=quantize_price(
                line.base_unit_price / Decimal("1.23") * line.quantity, currency
            ),
            gross=quantize_price(line.base_unit_price * line.quantity, currency),
        )
        assert line.tax_rate == (line.unit_price.tax / line.unit_price.net).quantize(
            Decimal(".001")
        )


def test_update_taxes_for_order_lines_voucher_on_shipping(
    order_with_lines, voucher_shipping_type
):
    # given
    order = order_with_lines
    currency = order.currency
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()
    country_code = get_order_country(order)

    order.voucher = voucher_shipping_type
    lines = list(order.lines.all())
    total_amount = sum([line.base_unit_price.amount * line.quantity for line in lines])
    order.undiscounted_total_gross_amount = total_amount
    order.undiscounted_total_net_amount = total_amount
    order.save(
        update_fields=[
            "voucher",
            "undiscounted_total_gross_amount",
            "undiscounted_total_net_amount",
        ]
    )

    order_discount_amount = Decimal("5.0")
    order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=order_discount_amount,
        name=voucher_shipping_type.code,
        currency=currency,
        amount_value=order_discount_amount,
    )

    # when
    lines, _ = update_taxes_for_order_lines(
        order, lines, country_code, Decimal(23), prices_entered_with_tax
    )

    # then
    for line in lines:
        assert line.unit_price == TaxedMoney(
            net=quantize_price(line.base_unit_price / Decimal("1.23"), currency),
            gross=line.base_unit_price,
        )
        assert line.undiscounted_unit_price == line.unit_price
        assert line.total_price == TaxedMoney(
            net=quantize_price(
                line.base_unit_price / Decimal("1.23") * line.quantity, currency
            ),
            gross=line.base_unit_price * line.quantity,
        )
        assert line.undiscounted_total_price == line.total_price
        assert line.tax_rate == Decimal("0.23")


def test_use_original_tax_rate_when_tax_class_is_removed_from_order_line(
    order_with_lines,
):
    # given
    order = order_with_lines
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # when
    for line in lines:
        tax_class = line.variant.product.tax_class
        if tax_class:
            tax_class.delete()
        tax_class = line.variant.product.product_type.tax_class
        if tax_class:
            tax_class.delete()
        line.refresh_from_db()

    shipping_tax_class = order.shipping_method.tax_class
    if shipping_tax_class:
        shipping_tax_class.delete()
        order.shipping_method.refresh_from_db()

    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("65.04", "USD"), gross=Money("80.00", "USD")
    )
