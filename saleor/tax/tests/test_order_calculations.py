from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from saleor.tax.models import TaxClass, TaxClassCountryRate

from ...core.prices import quantize_price
from ...core.taxes import zero_money, zero_taxed_money
from ...discount import DiscountType, DiscountValueType
from ...order import OrderStatus
from ...order.base_calculations import calculate_prices
from ...order.calculations import fetch_order_prices_if_expired
from ...order.models import OrderLine
from ...order.utils import get_order_country
from ...payment.model_helpers import get_subtotal
from ...plugins.manager import get_plugins_manager
from .. import TaxCalculationStrategy
from ..calculations.order import (
    update_order_prices_with_flat_rates,
    update_taxes_for_order_lines,
)


def _enable_flat_rates(
    order, prices_entered_with_tax, use_weighted_tax_for_shipping=False
):
    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = prices_entered_with_tax
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.use_weighted_tax_for_shipping = use_weighted_tax_for_shipping
    tc.save()


@pytest.mark.parametrize("use_weighted_tax_for_shipping", [True, False])
def test_calculations_calculate_order_total(
    order_with_lines_untaxed, use_weighted_tax_for_shipping
):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax, use_weighted_tax_for_shipping)
    lines = order.lines.all()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("65.04", "USD"), gross=Money("80.00", "USD")
    )


@pytest.mark.parametrize(
    (
        "expected_net",
        "expected_gross",
        "prices_entered_with_tax",
        "use_weighted_tax_for_shipping",
    ),
    [
        ("80.00", "90.40", False, False),
        ("71.35", "80.00", True, False),
        ("80.00", "89.26", False, True),
        ("72.25", "80.00", True, True),
    ],
)
def test_calculate_order_total_with_multiple_tax_rates(
    order_with_lines_untaxed,
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    use_weighted_tax_for_shipping,
    tax_classes,
):
    # given
    order = order_with_lines_untaxed
    _enable_flat_rates(order, prices_entered_with_tax, use_weighted_tax_for_shipping)

    country = get_order_country(order)

    lines = list(order.lines.all())
    first_line = lines[0]
    second_line = lines[-1]

    # Set different tax rates for different products
    first_line.tax_class.country_rates.update_or_create(country=country, rate=23)

    second_tax_class = tax_classes[0]
    second_tax_class.country_rates.filter(country=country).update(rate=3)
    second_line.tax_class = second_tax_class
    second_line.save()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    (
        "expected_net",
        "expected_gross",
        "prices_entered_with_tax",
    ),
    [
        ("10.00", "12.30", False),
        ("8.13", "10.00", True),
    ],
)
def test_calculate_order_shipping_with_not_weighted_taxes(
    order_with_lines_untaxed,
    shipping_zone,
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    tax_classes,
):
    # given
    order = order_with_lines_untaxed
    _enable_flat_rates(
        order, prices_entered_with_tax, use_weighted_tax_for_shipping=False
    )

    country = get_order_country(order)

    lines = list(order.lines.all())
    first_line = lines[0]
    second_line = lines[-1]

    # Set different tax rates for different products
    first_line.tax_class.country_rates.update_or_create(country=country, rate=23)

    second_tax_class = tax_classes[0]
    second_tax_class.country_rates.filter(country=country).update(rate=3)
    second_line.tax_class = second_tax_class
    second_line.save()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.shipping_tax_rate == Decimal("0.2300")
    assert order.shipping_price == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    (
        "expected_net",
        "expected_gross",
        "prices_entered_with_tax",
        "expected_shipping_tax_rate",
    ),
    [
        ("10.00", "11.16", False, "0.1157"),
        ("9.03", "10.00", True, "0.1072"),
    ],
)
def test_calculate_order_shipping_with_weighted_taxes(
    order_with_lines_untaxed,
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    tax_classes,
    expected_shipping_tax_rate,
):
    # given
    order = order_with_lines_untaxed
    _enable_flat_rates(
        order, prices_entered_with_tax, use_weighted_tax_for_shipping=True
    )

    country = get_order_country(order)

    lines = list(order.lines.all())
    first_line = lines[0]
    second_line = lines[-1]

    # Set different tax rates for different products
    first_line.tax_class.country_rates.update_or_create(country=country, rate=23)

    second_tax_class = tax_classes[0]
    second_tax_class.country_rates.filter(country=country).update(rate=3)
    second_line.tax_class = second_tax_class
    second_line.save()

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    weighted_tax_amount = sum(
        line.total_price.net.amount * line.tax_rate for line in lines
    )
    weighted_tax_amount = weighted_tax_amount / sum(
        line.total_price.net.amount for line in lines
    )
    assert (
        order.shipping_tax_rate.quantize(Decimal("0.0001"))
        == Decimal(weighted_tax_amount).quantize(Decimal("0.0001"))
        == Decimal(expected_shipping_tax_rate).quantize(Decimal("0.0001"))
    )
    assert order.shipping_price == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize("use_weighted_tax_for_shipping", [True, False])
def test_calculations_calculate_order_undiscounted_total(
    order_with_lines_untaxed, voucher_shipping_type, use_weighted_tax_for_shipping
):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax, use_weighted_tax_for_shipping)
    lines = order.lines.all()

    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=10,
    )
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal(5.0),
        name=voucher_shipping_type.code,
        currency=order.currency,
        amount_value=Decimal(5.0),
        voucher=voucher_shipping_type,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.undiscounted_total == TaxedMoney(
        net=Money("65.04", "USD"), gross=Money("80.00", "USD")
    )


def test_calculations_calculate_order_total_use_product_type_tax_class(
    order_with_lines_untaxed,
):
    # given
    order = order_with_lines_untaxed
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


def test_calculations_calculate_order_total_no_rates(order_with_lines_untaxed):
    # given
    order = order_with_lines_untaxed
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


def test_calculations_calculate_order_total_default_country_rate(
    order_with_lines_untaxed,
):
    # given
    order = order_with_lines_untaxed
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


def test_calculations_calculate_order_total_voucher(order_with_lines_untaxed, voucher):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    discount_amount = 10
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=10,
        voucher=voucher,
    )
    calculate_prices(order, lines)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("56.91", "USD"), gross=Money("70.00", "USD")
    )


def test_calculations_calculate_order_total_with_manual_discount(
    order_with_lines_untaxed,
):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=10,
    )
    calculate_prices(order, lines)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("56.91", "USD"), gross=Money("70.00", "USD")
    )


def test_calculations_calculate_order_total_with_discount_for_order_total(
    order_with_lines_untaxed,
):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=DiscountType.MANUAL,
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
    order_with_lines_untaxed,
):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=75,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=75,
    )
    calculate_prices(order, lines)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("4.07", "USD"), gross=Money("5.01", "USD")
    )


def test_calculations_calculate_order_total_with_discount_for_more_than_order_total(
    order_with_lines_untaxed,
):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=DiscountType.MANUAL,
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
    order_with_lines_untaxed, voucher
):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=10,
    )
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=10,
        voucher=voucher,
    )
    calculate_prices(order, lines)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("48.77", "USD"), gross=Money("60.00", "USD")
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
    order.shipping_tax_class = method.tax_class
    base_shipping_price = method.channel_listings.get(channel=order.channel).price
    order.base_shipping_price = base_shipping_price
    order.undiscounted_base_shipping_price = base_shipping_price
    order.save()

    calculate_prices(order, lines)

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

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.voucher = voucher_shipping_type
    order.save()

    voucher_listing = voucher_shipping_type.channel_listings.get(channel=order.channel)

    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        name=voucher_shipping_type.code,
        currency=currency,
        value=voucher_listing.discount_value,
        voucher=voucher_shipping_type,
    )
    channel = order.channel
    shipping_channel_listings = method.channel_listings.get(channel=channel)
    shipping_price = shipping_channel_listings.price

    calculate_prices(order, lines)

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    price = order.shipping_price
    price = quantize_price(price, price.currency)
    expected_gross_amount = shipping_price.amount - voucher_listing.discount_value
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
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("100.0"),
        name=voucher_shipping_type.code,
        currency=currency,
        amount_value=shipping_price.amount,
        voucher=voucher_shipping_type,
    )

    # when
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    price = order.shipping_price
    price = quantize_price(price, price.currency)
    assert price == zero_taxed_money(currency)


def test_update_taxes_for_order_lines(order_with_lines_untaxed):
    # given
    order = order_with_lines_untaxed
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
    order_with_lines_untaxed, voucher
):
    # given
    order = order_with_lines_untaxed
    currency = order.currency
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    country_code = get_order_country(order)

    order.voucher = voucher
    lines = list(order.lines.all())
    total_amount = sum([line.base_unit_price.amount * line.quantity for line in lines])
    order.save(update_fields=["voucher"])

    order_discount_amount = Decimal("5.0")
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=order_discount_amount,
        name=voucher.code,
        currency=currency,
        amount_value=order_discount_amount,
        voucher=voucher,
    )

    # when
    calculate_prices(order, lines)
    lines, _ = update_taxes_for_order_lines(
        order, lines, country_code, Decimal(23), prices_entered_with_tax
    )

    # then
    for line in lines:
        total_line_price = line.base_unit_price * line.quantity
        discount_amount = quantize_price(
            total_line_price.amount / total_amount * order_discount_amount, currency
        )
        unit_gross = (
            total_line_price - Money(discount_amount, currency)
        ) / line.quantity
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
    order_with_lines_untaxed, voucher_shipping_type
):
    # given
    order = order_with_lines_untaxed
    currency = order.currency
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()
    country_code = get_order_country(order)

    order.voucher = voucher_shipping_type
    order.save(update_fields=["voucher"])

    order_discount_amount = Decimal("5.0")
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=order_discount_amount,
        name=voucher_shipping_type.code,
        currency=currency,
        amount_value=order_discount_amount,
        voucher=voucher_shipping_type,
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


def test_update_taxes_for_order_line_on_promotion(
    order_with_lines_untaxed, order_line_on_promotion
):
    # given
    order = order_with_lines_untaxed
    currency = order.currency
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    country_code = get_order_country(order)

    order_line_on_promotion.order = order
    order_line_on_promotion.save(update_fields=["order"])

    lines = order.lines.all()
    assert lines.count() == 3

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
        assert line.undiscounted_unit_price == TaxedMoney(
            net=quantize_price(
                line.undiscounted_base_unit_price / Decimal("1.23"), currency
            ),
            gross=line.undiscounted_base_unit_price,
        )
        assert line.total_price == TaxedMoney(
            net=quantize_price(
                line.base_unit_price / Decimal("1.23") * line.quantity, currency
            ),
            gross=line.base_unit_price * line.quantity,
        )
        assert line.undiscounted_total_price == TaxedMoney(
            net=quantize_price(
                line.undiscounted_base_unit_price / Decimal("1.23") * line.quantity,
                currency,
            ),
            gross=line.undiscounted_base_unit_price * line.quantity,
        )
        assert line.tax_rate == Decimal("0.23")


def test_use_original_tax_rate_when_tax_class_is_removed_from_order_line(
    order_with_lines_untaxed,
):
    # given
    order = order_with_lines_untaxed
    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()
    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)
    OrderLine.objects.bulk_update(lines, ["tax_rate"])

    assert order.total == TaxedMoney(
        net=Money("65.04", "USD"), gross=Money("80.00", "USD")
    )

    # when
    TaxClass.objects.all().delete()

    order.refresh_from_db()
    lines = order.lines.all()

    update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)

    # then
    assert order.total == TaxedMoney(
        net=Money("65.04", "USD"), gross=Money("80.00", "USD")
    )


def test_use_default_country_rate_when_no_tax_class_was_set_before(
    order_with_lines_untaxed,
):
    # given
    manager = get_plugins_manager(allow_replica=False)
    order = order_with_lines_untaxed
    country = get_order_country(order)
    TaxClassCountryRate.objects.create(country=country, rate=20)

    prices_entered_with_tax = True
    _enable_flat_rates(order, prices_entered_with_tax)
    lines = order.lines.all()

    # drop tax classes from lines and shipping, so that default country rate is used
    for line in lines:
        line.tax_class = None
        line.tax_rate = Decimal(0)
        line.tax_class_name = None
        line.save(
            update_fields=[
                "tax_rate",
                "tax_class",
                "tax_class_name",
            ]
        )

    order.shipping_method.tax_class.delete()
    order.shipping_tax_class = None
    order.shipping_tax_class_name = None
    order.shipping_tax_rate = Decimal(0)
    order.status = OrderStatus.DRAFT
    order.save(
        update_fields=[
            "status",
            "shipping_tax_class_name",
            "shipping_tax_class",
            "shipping_tax_rate",
        ]
    )
    order.refresh_from_db()

    # when
    fetch_order_prices_if_expired(order, manager, force_update=True)
    order.refresh_from_db()

    # then
    line = order.lines.first()
    assert line.tax_rate == Decimal("0.20")
    assert not line.tax_class
    assert not line.tax_class_name

    assert order.shipping_tax_rate == Decimal("0.20")
    assert not order.shipping_tax_class
    assert not order.shipping_tax_class_name

    assert order.subtotal == get_subtotal(order.lines.all(), order.currency)
