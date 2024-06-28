import datetime
from decimal import Decimal
from json import JSONDecodeError
from unittest.mock import Mock, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from prices import Money, TaxedMoney
from requests import RequestException
from requests_hardened import HTTPSession

from ....account.models import Address
from ....checkout.fetch import (
    CheckoutInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ....checkout.utils import add_variant_to_checkout
from ....core.prices import quantize_price
from ....core.taxes import TaxError, TaxType, zero_money, zero_taxed_money
from ....discount import DiscountType, DiscountValueType, RewardValueType, VoucherType
from ....discount.models import CheckoutLineDiscount, Promotion, PromotionRule
from ....discount.utils.checkout import (
    create_or_update_discount_objects_from_promotion_for_checkout,
)
from ....order import OrderStatus
from ....product import ProductTypeKind
from ....product.models import Product, ProductType
from ....product.utils.variant_prices import update_discounted_prices_for_promotion
from ....product.utils.variants import fetch_variants_for_promotion_rules
from ....tax import TaxCalculationStrategy
from ....tax.models import TaxClass
from ...manager import get_plugins_manager
from ...models import PluginConfiguration
from .. import (
    DEFAULT_TAX_CODE,
    META_CODE_KEY,
    META_DESCRIPTION_KEY,
    TAX_CODE_NON_TAXABLE_PRODUCT,
    AvataxConfiguration,
    TransactionType,
    _validate_address_details,
    _validate_checkout,
    _validate_order,
    api_get_request,
    api_post_request,
    generate_request_data_from_checkout,
    generate_request_data_from_checkout_lines,
    get_cached_tax_codes_or_fetch,
    get_order_lines_data,
    get_order_request_data,
    get_order_tax_data,
    taxes_need_new_fetch,
)
from ..plugin import AvataxPlugin


def order_set_shipping_method(order, shipping_method):
    order.base_shipping_price = shipping_method.channel_listings.get(
        channel=order.channel
    ).price
    order.shipping_method = shipping_method
    order.shipping_method_name = shipping_method.name
    order.shipping_tax_class = shipping_method.tax_class
    order.shipping_tax_class_name = shipping_method.tax_class.name
    order.shipping_tax_class_metadata = shipping_method.tax_class.metadata
    order.shipping_tax_class_private_metadata = (
        shipping_method.tax_class.private_metadata
    )


def assign_tax_code_to_object_meta(obj: "TaxClass", tax_code: str):
    tax_item = {META_CODE_KEY: tax_code}
    obj.store_value_in_metadata(items=tax_item)


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("24.39", "30.00", True),
        ("30.00", "36.90", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item,
    ship_to_pl_address,
    monkeypatch,
    shipping_zone,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    tax_configuration = checkout_with_item.channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_line_info = lines[0]

    total = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("12.20", "15.00", True),
        ("15.00", "18.45", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total_with_promotion(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item_on_promotion,
    ship_to_pl_address,
    monkeypatch,
    shipping_zone,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    line = checkout.lines.first()
    product = line.variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]

    # when
    total = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total_with_variant_on_promotion(
    checkout_with_item_on_promotion,
    shipping_zone,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_on_promotion

    quantity = 3
    line = checkout.lines.first()
    line.quantity = quantity

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("12.20"), currency), gross=Money(Decimal("15.00"), currency)
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("20.33", "25.00", True),
        ("25.00", "30.75", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total_with_order_promotion(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item_and_order_discount,
    ship_to_pl_address,
    monkeypatch,
    shipping_zone,
    plugin_configuration,
):
    # given
    checkout = checkout_with_item_and_order_discount
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    line = checkout.lines.first()
    product = line.variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]

    # when
    total = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total_gift_promotion_line(
    checkout_with_item_and_gift_promotion,
    ship_to_pl_address,
    shipping_zone,
    plugin_configuration,
):
    # given
    checkout = checkout_with_item_and_gift_promotion
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    line = checkout.lines.get(is_gift=True)
    product = line.variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    gift_line_info = [line_info for line_info in lines if line_info.line.is_gift][0]

    # when
    total = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        gift_line_info,
        checkout.shipping_address,
    )

    # then
    total = quantize_price(total, total.currency)
    assert total == zero_taxed_money(total.currency)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total_with_voucher(
    checkout_with_item,
    shipping_zone,
    address,
    plugin_configuration,
    voucher,
    channel_USD,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item

    quantity = 3
    line = checkout_with_item.lines.first()
    line.quantity = quantity

    checkout_line = checkout.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_item.voucher_code = voucher.code

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_line_info = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("17.07"), currency), gross=Money(Decimal("21.00"), currency)
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total_with_voucher_once_per_order(
    checkout_with_item,
    shipping_zone,
    address,
    plugin_configuration,
    voucher,
    channel_USD,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item

    checkout_line = checkout.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_item.voucher_code = voucher.code

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_line_info = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("21.95"), currency), gross=Money(Decimal("27.00"), currency)
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total_with_variant_on_promotion_and_voucher(
    checkout_with_item_on_promotion,
    shipping_zone,
    address,
    plugin_configuration,
    voucher,
    channel_USD,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_on_promotion

    checkout_line = checkout.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout.voucher_code = voucher.code

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line_info = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("4.88"), currency), gross=Money(Decimal("6.00"), currency)
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_total_with_variant_on_promotion_and_voucher_only_once(
    checkout_with_item_on_promotion,
    shipping_zone,
    address,
    plugin_configuration,
    voucher,
    channel_USD,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_on_promotion

    checkout_line = checkout.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout.voucher_code = voucher.code

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line_info = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("9.76"), currency), gross=Money(Decimal("12.00"), currency)
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("24.39", "30.00", True),
        ("30.00", "36.90", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_without_sku_total(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item,
    ship_to_pl_address,
    monkeypatch,
    shipping_zone,
    plugin_configuration,
):
    monkeypatch.setattr(
        "graphene.Node.to_global_id", lambda x, y: "UHJvZHVjdFZhcmlhbnQ6Mg"
    )

    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    tax_configuration = checkout_with_item.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    line = checkout_with_item.lines.first()
    line.variant.sku = None
    line.variant.save()
    product = line.variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_line_info = lines[0]

    total_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
    )
    total = quantize_price(total_price, total_price.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("12.20", "15.00", True),
        ("15.00", "18.45", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_without_sku_total_with_promotion(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item_on_promotion,
    ship_to_pl_address,
    monkeypatch,
    shipping_zone,
    plugin_configuration,
):
    # given
    monkeypatch.setattr(
        "graphene.Node.to_global_id", lambda x, y: "UHJvZHVjdFZhcmlhbnQ6Mg"
    )

    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    line = checkout.lines.first()
    line.variant.sku = None
    line.variant.save()
    product = line.variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    checkout_line_info = lines[0]

    # when
    total_price = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    total = quantize_price(total_price, total_price.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_total(
    order_line,
    address,
    ship_to_pl_address,
    shipping_zone,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    order = order_line.order

    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    order.shipping_address = ship_to_pl_address
    shipping_method = shipping_zone.shipping_methods.get()
    order_set_shipping_method(order, shipping_method)
    order.save(
        update_fields=[
            "shipping_address",
            "shipping_method",
            "shipping_tax_class",
            "shipping_tax_class_name",
            "shipping_tax_class_metadata",
            "shipping_tax_class_private_metadata",
        ]
    )

    variant = order_line.variant
    product = variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    channel = order_line.order.channel
    channel_listing = variant.channel_listings.get(channel=channel)

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    order_line.unit_price = unit_price
    total_price = unit_price * order_line.quantity
    order_line.total_price = total_price
    order_line.base_unit_price = unit_price.gross
    order_line.save()

    total = manager.calculate_order_line_total(
        order_line.order, order_line, variant, product, list(order.lines.all())
    ).price_with_discounts
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(net=Money("24.39", "USD"), gross=Money("30.00", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_without_sku_total(
    order_line,
    address,
    ship_to_pl_address,
    shipping_zone,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    monkeypatch.setattr(
        "graphene.Node.to_global_id", lambda x, y: "UHJvZHVjdFZhcmlhbnQ6Mg"
    )

    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    order = order_line.order
    order.shipping_address = ship_to_pl_address
    shipping_method = shipping_zone.shipping_methods.get()
    order_set_shipping_method(order, shipping_method)
    order.save()

    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    variant = order_line.variant
    variant.sku = None
    variant.save()
    product = variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    channel = order_line.order.channel
    channel_listing = variant.channel_listings.get(channel=channel)

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    order_line.unit_price = unit_price
    total_price = unit_price * order_line.quantity
    order_line.total_price = total_price
    order_line.base_unit_price = unit_price.gross
    order_line.save()

    total = manager.calculate_order_line_total(
        order_line.order, order_line, variant, product, list(order.lines.all())
    ).price_with_discounts
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(net=Money("24.39", "USD"), gross=Money("30.00", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_total_with_discount(
    order_line,
    address,
    ship_to_pl_address,
    shipping_zone,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    order = order_line.order
    order.shipping_address = ship_to_pl_address
    shipping_method = shipping_zone.shipping_methods.get()
    order_set_shipping_method(order, shipping_method)
    order.save()

    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    variant = order_line.variant
    product = variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    channel = order_line.order.channel
    channel_listing = variant.channel_listings.get(channel=channel)

    discount_amount = Decimal("2.0")
    currency = order_line.currency
    order_line.unit_discount = Money(discount_amount, currency)
    order_line.unit_discount_value = discount_amount

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    order_line.unit_price = unit_price
    undiscounted_unit_price = order_line.unit_price + order_line.unit_discount
    order_line.undiscounted_unit_price = undiscounted_unit_price
    total_price = unit_price * order_line.quantity
    order_line.total_price = total_price
    order_line.base_unit_price = unit_price.gross
    order_line.undiscounted_total_price = undiscounted_unit_price * order_line.quantity
    order_line.save()

    # when
    total_price_data = manager.calculate_order_line_total(
        order_line.order, order_line, variant, product, list(order.lines.all())
    )

    # then
    assert total_price_data.undiscounted_price == TaxedMoney(
        net=Money(Decimal("36.90"), currency), gross=Money(Decimal("36.90"), currency)
    )
    assert total_price_data.price_with_discounts == TaxedMoney(
        net=Money(Decimal("24.39"), currency), gross=Money(Decimal("30.00"), currency)
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("16.26", "20.00", True),
        ("20.00", "24.60", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_total_entire_order_voucher(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    order_line,
    ship_to_pl_address,
    shipping_zone,
    voucher,
    monkeypatch,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    order = order_line.order
    channel = order.channel

    tax_configuration = channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    order.shipping_address = ship_to_pl_address
    shipping_method = shipping_zone.shipping_methods.get()
    order_set_shipping_method(order, shipping_method)
    order.save()

    variant = order_line.variant
    product = variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    channel_listing = variant.channel_listings.get(channel=channel)

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    order_line.unit_price = unit_price
    total_price = unit_price * order_line.quantity
    order_line.total_price = total_price
    order_line.base_unit_price = unit_price.gross
    order_line.save()

    order = order_line.order
    order.discounts.create(
        voucher=voucher,
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )
    order.voucher = voucher
    total = total_price * order.lines.count()
    order.total = total
    order.undiscounted_total = total
    order.save(
        update_fields=[
            "voucher",
            "undiscounted_total_gross_amount",
            "undiscounted_total_net_amount",
            "total_net_amount",
            "total_gross_amount",
        ]
    )

    # when
    total = manager.calculate_order_line_total(
        order_line.order, order_line, variant, product, list(order.lines.all())
    ).price_with_discounts

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("24.39", "30.00", True),
        ("30.00", "36.90", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_total_shipping_voucher(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    order_line,
    ship_to_pl_address,
    shipping_zone,
    voucher_free_shipping,
    monkeypatch,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    order = order_line.order
    channel = order_line.order.channel

    tax_configuration = channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    order.shipping_address = ship_to_pl_address
    shipping_method = shipping_zone.shipping_methods.get()
    order_set_shipping_method(order, shipping_method)
    order.save()

    variant = order_line.variant
    product = variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    channel_listing = variant.channel_listings.get(channel=channel)

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    order_line.unit_price = unit_price
    total_price = unit_price * order_line.quantity
    order_line.total_price = total_price
    order_line.base_unit_price = unit_price.gross
    order_line.save()

    order = order_line.order
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher_free_shipping.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )
    order.voucher = voucher_free_shipping
    total = total_price * order.lines.count()
    order.total = total
    order.undiscounted_total = total
    order.save(
        update_fields=[
            "voucher",
            "undiscounted_total_gross_amount",
            "undiscounted_total_net_amount",
            "total_net_amount",
            "total_gross_amount",
        ]
    )

    # when
    total = manager.calculate_order_line_total(
        order_line.order, order_line, variant, product, list(order.lines.all())
    ).price_with_discounts

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_total_order_not_valid(
    order_line,
    address,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    variant = order_line.variant
    product = variant.product
    product.metadata = {}
    product.save()
    product.product_type.save()

    order = order_line.order
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)

    tax_configuration = channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    order_line.base_unit_price = net
    order_line.undiscounted_base_unit_price = net
    order_line.unit_price = unit_price
    expected_total_price = unit_price * order_line.quantity
    order_line.total_price = expected_total_price
    order_line.save()

    total = manager.calculate_order_line_total(
        order_line.order, order_line, variant, product, list(order.lines.all())
    ).price_with_discounts
    total = quantize_price(total, total.currency)
    assert total == expected_total_price


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping_order_not_valid(
    order_line,
    address,
    site_settings,
    monkeypatch,
    plugin_configuration,
    shipping_method,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    variant = order_line.variant
    product = variant.product
    product.metadata = {}
    product.save(update_fields=["metadata"])

    order = order_line.order

    tax_configuration = order.channel.tax_configuration
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes"])
    tax_configuration.country_exceptions.all().delete()

    expected_shipping_price = TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )
    order.shipping_address = None
    order.base_shipping_price = Money("10.00", "USD")
    order_set_shipping_method(order, shipping_method)
    order.save()

    order.shipping_method.channel_listings.filter(channel_id=order.channel_id).update(
        price_amount=Decimal("10.00")
    )

    # when
    shipping_price = manager.calculate_order_shipping(order, list(order.lines.all()))

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)

    assert shipping_price == expected_shipping_price


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("41.99", "51.19", "0.0", False),
        ("32.04", "38.99", "3.0", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_uses_default_calculation(
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
    checkout_with_item,
    product_with_single_variant,
    voucher_percentage,
    shipping_zone,
    address,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
    non_default_category,
    tax_class_zero_rates,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.save()

    tax_configuration = checkout_with_item.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount = voucher_amount
    if voucher_amount != "0.0":
        checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.metadata = {}
    assign_tax_code_to_object_meta(product.product_type.tax_class, "PC040156")
    product.save()
    product.product_type.save()
    product_with_single_variant.tax_class = tax_class_zero_rates
    product_with_single_variant.category = non_default_category
    product_with_single_variant.save()
    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    add_variant_to_checkout(checkout_info, product_with_single_variant.variants.get())
    lines, _ = fetch_checkout_lines(checkout_with_item)

    total = manager.calculate_checkout_total(checkout_info, lines, address)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("22.32", "26.99", "0.0", True),
        ("21.99", "26.73", "5.0", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_uses_default_calculation_with_promotion(
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
    checkout_with_item_on_promotion,
    product_with_single_variant,
    voucher_percentage,
    shipping_zone,
    address,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
    non_default_category,
    tax_class_zero_rates,
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = ship_to_pl_address
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    voucher_amount = Money(voucher_amount, "USD")
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.discount = voucher_amount
    if voucher_amount != "0.0":
        checkout.voucher_code = voucher_percentage.code
    checkout.save()
    line = checkout.lines.first()
    product = line.variant.product
    product.metadata = {}
    assign_tax_code_to_object_meta(product.product_type.tax_class, "PC040156")
    product.save()
    product.product_type.save()
    product_with_single_variant.tax_class = tax_class_zero_rates
    product_with_single_variant.category = non_default_category
    product_with_single_variant.save()
    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, product_with_single_variant.variants.get())
    lines, _ = fetch_checkout_lines(checkout)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("41.99", "51.19", "0.0", False),
        ("32.04", "38.99", "3.0", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total(
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
    checkout_with_item,
    product_with_single_variant,
    voucher_percentage,
    shipping_zone,
    address,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
    non_default_category,
    tax_class_zero_rates,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc", TAX_CODE_NON_TAXABLE_PRODUCT: "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.save()

    tax_configuration = checkout_with_item.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount = voucher_amount
    if voucher_amount != "0.0":
        checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product

    assign_tax_code_to_object_meta(product.tax_class, "PS081282")
    product.save()
    product.tax_class.save()

    product_with_single_variant.tax_class = tax_class_zero_rates
    product_with_single_variant.category = non_default_category
    product_with_single_variant.save(
        update_fields=[
            "category",
            "tax_class",
        ]
    )
    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    add_variant_to_checkout(checkout_info, product_with_single_variant.variants.get())
    lines, _ = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_with_order_promotion(
    checkout_with_item_and_order_discount,
    shipping_zone,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
):
    # given
    checkout = checkout_with_item_and_order_discount
    discount_amount = checkout.discount_amount

    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc", TAX_CODE_NON_TAXABLE_PRODUCT: "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout.shipping_address = ship_to_pl_address
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    shipping_method = shipping_zone.shipping_methods.get()
    checkout.shipping_method = shipping_method
    checkout.save(update_fields=["shipping_method"])

    line = checkout.lines.first()
    product = line.variant.product

    assign_tax_code_to_object_meta(product.tax_class, "PS081282")
    product.save()
    product.tax_class.save()

    checkout_info = fetch_checkout_info(checkout, [], manager)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    total = quantize_price(total, total.currency)
    line_info = lines[0]
    unit_price = line_info.variant.get_price(line_info.channel_listing)
    subtotal_price_amount = (unit_price * line.quantity).amount - discount_amount
    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price
    total_price_amount = subtotal_price_amount + shipping_price.amount
    assert total == TaxedMoney(
        net=Money(round(total_price_amount / Decimal("1.23"), 2), checkout.currency),
        gross=Money(total_price_amount, "USD"),
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_with_gift_promotion(
    checkout_with_item_and_gift_promotion,
    shipping_zone,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
):
    # given
    checkout = checkout_with_item_and_gift_promotion

    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc", TAX_CODE_NON_TAXABLE_PRODUCT: "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout.shipping_address = ship_to_pl_address
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    shipping_method = shipping_zone.shipping_methods.get()
    checkout.shipping_method = shipping_method
    checkout.save(update_fields=["shipping_method"])

    line = checkout.lines.get(is_gift=False)
    product = line.variant.product

    assign_tax_code_to_object_meta(product.tax_class, "PS081282")
    product.save()
    product.tax_class.save()

    checkout_info = fetch_checkout_info(checkout, [], manager)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    total = quantize_price(total, total.currency)
    line_info = [line_info for line_info in lines if not line_info.line.is_gift][0]
    unit_price = line_info.variant.get_price(line_info.channel_listing)
    subtotal_price_amount = (unit_price * line.quantity).amount
    shipping_price = shipping_method.channel_listings.get(
        channel=checkout.channel
    ).price
    total_price_amount = subtotal_price_amount + shipping_price.amount
    assert total == TaxedMoney(
        net=Money(round(total_price_amount / Decimal("1.23"), 2), checkout.currency),
        gross=Money(total_price_amount, "USD"),
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("22.32", "26.99", "0.0", True),
        # ("21.99", "26.73", "5.0", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_with_promotion(
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
    checkout_with_item_on_promotion,
    product_with_single_variant,
    voucher_percentage,
    shipping_zone,
    address,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
    non_default_category,
    tax_class_zero_rates,
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc", TAX_CODE_NON_TAXABLE_PRODUCT: "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = ship_to_pl_address
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    voucher_amount = Money(voucher_amount, "USD")
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.discount = voucher_amount
    if voucher_amount != "0.0":
        checkout.voucher_code = voucher_percentage.code
    checkout.save()
    line = checkout.lines.first()
    product = line.variant.product

    assign_tax_code_to_object_meta(product.tax_class, "PS081282")
    product.save()
    product.tax_class.save()

    product_with_single_variant.tax_class = tax_class_zero_rates
    product_with_single_variant.category = non_default_category
    product_with_single_variant.save(
        update_fields=[
            "category",
            "tax_class",
        ]
    )
    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, product_with_single_variant.variants.get())
    lines, _ = fetch_checkout_lines(checkout)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("4300", "5289", "0.0", False),
        ("3493", "4297", "3.0", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_for_JPY(
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
    channel_JPY,
    checkout_JPY_with_item,
    voucher_percentage,
    shipping_zone_JPY,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
):
    # given
    checkout = checkout_JPY_with_item
    plugin_configuration(channel=channel_JPY)
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc", TAX_CODE_NON_TAXABLE_PRODUCT: "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout.shipping_address = ship_to_pl_address
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    voucher_amount = Money(voucher_amount, "JPY")
    checkout.shipping_method = shipping_zone_JPY.shipping_methods.get()
    checkout.discount = voucher_amount
    voucher_percentage.channel_listings.create(
        channel=channel_JPY,
        discount_value=10,
        currency=channel_JPY.currency_code,
    )
    if voucher_amount != "0.0":
        checkout.voucher_code = voucher_percentage.code
    checkout.save()
    line = checkout.lines.first()
    product = line.variant.product

    assign_tax_code_to_object_meta(product.tax_class, "PS081282")
    product.save()
    product.tax_class.save()

    checkout_info = fetch_checkout_info(checkout, [], manager)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "JPY"), gross=Money(expected_gross, "JPY")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "voucher_amount", "prices_entered_with_tax"),
    [
        ("3484", "4285", "0.0", True),
        ("4280", "5264", "5.0", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_for_JPY_with_promotion(
    expected_net,
    expected_gross,
    voucher_amount,
    prices_entered_with_tax,
    channel_JPY,
    checkout_JPY_with_item,
    voucher_percentage,
    shipping_zone_JPY,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
):
    # given
    checkout = checkout_JPY_with_item
    plugin_configuration(channel=channel_JPY)
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc", TAX_CODE_NON_TAXABLE_PRODUCT: "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout.shipping_address = ship_to_pl_address
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    voucher_amount = Money(voucher_amount, "JPY")
    checkout.shipping_method = shipping_zone_JPY.shipping_methods.get()
    checkout.discount = voucher_amount
    voucher_percentage.channel_listings.create(
        channel=channel_JPY,
        discount_value=10,
        currency=channel_JPY.currency_code,
    )
    if voucher_amount != "0.0":
        checkout.voucher_code = voucher_percentage.code
    checkout.save()
    line = checkout.lines.first()
    variant = line.variant
    product = variant.product

    assign_tax_code_to_object_meta(product.tax_class, "PS081282")
    product.save()
    product.tax_class.save()

    channel = checkout.channel
    promotion = Promotion.objects.create(name="Checkout promotion")

    reward_value = Decimal("5")
    rule = promotion.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel_JPY)

    variant_channel_listing = variant.channel_listings.get(channel=channel_JPY)

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel.currency_code,
    )
    CheckoutLineDiscount.objects.create(
        line=line,
        type=DiscountType.PROMOTION,
        value_type=DiscountValueType.FIXED,
        value=reward_value,
        amount_value=reward_value * line.quantity,
        currency=channel.currency_code,
        promotion_rule=rule,
    )

    checkout_info = fetch_checkout_info(checkout, [], manager)
    lines, _ = fetch_checkout_lines(checkout)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "JPY"), gross=Money(expected_gross, "JPY")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("8.13", "10.00", True),
        ("10.00", "12.30", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_voucher_on_entire_order(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item,
    voucher_percentage,
    stock,
    monkeypatch,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    """Check that the totals are correct when the checkout is 100% off."""
    # given
    plugin_configuration()
    variant = stock.product_variant
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    channel = checkout_with_item.channel

    tax_configuration = channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing) * checkout_with_item.lines.first().quantity

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.discount_amount = net.amount
    checkout_with_item.save()

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_voucher_on_entire_order_applied_once_per_order(
    checkout_with_item,
    voucher_percentage,
    stock,
    monkeypatch,
    site_settings,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    """Test that the totals are correct when the checkout is 100% off.

    In this case, the voucher is applied once per order.
    """
    # given
    plugin_configuration()
    variant = stock.product_variant
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    site_settings.company_address = address
    site_settings.save()

    channel = checkout_with_item.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing) * checkout_with_item.lines.first().quantity

    voucher_percentage.apply_once_per_order = True
    voucher_percentage.save(update_fields=["apply_once_per_order"])

    voucher_listing = voucher_percentage.channel_listings.get(
        channel=checkout_with_item.channel
    )
    discount_value = voucher_listing.discount_value

    shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.discount_amount = net.amount
    checkout_with_item.save()

    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    shipping_price = shipping_channel_listings.price

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    line = checkout_with_item.lines.first()
    channel_listing = variant.channel_listings.get(channel=channel)
    expected_amount = (
        channel_listing.price.amount * ((100 - discount_value) / 100)  # discounted line
        + ((line.quantity - 1) * channel_listing.price).amount  # undiscounted lines
        + shipping_price.amount  # shipping price
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=quantize_price(Money(expected_amount / Decimal(1.23), "USD"), "USD"),
        gross=quantize_price(Money(expected_amount, "USD"), "USD"),
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_voucher_on_entire_order_product_without_taxes(
    checkout_with_item,
    voucher_percentage,
    stock,
    monkeypatch,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    """Test that the totals are correct when the product is 100% off."""
    # given
    plugin_configuration()
    variant = stock.product_variant
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    channel = checkout_with_item.channel

    tax_configuration = channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = False
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing) * checkout_with_item.lines.first().quantity

    discount_amount = Decimal("2.0")
    checkout_with_item.shipping_address = ship_to_pl_address
    shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.discount_amount = discount_amount
    checkout_with_item.save()

    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)
    shipping_price = shipping_channel_listings.price

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)

    currency = checkout_with_item.currency

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    total = quantize_price(total, currency)
    expected_gross = Money(net.amount - discount_amount, "USD")
    assert total == TaxedMoney(
        net=quantize_price(expected_gross + shipping_price / Decimal("1.23"), currency),
        gross=expected_gross + shipping_price,
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("24.39", "30.00", True),
        ("30.00", "36.90", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_voucher_on_shipping(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item,
    voucher_free_shipping,
    stock,
    monkeypatch,
    ship_to_pl_address,
    shipping_zone,
    plugin_configuration,
):
    """Test that free shipping results in correct checkout totals."""
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    channel = checkout_with_item.channel

    tax_configuration = channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    shipping_method = shipping_zone.shipping_methods.get()
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.voucher_code = voucher_free_shipping.code
    checkout_with_item.discount_amount = shipping_channel_listings.price.amount
    checkout_with_item.save()

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)

    # when
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_total_not_charged_product_and_shipping_with_0_price(
    checkout_with_item,
    shipping_zone,
    ship_to_pl_address,
    monkeypatch,
    plugin_configuration,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PS081282": "desc"},
    )
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin", lambda *_: False
    )
    manager = get_plugins_manager(allow_replica=False)
    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.save()
    channel = checkout_with_item.channel

    tax_configuration = channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = False
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    shipping_method = shipping_zone.shipping_methods.get()
    shipping_channel_listing = shipping_method.channel_listings.get(channel=channel)
    shipping_channel_listing.price = Money(0, "USD")
    shipping_channel_listing.save()

    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    variant = line.variant
    product = variant.product
    product.metadata = {}
    assign_tax_code_to_object_meta(product.product_type.tax_class, "PS081282")
    product.save()
    product.product_type.save()

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_total(checkout_info, lines, ship_to_pl_address)
    total = quantize_price(total, total.currency)

    channel_listing = variant.channel_listings.get(channel=channel)
    expected_amount = (line.quantity * channel_listing.price).amount
    assert total == TaxedMoney(
        net=Money(expected_amount, "USD"), gross=Money(expected_amount, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_shipping(
    checkout_with_item_on_promotion,
    shipping_zone,
    address,
    ship_to_pl_address,
    site_settings,
    monkeypatch,
    plugin_configuration,
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    site_settings.company_address = address
    site_settings.save()

    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    shipping_price = manager.calculate_checkout_shipping(checkout_info, lines, address)

    # then
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("40.65", "50.00", True),
        ("50.00", "61.50", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_subtotal(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item,
    stock,
    monkeypatch,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    plugin_configuration()
    variant = stock.product_variant
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)

    tax_configuration = checkout_with_item.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    add_variant_to_checkout(checkout_info, variant, 2)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_subtotal(checkout_info, lines, address)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("25.00", "30.75", False),
        ("20.33", "25.00", True),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_subtotal_with_promotion(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item_on_promotion,
    stock,
    monkeypatch,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration()
    variant = stock.product_variant
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)

    checkout = checkout_with_item_on_promotion
    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, variant, 2)

    rule = PromotionRule.objects.first()
    rule.catalogue_predicate["variant_predicate"] = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
    ]
    rule.save(update_fields=["catalogue_predicate"])

    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    update_discounted_prices_for_promotion(Product.objects.all())

    lines, _ = fetch_checkout_lines(checkout)
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_info, lines)

    # when
    total = manager.calculate_checkout_subtotal(checkout_info, lines, address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_subtotal_for_product_without_tax(
    checkout,
    stock,
    monkeypatch,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
    tax_class_zero_rates,
):
    plugin_configuration()
    variant = stock.product_variant
    product = variant.product
    product.tax_class = tax_class_zero_rates
    product.save(update_fields=["tax_class"])

    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = False
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()

    quantity = 2
    checkout_info = fetch_checkout_info(checkout, [], manager)
    add_variant_to_checkout(checkout_info, variant, quantity)

    lines, _ = fetch_checkout_lines(checkout)
    assert len(lines) == 1

    total = manager.calculate_checkout_subtotal(checkout_info, lines, address)
    total = quantize_price(total, total.currency)
    expected_total = variant.channel_listings.first().price_amount * quantity
    assert total == TaxedMoney(
        net=Money(expected_total, "USD"), gross=Money(expected_total, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_subtotal_voucher_on_entire_order(
    prices_entered_with_tax,
    checkout_with_item,
    voucher_percentage,
    stock,
    monkeypatch,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    """Test that a voucher covering the total properly discounts the subtotal price to zero."""
    # given
    plugin_configuration()
    variant = stock.product_variant
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    channel = checkout_with_item.channel

    tax_configuration = channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(channel_listing) * checkout_with_item.lines.first().quantity

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.voucher_code = voucher_percentage.code
    checkout_with_item.discount_amount = net.amount
    checkout_with_item.save()

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)

    # when
    total = manager.calculate_checkout_subtotal(checkout_info, lines, address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("expected_net", "expected_gross", "prices_entered_with_tax"),
    [
        ("24.39", "30.00", True),
        ("30.00", "36.90", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_subtotal_voucher_on_shipping(
    expected_net,
    expected_gross,
    prices_entered_with_tax,
    checkout_with_item,
    voucher_free_shipping,
    stock,
    monkeypatch,
    ship_to_pl_address,
    shipping_zone,
    address,
    plugin_configuration,
):
    """That that free shipping does not affect the subtotal price."""
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    channel = checkout_with_item.channel

    tax_configuration = channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    shipping_method = shipping_zone.shipping_methods.get()
    shipping_channel_listings = shipping_method.channel_listings.get(channel=channel)

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.voucher_code = voucher_free_shipping.code
    checkout_with_item.discount_amount = shipping_channel_listings.price.amount
    checkout_with_item.save()

    checkout_info = fetch_checkout_info(checkout_with_item, [], manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)

    # when
    total = manager.calculate_checkout_subtotal(checkout_info, lines, address)

    # then
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping(
    order_line, shipping_zone, site_settings, address, plugin_configuration
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address
    site_settings.save()

    price = manager.calculate_order_shipping(order, list(order.lines.all()))
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("8.13", "USD"), gross=Money("10.00", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_total(
    order_line, shipping_zone, site_settings, address, plugin_configuration
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address
    site_settings.save()

    price = manager.calculate_order_total(order, order.lines.all())
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("38.13", "USD"), gross=Money("46.90", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_total_for_JPY(
    order_line_JPY,
    shipping_zone_JPY,
    channel_JPY,
    site_settings,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration(channel=channel_JPY)
    manager = get_plugins_manager(allow_replica=False)
    order = order_line_JPY.order
    method = shipping_zone_JPY.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address
    site_settings.save()

    # when
    price = manager.calculate_order_total(order, order.lines.all())

    # then
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("3496", "JPY"), gross=Money("4300", "JPY"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_total_order_promotion(
    order_with_lines_and_order_promotion,
    shipping_zone,
    site_settings,
    address,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    order = order_with_lines_and_order_promotion
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address
    site_settings.save()

    price = manager.calculate_order_total(order, order.lines.all())
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("44.71", "USD"), gross=Money("55.00", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_total_gift_promotion(
    order_with_lines_and_gift_promotion,
    shipping_zone,
    site_settings,
    address,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    order = order_with_lines_and_gift_promotion
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address
    site_settings.save()

    price = manager.calculate_order_total(order, order.lines.all())
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("65.04", "USD"), gross=Money("80.00", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping_entire_order_voucher(
    order_line, shipping_zone, voucher, site_settings, address, plugin_configuration
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    variant = order_line.variant
    channel = order_line.order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    order = order_line.order

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    total_price = unit_price * order_line.quantity
    total = total_price * order.lines.count()

    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.total = total
    order.undiscounted_total = total
    order.voucher = voucher
    order.save()

    site_settings.company_address = address
    site_settings.save()

    # when
    price = manager.calculate_order_shipping(order, list(order.lines.all()))

    # then
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("8.13", "USD"), gross=Money("10.00", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping_free_shipping_voucher(
    order_line,
    shipping_zone,
    voucher_free_shipping,
    site_settings,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    variant = order_line.variant
    channel = order_line.order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    order = order_line.order

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    total_price = unit_price * order_line.quantity
    total = total_price * order.lines.count()

    method = shipping_zone.shipping_methods.get()
    shipping_channel_listings = method.channel_listings.get(channel=channel)

    discount_amount = Decimal("10.0")
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name=voucher_free_shipping.code,
        currency="USD",
        amount_value=shipping_channel_listings.price.amount,
    )

    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.total = total
    order.undiscounted_total = total
    order.voucher = voucher_free_shipping
    order.discount_amount = discount_amount
    order.base_shipping_price_amount = (
        order.base_shipping_price.amount - discount_amount
    )
    order.save()

    site_settings.company_address = address
    site_settings.save()

    # when
    price = manager.calculate_order_shipping(order, list(order.lines.all()))

    # then
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("0", "USD"), gross=Money("0", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping_voucher_on_shipping(
    order_line,
    shipping_zone,
    voucher_shipping_type,
    site_settings,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    variant = order_line.variant
    channel = order_line.order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    order = order_line.order

    net = variant.get_price(channel_listing)
    unit_price = TaxedMoney(net=net, gross=net)
    total_price = unit_price * order_line.quantity
    total = total_price * order.lines.count()

    method = shipping_zone.shipping_methods.get()
    shipping_channel_listings = method.channel_listings.get(channel=channel)

    discount_amount = shipping_channel_listings.price.amount - Decimal("5")
    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name=voucher_shipping_type.code,
        currency="USD",
        amount_value=discount_amount,
    )

    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.total = total
    order.undiscounted_total = total
    order.base_shipping_price_amount = (
        order.base_shipping_price.amount - discount_amount
    )
    order.voucher = voucher_shipping_type
    order.save()

    site_settings.company_address = address
    site_settings.save()

    # when
    price = manager.calculate_order_shipping(order, list(order.lines.all()))

    # then
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("4.07", "USD"), gross=Money("5.0", "USD"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping_zero_shipping_amount(
    order_line, shipping_zone, site_settings, address, plugin_configuration
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()

    channel_listing = method.channel_listings.get(channel=order.channel)
    channel_listing.price_amount = 0
    channel_listing.save(update_fields=["price_amount"])

    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address
    site_settings.save()

    price = manager.calculate_order_shipping(order, list(order.lines.all()))
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("0.00", "USD"), gross=Money("0.00", "USD"))


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping_base_shipping_price_0(
    order_line, shipping_zone, site_settings, address, plugin_configuration
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.base_shipping_price = zero_money(order.currency)
    order.save()

    method.channel_listings.all().delete()

    site_settings.company_address = address
    site_settings.save()

    price = manager.calculate_order_shipping(order, list(order.lines.all()))
    price = quantize_price(price, price.currency)
    assert price == zero_taxed_money(order.currency)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_shipping_not_shippable_order(
    order_line, site_settings, address, plugin_configuration
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    order_line.is_shipping_required = False
    order_line.save(update_fields=["is_shipping_required"])

    order = order_line.order
    order.shipping_address = order.billing_address.get_copy()
    order.save(update_fields=["shipping_address"])

    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    # when
    price = manager.calculate_order_shipping(order, list(order.lines.all()))

    # then
    price = quantize_price(price, price.currency)
    assert price == zero_taxed_money(order.currency)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_unit(
    order_line,
    shipping_zone,
    site_settings,
    address_usa,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    order_line.unit_price = TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )
    order_line.base_unit_price = order_line.unit_price.gross
    order_line.undiscounted_unit_price = TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )
    order_line.save()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address_usa
    site_settings.save()

    line_price_data = manager.calculate_order_line_unit(
        order,
        order_line,
        order_line.variant,
        order_line.variant.product,
        list(order.lines.all()),
    )

    assert line_price_data.undiscounted_price == TaxedMoney(
        net=Money("12.30", "USD"), gross=Money("12.30", "USD")
    )
    assert line_price_data.price_with_discounts == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_unit_in_JPY(
    order_line_JPY,
    shipping_zone_JPY,
    site_settings,
    address,
    channel_JPY,
    plugin_configuration,
):
    plugin_configuration(channel=channel_JPY)
    manager = get_plugins_manager(allow_replica=False)

    # Net price from `test_calculate_checkout_line_unit_price_in_JPY`
    order_line_JPY.unit_price = TaxedMoney(
        net=Money("976", "JPY"), gross=Money("1200", "JPY")
    )
    order_line_JPY.undiscounted_unit_price = TaxedMoney(
        net=Money("976", "JPY"), gross=Money("1200", "JPY")
    )
    order_line_JPY.save()

    order = order_line_JPY.order
    method = shipping_zone_JPY.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address
    site_settings.save()

    line_price_data = manager.calculate_order_line_unit(
        order,
        order_line_JPY,
        order_line_JPY.variant,
        order_line_JPY.variant.product,
        list(order.lines.all()),
    )

    assert line_price_data.undiscounted_price == TaxedMoney(
        net=Money("1200", "JPY"), gross=Money("1200", "JPY")
    )
    assert line_price_data.price_with_discounts == TaxedMoney(
        net=Money("976", "JPY"), gross=Money("1200", "JPY")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_order_line_unit_with_discount(
    order_line,
    shipping_zone,
    site_settings,
    address_usa,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)
    unit_price = TaxedMoney(net=Money("10.00", "USD"), gross=Money("10.00", "USD"))
    order_line.unit_price = unit_price
    order_line.base_unit_price = unit_price.gross

    currency = order_line.currency
    discount_amount = Decimal("2.5")
    order_line.unit_discount = Money(discount_amount, currency)
    order_line.unit_discount_value = discount_amount
    order_line.save()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    site_settings.company_address = address_usa
    site_settings.save()

    # when
    line_price_data = manager.calculate_order_line_unit(
        order,
        order_line,
        order_line.variant,
        order_line.variant.product,
        list(order.lines.all()),
    )

    # then
    assert line_price_data.undiscounted_price == TaxedMoney(
        net=Money("12.30", "USD"), gross=Money("12.30", "USD")
    )
    assert line_price_data.price_with_discounts == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize("charge_taxes", [True, False])
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price(
    charge_taxes,
    checkout_with_item,
    shipping_zone,
    address,
    plugin_configuration,
):
    plugin_configuration()
    checkout = checkout_with_item

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_line = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = charge_taxes
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line,
        checkout.shipping_address,
    )

    if charge_taxes:
        expected_line_price = TaxedMoney(
            net=Money("8.13", "USD"), gross=Money("10.00", "USD")
        )
    else:
        expected_line_price = TaxedMoney(
            net=Money("10.00", "USD"), gross=Money("10.00", "USD")
        )
    assert line_price == expected_line_price


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_in_JPY(
    checkout_JPY_with_item,
    shipping_zone_JPY,
    ship_to_pl_address,
    channel_JPY,
    plugin_configuration,
):
    checkout = checkout_JPY_with_item
    plugin_configuration(channel=channel_JPY)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone_JPY.shipping_methods.get()
    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line,
        checkout.shipping_address,
    )
    assert line_price == TaxedMoney(net=Money("976", "JPY"), gross=Money("1200", "JPY"))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_with_variant_on_promotion(
    checkout_with_item_on_promotion,
    shipping_zone,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_on_promotion

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("4.07"), currency), gross=Money(Decimal("5.00"), currency)
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_order_promotion_charge_taxes(
    checkout_with_item_and_order_discount,
    shipping_zone,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_and_order_discount

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line = lines[0]
    discount_amount = checkout.discount_amount

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line,
        checkout.shipping_address,
    )

    # then
    line = lines[0].line
    unit_price = checkout_line.variant.get_price(checkout_line.channel_listing)
    total_price_amount = (unit_price * line.quantity).amount - discount_amount
    discounted_unit_amount = total_price_amount / line.quantity
    expected_line_price = TaxedMoney(
        net=Money(
            round(discounted_unit_amount / Decimal("1.23"), 2), checkout.currency
        ),
        gross=Money(round(discounted_unit_amount, 2), checkout.currency),
    )
    assert line_price == expected_line_price


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_order_promotion_do_not_charge_taxes(
    checkout_with_item_and_order_discount,
    shipping_zone,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_and_order_discount

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line = lines[0]
    discount_amount = checkout.discount_amount

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = False
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line,
        checkout.shipping_address,
    )

    # then
    line = lines[0].line
    unit_price = checkout_line.variant.get_price(checkout_line.channel_listing)
    total_price_amount = (unit_price * line.quantity).amount - discount_amount
    discounted_unit_amount = round(total_price_amount / line.quantity, 2)
    expected_line_price = TaxedMoney(
        net=Money(discounted_unit_amount, checkout.currency),
        gross=Money(discounted_unit_amount, checkout.currency),
    )
    assert line_price == expected_line_price


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_gift_promotion_line(
    checkout_with_item_and_gift_promotion,
    shipping_zone,
    address,
    plugin_configuration,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_and_gift_promotion

    lines, _ = fetch_checkout_lines(checkout)
    gift_line_info = [line_info for line_info in lines if line_info.line.is_gift][0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.charge_taxes = True
    tax_configuration.save(update_fields=["charge_taxes", "prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        gift_line_info,
        checkout.shipping_address,
    )

    # then
    assert line_price == zero_taxed_money(checkout.currency)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_with_voucher(
    checkout_with_item,
    shipping_zone,
    address,
    plugin_configuration,
    voucher,
    channel_USD,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item

    checkout_line = checkout.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_item.voucher_code = voucher.code

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_line_info = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("5.69"), currency), gross=Money(Decimal("7.00"), currency)
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_with_voucher_once_per_order(
    checkout_with_item,
    shipping_zone,
    address,
    plugin_configuration,
    voucher,
    channel_USD,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item

    checkout_line = checkout.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout_with_item.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout_with_item.voucher_code = voucher.code

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_line_info = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    # voucher with apply_once_per_order is added in calulation of total unit price
    assert line_price == TaxedMoney(
        net=Money(Decimal("7.32"), currency), gross=Money(Decimal("9.00"), currency)
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_with_variant_on_promotion_and_voucher(
    checkout_with_item_on_promotion,
    shipping_zone,
    address,
    plugin_configuration,
    voucher,
    channel_USD,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_on_promotion

    checkout_line = checkout.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout.voucher_code = voucher.code

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line_info = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("1.63"), currency), gross=Money(Decimal("2.00"), currency)
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_calculate_checkout_line_unit_price_variant_on_promotion_and_voucher_only_once(
    checkout_with_item_on_promotion,
    shipping_zone,
    address,
    plugin_configuration,
    voucher,
    channel_USD,
):
    # given
    plugin_configuration()
    checkout = checkout_with_item_on_promotion

    checkout_line = checkout.lines.first()
    voucher.products.add(checkout_line.variant.product)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.apply_once_per_order = True
    voucher.save()

    voucher_amount = Money(Decimal(3), checkout.currency)
    voucher_channel_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_channel_listing.discount = voucher_amount
    voucher_channel_listing.save()

    checkout.voucher_code = voucher.code

    lines, _ = fetch_checkout_lines(checkout)
    checkout_line_info = lines[0]

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    checkout.shipping_address = address
    checkout.shipping_method_name = method.name
    checkout.shipping_method = method
    checkout.save()

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_info = fetch_checkout_info(checkout, lines, manager)
    currency = checkout_info.checkout.currency

    # when
    line_price = manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        checkout_line_info,
        checkout.shipping_address,
    )

    # then
    assert line_price == TaxedMoney(
        net=Money(Decimal("3.25"), currency), gross=Money(Decimal("4.00"), currency)
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation(
    checkout_with_item_on_promotion,
    monkeypatch,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    site_settings.company_address = address
    site_settings.save()

    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when & then
    manager.preprocess_order_creation(checkout_info, lines)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_no_lines_data(
    checkout_with_item,
    monkeypatch,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when & then
    manager.preprocess_order_creation(checkout_info)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_wrong_data(
    checkout_with_item,
    monkeypatch,
    address,
    shipping_zone,
    plugin_configuration,
):
    # given
    plugin_configuration("wrong", "wrong")
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when & then
    with pytest.raises(TaxError):
        manager.preprocess_order_creation(checkout_info, lines)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_shipping_voucher_no_tax_class_on_delivery_method(
    checkout_with_item_on_promotion,
    monkeypatch,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    plugin_configuration,
    voucher_free_shipping,
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)
    site_settings.company_address = address
    site_settings.save()

    shipping_method = shipping_zone.shipping_methods.get()
    checkout = checkout_with_item_on_promotion
    checkout.shipping_address = ship_to_pl_address
    checkout.shipping_method = shipping_method
    checkout.voucher_code = voucher_free_shipping.code
    checkout.discount = shipping_method.channel_listings.first().price
    checkout.save()

    shipping_method.tax_class.delete()
    shipping_method.refresh_from_db()
    assert not shipping_method.tax_class

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when & then
    manager.preprocess_order_creation(checkout_info)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_address_error_logging(
    checkout_with_item,
    monkeypatch,
    address,
    shipping_zone,
    plugin_configuration,
    caplog,
):
    # given
    checkout = checkout_with_item
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    manager = get_plugins_manager(allow_replica=False)

    address.validation_skipped = True
    address.postal_code = "invalid postal code"
    address.save(update_fields=["postal_code", "validation_skipped"])

    checkout.shipping_address = address
    checkout.shipping_method = shipping_zone.shipping_methods.get()
    checkout.save()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    with pytest.raises(TaxError):
        manager.preprocess_order_creation(checkout_info, lines)

    # then
    assert f"Unable to calculate taxes for checkout {checkout.pk}" in caplog.text
    assert (
        f"Fetching tax data for checkout with address validation skipped. "
        f"Address ID: {address.pk}" in caplog.text
    )


@pytest.mark.vcr
def test_get_cached_tax_codes_or_fetch(monkeypatch, avatax_config):
    monkeypatch.setattr("saleor.plugins.avatax.cache.get", lambda x, y: {})
    config = avatax_config
    tax_codes = get_cached_tax_codes_or_fetch(config)
    assert len(tax_codes) > 0


@pytest.mark.vcr
def test_get_cached_tax_codes_or_fetch_wrong_response(monkeypatch):
    monkeypatch.setattr("saleor.plugins.avatax.cache.get", lambda x, y: {})
    config = AvataxConfiguration(
        username_or_account="wrong_data",
        password_or_license="wrong_data",
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    tax_codes = get_cached_tax_codes_or_fetch(config)
    assert len(tax_codes) == 0


def test_checkout_needs_new_fetch(checkout_with_item, address, shipping_method):
    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_method
    config = AvataxConfiguration(
        username_or_account="wrong_data",
        password_or_license="wrong_data",
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_data = generate_request_data_from_checkout(checkout_info, lines, config)
    assert taxes_need_new_fetch(checkout_data, None)


def test_generate_request_data_from_checkout_for_cc(
    checkout_with_item,
    address,
    address_other_country,
    warehouse,
):
    # given
    warehouse.address = address_other_country
    warehouse.is_private = False
    warehouse.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.collection_point = warehouse
    checkout_with_item.save()

    config = AvataxConfiguration(
        username_or_account="wrong_data",
        password_or_license="wrong_data",
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    request_data = generate_request_data_from_checkout(checkout_info, lines, config)

    # then
    expected_address_data = address_other_country.as_data()
    addresses = request_data["createTransactionModel"]["addresses"]
    assert "shipTo" in addresses
    assert "shipFrom" in addresses
    assert addresses["shipTo"] == {
        "line1": expected_address_data.get("street_address_1"),
        "line2": expected_address_data.get("street_address_2"),
        "city": expected_address_data.get("city"),
        "region": expected_address_data.get("country_area"),
        "country": expected_address_data.get("country"),
        "postalCode": expected_address_data.get("postal_code"),
    }


def test_generate_request_data_from_checkout_for_cc_and_single_location(
    checkout_with_item,
    address,
    address_other_country,
    warehouse,
    avatax_config,
):
    # given
    warehouse.address = address_other_country
    warehouse.is_private = False
    warehouse.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.collection_point = warehouse
    checkout_with_item.save()

    address_data = address_other_country.as_data()

    avatax_config.from_street_address = address_data.get("street_address_1")
    avatax_config.from_city = address_data.get("city")
    avatax_config.from_postal_code = address_data.get("postal_code")
    avatax_config.from_country = address_data.get("country")

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    request_data = generate_request_data_from_checkout(
        checkout_info, lines, avatax_config
    )

    # then
    addresses = request_data["createTransactionModel"]["addresses"]
    assert "shipTo" not in addresses
    assert "shipFrom" not in addresses
    assert addresses["singleLocation"] == {
        "line1": address_data.get("street_address_1"),
        "line2": address_data.get("street_address_2"),
        "city": address_data.get("city"),
        "region": address_data.get("country_area"),
        "country": address_data.get("country"),
        "postalCode": address_data.get("postal_code"),
    }


def test_get_checkout_tax_data_with_single_point(
    checkout_with_item,
    warehouse,
    avatax_config,
):
    # given
    expected_address = {
        "line1": "4371 Lucas Knoll Apt. 791",
        "line2": "",
        "city": "BENNETTMOUTH",
        "region": "",
        "country": "PL",
        "postalCode": "53-601",
    }
    address = Address.objects.create(
        street_address_1=expected_address["line1"],
        city=expected_address["city"],
        postal_code=expected_address["postalCode"],
        country=expected_address["country"],
    )
    warehouse.address = address
    warehouse.is_private = False
    warehouse.save()

    avatax_config.from_street_address = expected_address["line1"]
    avatax_config.from_city = expected_address["city"]
    avatax_config.from_postal_code = expected_address["postalCode"]
    avatax_config.from_country = expected_address["country"]

    checkout_with_item.collection_point = warehouse
    checkout_with_item.save()

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    request_data = generate_request_data_from_checkout(
        checkout_info, lines, config=avatax_config
    )

    # then
    addresses = request_data["createTransactionModel"]["addresses"]
    assert addresses["singleLocation"] == expected_address
    assert "shipFrom" not in addresses.keys()
    assert "shipTo" not in addresses.keys()


def test_taxes_need_new_fetch_uses_cached_data(checkout_with_item, address):
    checkout_with_item.shipping_address = address
    config = AvataxConfiguration(
        username_or_account="wrong_data",
        password_or_license="wrong_data",
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_country_area="",
        from_postal_code="53-601",
        from_country="PL",
    )
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_data = generate_request_data_from_checkout(checkout_info, lines, config)
    assert not taxes_need_new_fetch(checkout_data, (checkout_data, None))


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate(
    monkeypatch,
    checkout_with_item,
    address,
    plugin_configuration,
    shipping_zone,
    site_settings,
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(14, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])
    lines, _ = fetch_checkout_lines(checkout_with_item)
    shipping_method = checkout_with_item.shipping_method
    checkout_info = CheckoutInfo(
        checkout=checkout_with_item,
        shipping_address=address,
        billing_address=None,
        channel=checkout_with_item.channel,
        user=None,
        tax_configuration=checkout_with_item.channel.tax_configuration,
        discounts=[],
        manager=manager,
        lines=lines,
        shipping_method=shipping_method,
        shipping_channel_listings=shipping_method.channel_listings.all(),
    )
    checkout_line_info = lines[0]

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.23")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate_for_product_with_charge_taxes_set_to_false(
    monkeypatch,
    checkout_with_item,
    address,
    plugin_configuration,
    shipping_zone,
    site_settings,
    tax_class_zero_rates,
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(12, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    tax_configuration = checkout_with_item.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = False
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    shipping_method = checkout_with_item.shipping_method
    checkout_info = CheckoutInfo(
        checkout=checkout_with_item,
        shipping_address=address,
        billing_address=None,
        channel=checkout_with_item.channel,
        user=None,
        tax_configuration=checkout_with_item.channel.tax_configuration,
        discounts=[],
        manager=manager,
        lines=lines,
        shipping_method=shipping_method,
        shipping_channel_listings=shipping_method.channel_listings.all(),
    )
    checkout_line_info = lines[0]
    product = checkout_line_info.product
    product.tax_class = tax_class_zero_rates
    product.save(update_fields=["tax_class"])

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.0")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate_for_product_type_with_non_taxable_product(
    monkeypatch,
    checkout_with_item,
    address,
    plugin_configuration,
    shipping_zone,
    site_settings,
    product_with_two_variants,
    tax_class_zero_rates,
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"NT": "Non-Taxable Product"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(12, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    product_type = ProductType.objects.create(
        name="non-taxable", kind=ProductTypeKind.NORMAL, tax_class=tax_class_zero_rates
    )
    product2 = product_with_two_variants
    product2.product_type = product_type
    product2.save()
    product_type.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    shipping_method = checkout_with_item.shipping_method

    variant2 = product2.variants.first()
    checkout_info = CheckoutInfo(
        checkout=checkout_with_item,
        shipping_address=address,
        billing_address=None,
        channel=checkout_with_item.channel,
        user=None,
        tax_configuration=checkout_with_item.channel.tax_configuration,
        discounts=[],
        manager=manager,
        shipping_method=shipping_method,
        shipping_channel_listings=shipping_method.channel_listings.all(),
        lines=lines,
    )
    add_variant_to_checkout(checkout_info, variant2, 1)

    assert checkout_with_item.lines.count() == 2

    lines, _ = fetch_checkout_lines(checkout_with_item)
    order = [checkout_with_item.lines.first().variant.pk, variant2.pk]
    lines.sort(key=lambda line: order.index(line.variant.pk))

    # when
    tax_rates = [
        manager.get_checkout_line_tax_rate(
            checkout_info,
            lines,
            checkout_line_info,
            checkout_with_item.shipping_address,
            unit_price,
        )
        for checkout_line_info in lines
    ]
    # then
    assert tax_rates[0] == Decimal("0.23")
    assert tax_rates[1] == Decimal("0.0")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate_checkout_no_shipping_method_default_value_returned(
    monkeypatch, checkout_with_item, address, plugin_configuration, site_settings
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = address
    checkout_with_item.save(update_fields=["shipping_address"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_line_info = lines[0]

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_line_tax_rate_error_in_response(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: {"error": "Example error"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    checkout_line_info = lines[0]

    # when
    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_info,
        lines,
        checkout_line_info,
        checkout_with_item.shipping_address,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_line_tax_rate(
    monkeypatch, order_line, shipping_zone, plugin_configuration, site_settings, address
):
    # given
    order = order_line.order
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )

    unit_price = TaxedMoney(Money(12, "USD"), Money(14, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    product = Product.objects.get(name=order_line.product_name)

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    # when
    tax_rate = manager.get_order_line_tax_rate(
        order,
        product,
        order_line.variant,
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.23")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_line_tax_rate_order_not_valid_default_value_returned(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    product = Product.objects.get(name=order_line.product_name)

    # when
    tax_rate = manager.get_order_line_tax_rate(
        order,
        product,
        order_line.variant,
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_line_tax_rate_error_in_response(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data",
        lambda *_: {"error": "Example error"},
    )
    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    product = Product.objects.get(name=order_line.product_name)

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    # when
    tax_rate = manager.get_order_line_tax_rate(
        order,
        product,
        order_line.variant,
        None,
        unit_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_shipping_tax_rate(
    checkout_with_item, address, plugin_configuration, shipping_zone, site_settings
):
    # given
    site_settings.company_address = address
    site_settings.save()
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.23")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test__get_shipping_tax_rate_handles_multiple_tax_districts(
    avalara_response_for_checkout_with_items_and_shipping, channel_USD
):
    manager = get_plugins_manager(allow_replica=False)
    plugin = manager.get_plugin(AvataxPlugin.PLUGIN_ID, channel_USD.slug)

    # 0.46 == sum of two tax districts
    assert Decimal("0.46") == plugin._get_shipping_tax_rate(
        avalara_response_for_checkout_with_items_and_shipping, Decimal(0.0)
    ).quantize(Decimal(".01"))


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test__get_unit_tax_rate_handles_multiple_tax_districts(
    avalara_response_for_checkout_with_items_and_shipping, channel_USD
):
    manager = get_plugins_manager(allow_replica=False)
    plugin = manager.get_plugin(AvataxPlugin.PLUGIN_ID, channel_USD.slug)

    # 0.36 == sum of two tax districts
    assert Decimal("0.36") == plugin._get_unit_tax_rate(
        avalara_response_for_checkout_with_items_and_shipping, "123", Decimal(0.0)
    ).quantize(Decimal(".01"))


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_shipping_tax_rate_checkout_not_valid_default_value_returned(
    monkeypatch, checkout_with_item, address, plugin_configuration
):
    # given
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = address
    checkout_with_item.save(update_fields=["shipping_address"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_shipping_tax_rate_error_in_response(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_checkout_tax_data",
        lambda *_: {"error": "Example error"},
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_shipping_tax_rate_skip_plugin(
    monkeypatch, checkout_with_item, address, plugin_configuration, shipping_zone
):
    # given
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin",
        lambda *_: True,
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info,
        lines,
        checkout_with_item.shipping_address,
        shipping_price,
    )

    # then
    assert tax_rate == Decimal("0.25")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate(
    order_line, shipping_zone, plugin_configuration, site_settings, address
):
    # given
    site_settings.company_address = address
    site_settings.save()
    order = order_line.order
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.23")


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate_shipping_with_tax_class(
    order_line, shipping_zone, plugin_configuration, site_settings, address
):
    # given
    site_settings.company_address = address
    site_settings.save()
    order = order_line.order
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.shipping_tax_class = method.tax_class
    order.shipping_tax_class_name = method.tax_class.name
    order.shipping_tax_class_metadata = method.tax_class.metadata
    order.shipping_tax_class_private_metadata = method.tax_class.private_metadata  # noqa: E501
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.23")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate_order_not_valid_default_value_returned(
    order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate_error_in_response(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_order_tax_data",
        lambda *_: {"error": "Example error"},
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_shipping_tax_rate_skip_plugin(
    monkeypatch, order_line, shipping_zone, plugin_configuration
):
    # given
    order = order_line.order
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin",
        lambda *_: True,
    )
    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    manager = get_plugins_manager(allow_replica=False)

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save()

    # when
    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)

    # then
    assert tax_rate == Decimal("0.25")


def test_get_plugin_configuration(settings, channel_USD):
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    plugin = manager.get_plugin(AvataxPlugin.PLUGIN_ID, channel_slug=channel_USD.slug)

    configuration_fields = [
        configuration_item["name"] for configuration_item in plugin.configuration
    ]
    assert "Username or account" in configuration_fields
    assert "Password or license" in configuration_fields
    assert "Use sandbox" in configuration_fields
    assert "Company name" in configuration_fields
    assert "Autocommit" in configuration_fields


@patch("saleor.plugins.avatax.plugin.api_get_request")
def test_save_plugin_configuration(
    api_get_request_mock, settings, channel_USD, plugin_configuration
):
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration()
    api_get_request_mock.return_value = {"authenticated": True}
    manager = get_plugins_manager(allow_replica=False)
    manager.save_plugin_configuration(
        AvataxPlugin.PLUGIN_ID,
        channel_USD.slug,
        {
            "active": True,
            "configuration": [
                {"name": "Username or account", "value": "test"},
                {"name": "Password or license", "value": "test"},
            ],
        },
    )
    manager.save_plugin_configuration(
        AvataxPlugin.PLUGIN_ID, channel_USD.slug, {"active": True}
    )
    plugin_configuration = PluginConfiguration.objects.get(
        identifier=AvataxPlugin.PLUGIN_ID
    )
    assert plugin_configuration.active


@patch("saleor.plugins.avatax.plugin.api_get_request")
def test_save_plugin_configuration_authentication_failed(
    api_get_request_mock, settings, channel_USD, plugin_configuration
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(active=False)
    api_get_request_mock.return_value = {"authenticated": False}
    manager = get_plugins_manager(allow_replica=False)

    # when
    with pytest.raises(ValidationError) as e:
        manager.save_plugin_configuration(
            AvataxPlugin.PLUGIN_ID,
            channel_USD.slug,
            {
                "active": True,
                "configuration": [
                    {"name": "Username or account", "value": "test"},
                    {"name": "Password or license", "value": "test"},
                ],
            },
        )

    # then
    assert e._excinfo[1].args[0] == "Authentication failed. Please check provided data."
    plugin_configuration = PluginConfiguration.objects.get(
        identifier=AvataxPlugin.PLUGIN_ID
    )
    assert not plugin_configuration.active


def test_save_plugin_configuration_cannot_be_enabled_without_config(
    settings, plugin_configuration, channel_USD
):
    plugin_configuration(None, None)
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    with pytest.raises(ValidationError):
        manager.save_plugin_configuration(
            AvataxPlugin.PLUGIN_ID, channel_USD.slug, {"active": True}
        )


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_order_confirmed(
    api_post_request_task_mock, order, order_line, plugin_configuration
):
    # given
    plugin_conf = plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )
    conf = {data["name"]: data["value"] for data in plugin_conf.configuration}

    manager = get_plugins_manager(allow_replica=False)

    # when
    manager.order_confirmed(order)

    # then
    address = order.billing_address
    expected_request_data = {
        "createTransactionModel": {
            "companyCode": conf["Company name"],
            "type": TransactionType.INVOICE,
            "lines": [
                {
                    "amount": str(round(order_line.total_price.gross.amount, 3)),
                    "description": order_line.variant.product.name,
                    "discounted": False,
                    "itemCode": order_line.variant.sku,
                    "quantity": order_line.quantity,
                    "taxCode": DEFAULT_TAX_CODE,
                    "taxIncluded": True,
                }
            ],
            "code": str(order.id),
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "customerCode": 0,
            "discount": None,
            "addresses": {
                "shipFrom": {
                    "line1": "Tęczowa 7",
                    "line2": "",
                    "city": "WROCŁAW",
                    "region": "",
                    "country": "PL",
                    "postalCode": "53-603",
                },
                "shipTo": {
                    "line1": address.street_address_1,
                    "line2": address.street_address_2,
                    "city": address.city,
                    "region": address.city_area or "",
                    "country": address.country.code,
                    "postalCode": address.postal_code,
                },
            },
            "commit": False,
            "currencyCode": order.currency,
            "email": order.user_email,
        }
    }

    conf_data = {
        "username_or_account": conf["Username or account"],
        "password_or_license": conf["Password or license"],
        "use_sandbox": conf["Use sandbox"],
        "company_name": conf["Company name"],
        "autocommit": conf["Autocommit"],
        "from_street_address": conf["from_street_address"],
        "from_city": conf["from_city"],
        "from_postal_code": conf["from_postal_code"],
        "from_country": conf["from_country"],
        "from_country_area": conf["from_country_area"],
        "shipping_tax_code": conf["shipping_tax_code"],
    }

    api_post_request_task_mock.assert_called_once_with(
        "https://sandbox-rest.avatax.com/api/v2/transactions/createoradjust",
        expected_request_data,
        conf_data,
        order.pk,
    )


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_with_enabled_flat_rates(
    api_post_request_task_mock,
    checkout_with_item,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    # given
    channel = checkout_with_item.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    manager.preprocess_order_creation(checkout_info, lines)

    # then
    assert not api_post_request_task_mock.called


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_with_country_exception_for_flat_rates(
    api_post_request_task_mock,
    checkout_with_item,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    # given
    channel = checkout_with_item.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    tax_configuration.country_exceptions.create(
        country="PL",
        tax_calculation_strategy=TaxCalculationStrategy.FLAT_RATES,
    )

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    manager.preprocess_order_creation(checkout_info, lines)

    # then
    assert not api_post_request_task_mock.called


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_order_confirmed_skip_when_flat_rate_usage(
    api_post_request_task_mock, order, plugin_configuration
):
    # given
    channel = order.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)

    # when
    manager.order_confirmed(order)

    # then
    assert not api_post_request_task_mock.called


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_order_confirmed_skip_with_country_exception_for_flat_rate(
    api_post_request_task_mock, order, order_line, plugin_configuration
):
    # given
    channel = order.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    tax_configuration.country_exceptions.create(
        country="PL",
        tax_calculation_strategy=TaxCalculationStrategy.FLAT_RATES,
    )

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)

    # when
    manager.order_confirmed(order)

    # then
    assert not api_post_request_task_mock.called


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_order_created_no_lines(
    api_post_request_task_mock, order, plugin_configuration
):
    """Ensure that when order has no lines, the request to avatax api is not sent."""
    # given
    manager = get_plugins_manager(allow_replica=False)

    # when
    manager.order_created(order)

    # then
    api_post_request_task_mock.assert_not_called()


@pytest.mark.vcr
def test_plugin_uses_configuration_from_db(
    plugin_configuration,
    monkeypatch,
    ship_to_pl_address,
    site_settings,
    address,
    checkout_with_item,
    shipping_zone,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    configuration = plugin_configuration()
    manager = get_plugins_manager(allow_replica=False)

    monkeypatch.setattr(
        "saleor.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda _: {"PC040156": "desc"},
    )
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    manager.preprocess_order_creation(checkout_info, lines)

    field_to_update = [
        {"name": "Username or account", "value": "New value"},
        {"name": "Password or license", "value": "Wrong pass"},
    ]
    AvataxPlugin._update_config_items(field_to_update, configuration.configuration)
    configuration.save()

    manager = get_plugins_manager(allow_replica=False)
    with pytest.raises(TaxError):
        manager.preprocess_order_creation(checkout_info, lines)


def test_skip_disabled_plugin(settings, plugin_configuration, channel_USD):
    plugin_configuration(username=None, password=None)
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    plugin: AvataxPlugin = manager.get_plugin(
        AvataxPlugin.PLUGIN_ID, channel_slug=channel_USD.slug
    )

    assert (
        plugin._skip_plugin(
            previous_value=TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))
        )
        is True
    )


def test_get_tax_code_from_object_meta(
    product, settings, plugin_configuration, channel_USD
):
    product.tax_class.store_value_in_metadata(
        {META_CODE_KEY: "KEY", META_DESCRIPTION_KEY: "DESC"}
    )
    plugin_configuration(username=None, password=None)
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_plugins_manager(allow_replica=False)
    tax_type = manager.get_tax_code_from_object_meta(
        product.tax_class, channel_USD.slug
    )

    assert isinstance(tax_type, TaxType)
    assert tax_type.code == "KEY"
    assert tax_type.description == "DESC"


def test_api_get_request_handles_request_errors(product, monkeypatch, avatax_config):
    mocked_response = Mock(side_effect=RequestException())
    monkeypatch.setattr(HTTPSession, "request", mocked_response)

    config = avatax_config
    url = "https://www.avatax.api.com/some-get-path"

    response = api_get_request(
        url, config.username_or_account, config.password_or_license
    )

    assert response == {}
    assert mocked_response.called


def test_api_get_request_handles_json_errors(product, monkeypatch, avatax_config):
    mocked_response = Mock(side_effect=JSONDecodeError("", "", 0))
    monkeypatch.setattr(HTTPSession, "request", mocked_response)

    config = avatax_config
    url = "https://www.avatax.api.com/some-get-path"

    response = api_get_request(
        url, config.username_or_account, config.password_or_license
    )

    assert response == {}
    assert mocked_response.called


def test_api_post_request_handles_request_errors(product, monkeypatch, avatax_config):
    mocked_response = Mock(side_effect=RequestException())
    monkeypatch.setattr(HTTPSession, "request", mocked_response)

    config = avatax_config
    url = "https://www.avatax.api.com/some-get-path"

    response = api_post_request(url, {}, config)

    assert mocked_response.called
    assert response == {}


def test_api_post_request_handles_json_errors(product, monkeypatch, avatax_config):
    mocked_response = Mock(side_effect=JSONDecodeError("", "", 0))
    monkeypatch.setattr(HTTPSession, "request", mocked_response)

    config = avatax_config
    url = "https://www.avatax.api.com/some-get-path"

    response = api_post_request(url, {}, config)

    assert mocked_response.called
    assert response == {}


def test_get_order_request_data_checks_when_taxes_are_included_to_price(
    order_with_lines, shipping_zone, avatax_config
):
    # given
    tax_configuration = order_with_lines.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    method = shipping_zone.shipping_methods.get()
    line = order_with_lines.lines.first()
    line.unit_price_gross_amount = line.unit_price_net_amount
    line.save()

    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_with_lines.shipping_method_name = method.name
    order_with_lines.shipping_method = method
    order_with_lines.save()

    # when
    request_data = get_order_request_data(order_with_lines, avatax_config)
    lines_data = request_data["createTransactionModel"]["lines"]

    # then
    assert all([line for line in lines_data if line["taxIncluded"] is True])


def test_get_order_request_data_uses_correct_address_for_cc(
    order_with_lines,
    site_settings,
    address,
    address_other_country,
    warehouse,
    avatax_config,
):
    # given
    site_settings.include_taxes_in_prices = True
    site_settings.company_address = address
    site_settings.save()

    warehouse.is_private = False
    warehouse.address = address_other_country
    warehouse.save()

    order_with_lines.collection_point = warehouse
    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_with_lines.shipping_method_name = None
    order_with_lines.shipping_method = None
    order_with_lines.save()

    # when
    request_data = get_order_request_data(order_with_lines, avatax_config)

    # then
    expected_address_data = address_other_country.as_data()
    addresses = request_data["createTransactionModel"]["addresses"]
    assert "shipFrom" in addresses
    assert "shipTo" in addresses
    assert addresses["shipTo"] == {
        "line1": expected_address_data.get("street_address_1"),
        "line2": expected_address_data.get("street_address_2"),
        "city": expected_address_data.get("city"),
        "region": expected_address_data.get("country_area"),
        "country": expected_address_data.get("country"),
        "postalCode": expected_address_data.get("postal_code"),
    }


def test_get_order_request_data_uses_correct_address_for_cc_with_single_location(
    order_with_lines,
    site_settings,
    address,
    address_other_country,
    warehouse,
    avatax_config,
):
    # given
    site_settings.include_taxes_in_prices = True
    site_settings.company_address = address
    site_settings.save()

    warehouse.is_private = False
    warehouse.address = address_other_country
    warehouse.save()

    order_with_lines.collection_point = warehouse
    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_with_lines.shipping_method_name = None
    order_with_lines.shipping_method = None
    order_with_lines.save()

    address_data = address_other_country.as_data()

    avatax_config.from_street_address = address_data.get("street_address_1")
    avatax_config.from_city = address_data.get("city")
    avatax_config.from_postal_code = address_data.get("postal_code")
    avatax_config.from_country = address_data.get("country")

    # when
    request_data = get_order_request_data(order_with_lines, avatax_config)

    # then
    addresses = request_data["createTransactionModel"]["addresses"]
    assert "shipFrom" not in addresses
    assert "shipTo" not in addresses
    assert "singleLocation" in addresses
    assert addresses["singleLocation"] == {
        "line1": address_data.get("street_address_1"),
        "line2": "",
        "city": address_data.get("city"),
        "region": address_data.get("country_area"),
        "country": address_data.get("country"),
        "postalCode": address_data.get("postal_code"),
    }


def test_get_order_request_data_for_line_with_already_included_taxes_in_price(
    order_with_lines, shipping_zone, avatax_config
):
    """Test that net price is used when appropriate even if taxes are already known."""
    # given
    prices_entered_with_tax = False
    tax_configuration = order_with_lines.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    method = shipping_zone.shipping_methods.get()
    line_1, line_2 = order_with_lines.lines.all()
    line_1.unit_price_gross_amount = line_1.unit_price_net_amount
    line_1.save()

    assert line_2.unit_price_gross_amount != line_2.unit_price_net_amount

    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_with_lines.shipping_method_name = method.name
    order_with_lines.shipping_method = method
    order_with_lines.save()

    # when
    request_data = get_order_request_data(order_with_lines, avatax_config)

    # then
    lines_data = request_data["createTransactionModel"]["lines"]
    lines_1_data = lines_data[0]
    assert lines_1_data["itemCode"] == line_1.product_sku
    assert lines_1_data["amount"] == str(
        line_1.base_unit_price.amount * line_1.quantity
    )
    assert lines_1_data["taxIncluded"] == prices_entered_with_tax

    lines_2_data = lines_data[1]
    assert lines_2_data["itemCode"] == line_2.product_sku
    assert lines_2_data["amount"] == str(
        line_2.base_unit_price.amount * line_2.quantity
    )
    assert lines_2_data["taxIncluded"] == prices_entered_with_tax


def test_get_order_request_data_confirmed_order_with_voucher(
    order_with_lines, shipping_zone, voucher, avatax_config
):
    tax_configuration = order_with_lines.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    method = shipping_zone.shipping_methods.get()
    line = order_with_lines.lines.first()
    line.unit_price_gross_amount = line.unit_price_net_amount
    line.save()

    order_with_lines.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )

    order_with_lines.status = OrderStatus.UNFULFILLED
    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_set_shipping_method(order_with_lines, method)
    order_with_lines.save(
        update_fields=[
            "status",
            "shipping_address",
            "shipping_method_name",
            "shipping_method",
            "shipping_tax_class",
            "shipping_tax_class_name",
            "shipping_tax_class_metadata",
            "shipping_tax_class_private_metadata",
        ]
    )

    request_data = get_order_request_data(order_with_lines, avatax_config)
    lines_data = request_data["createTransactionModel"]["lines"]

    # extra one from shipping data
    assert len(lines_data) == order_with_lines.lines.count() + 1
    for line_data in lines_data[:-1]:
        assert line_data["discounted"] is True
    # shipping line shouldn't be discounted
    assert lines_data[-1]["discounted"] is False


def test_get_order_request_data_confirmed_order_with_promotion(
    order_line_on_promotion, shipping_zone, avatax_config
):
    # given
    order = order_line_on_promotion.order
    tax_configuration = order.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    method = shipping_zone.shipping_methods.get()
    line = order.lines.first()
    line.unit_price_gross_amount = line.unit_price_net_amount
    line.save()

    order.status = OrderStatus.UNFULFILLED
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save(
        update_fields=[
            "status",
            "shipping_address",
            "shipping_method_name",
            "shipping_method",
            "shipping_tax_class",
            "shipping_tax_class_name",
            "shipping_tax_class_metadata",
            "shipping_tax_class_private_metadata",
        ]
    )

    # when
    request_data = get_order_request_data(order, avatax_config)

    # then
    lines_data = request_data["createTransactionModel"]["lines"]

    # extra one from shipping data
    assert len(lines_data) == order.lines.count() + 1


def test_get_order_request_data_draft_order_with_voucher(
    order_with_lines, shipping_zone, voucher, avatax_config
):
    # given
    tax_configuration = order_with_lines.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    method = shipping_zone.shipping_methods.get()
    line = order_with_lines.lines.first()
    line.base_unit_price_amount = line.unit_price_net_amount
    line.undiscounted_base_unit_price_amount = line.unit_price_gross_amount
    line.save()

    order_with_lines.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal("10.0"),
        name=voucher.code,
        currency="USD",
        amount_value=Decimal("10.0"),
    )

    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_set_shipping_method(order_with_lines, method)
    order_with_lines.save(
        update_fields=[
            "status",
            "shipping_address",
            "shipping_method_name",
            "shipping_method",
            "shipping_tax_class",
            "shipping_tax_class_name",
            "shipping_tax_class_metadata",
            "shipping_tax_class_private_metadata",
        ]
    )

    # when
    request_data = get_order_request_data(order_with_lines, avatax_config)

    # then
    lines_data = request_data["createTransactionModel"]["lines"]

    # lines + shipping
    assert len(lines_data) == order_with_lines.lines.count() + 1
    for line_data in lines_data[:-1]:
        assert line_data["discounted"] is True
    # shipping line shouldn't be discounted
    assert lines_data[-1]["discounted"] is False
    assert Decimal(lines_data[-1]["amount"]) != Decimal("0")


def test_get_order_request_data_draft_order_with_shipping_voucher(
    order_with_lines, shipping_zone, voucher_free_shipping, avatax_config
):
    # given
    tax_configuration = order_with_lines.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    method = shipping_zone.shipping_methods.get()
    method_listing = method.channel_listings.get(channel=order_with_lines.channel)
    line = order_with_lines.lines.first()
    line.base_unit_price_amount = line.unit_price_net_amount
    line.undiscounted_base_unit_price_amount = line.unit_price_gross_amount
    line.save()

    order_with_lines.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("100.0"),
        name=voucher_free_shipping.code,
        currency="USD",
        amount_value=method_listing.price.amount,
    )

    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_set_shipping_method(order_with_lines, method)
    order_with_lines.base_shipping_price = zero_money(order_with_lines.currency)
    order_with_lines.voucher = voucher_free_shipping
    order_with_lines.save(
        update_fields=[
            "status",
            "voucher",
            "base_shipping_price_amount",
            "shipping_address",
            "shipping_method_name",
            "shipping_method",
            "shipping_tax_class",
            "shipping_tax_class_name",
            "shipping_tax_class_metadata",
            "shipping_tax_class_private_metadata",
        ]
    )

    # when
    request_data = get_order_request_data(order_with_lines, avatax_config)

    # then
    lines_data = request_data["createTransactionModel"]["lines"]

    # only lines, shipping is not added as after discount shipping price is 0
    assert len(lines_data) == order_with_lines.lines.count()
    for line_data in lines_data:
        assert line_data["discounted"] is False


def test_get_order_request_data_draft_order_shipping_voucher_amount_too_high(
    order_with_lines, shipping_zone, voucher_free_shipping, avatax_config
):
    """Test discount behavior when the voucher amount is higher than the order total."""
    # given
    tax_configuration = order_with_lines.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    method = shipping_zone.shipping_methods.get()
    method_listing = method.channel_listings.get(channel=order_with_lines.channel)
    line = order_with_lines.lines.first()
    line.base_unit_price_amount = line.unit_price_net_amount
    line.undiscounted_base_unit_price_amount = line.unit_price_gross_amount
    line.save()

    order_with_lines.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("100.0"),
        name=voucher_free_shipping.code,
        currency="USD",
        amount_value=method_listing.price.amount + Decimal("10.0"),
    )

    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.shipping_address = order_with_lines.billing_address.get_copy()
    order_set_shipping_method(order_with_lines, method)
    order_with_lines.base_shipping_price = zero_money(order_with_lines.currency)
    order_with_lines.voucher = voucher_free_shipping
    order_with_lines.save(
        update_fields=[
            "status",
            "voucher",
            "base_shipping_price_amount",
            "shipping_address",
            "shipping_method_name",
            "shipping_method",
            "shipping_tax_class",
            "shipping_tax_class_name",
            "shipping_tax_class_metadata",
            "shipping_tax_class_private_metadata",
        ]
    )

    # when
    request_data = get_order_request_data(order_with_lines, avatax_config)

    # then
    lines_data = request_data["createTransactionModel"]["lines"]

    # only lines, shipping is not added as after discount shipping price is 0
    assert len(lines_data) == order_with_lines.lines.count()
    for line_data in lines_data[:-1]:
        assert line_data["discounted"] is False


def test_get_order_request_data_draft_order_on_promotion(
    order_line_on_promotion,
    shipping_zone,
    catalogue_promotion_with_single_rule,
    avatax_config,
):
    # given
    order = order_line_on_promotion.order
    tax_configuration = order.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = True
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    method = shipping_zone.shipping_methods.get()
    line = order.lines.first()
    line.base_unit_price_amount = line.unit_price_net_amount
    line.undiscounted_base_unit_price_amount = line.unit_price_gross_amount
    line.save()

    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.id)
    predicate = {"variantPredicate": {"ids": [variant_id]}}
    rule = catalogue_promotion_with_single_rule.rules.first()
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])

    order.status = OrderStatus.DRAFT
    order.shipping_address = order.billing_address.get_copy()
    order_set_shipping_method(order, method)
    order.save(
        update_fields=[
            "status",
            "shipping_address",
            "shipping_method_name",
            "shipping_method",
            "shipping_tax_class",
            "shipping_tax_class_name",
            "shipping_tax_class_metadata",
            "shipping_tax_class_private_metadata",
        ]
    )

    # when
    request_data = get_order_request_data(order, avatax_config)

    # then
    lines_data = request_data["createTransactionModel"]["lines"]

    # lines + one line for shipping data
    assert len(lines_data) == order.lines.count() + 1


@patch("saleor.plugins.avatax.get_order_request_data")
@patch("saleor.plugins.avatax.get_cached_response_or_fetch")
def test_get_order_tax_data(
    get_cached_response_or_fetch_mock,
    get_order_request_data_mock,
    order,
    plugin_configuration,
):
    # given
    conf = plugin_configuration()

    return_value = {"id": 0, "code": "3d4893da", "companyId": 123}
    get_cached_response_or_fetch_mock.return_value = return_value

    # when
    response = get_order_tax_data(order, conf)

    # then
    get_order_request_data_mock.assert_called_once_with(order, conf)
    assert response == return_value


@pytest.mark.vcr
@patch("saleor.plugins.avatax.cache.set")
def test_get_order_tax_data_with_single_location(
    mock_cache_set,
    order_line,
    warehouse,
    avatax_config,
):
    # given
    address = Address.objects.create(
        street_address_1="4371 Lucas Knoll Apt. 791",
        city="BENNETTMOUTH",
        postal_code="53-601",
        country="PL",
    )
    warehouse.address = address
    warehouse.is_private = False
    warehouse.save()

    order = order_line.order
    order.collection_point = warehouse
    order.save()

    address_data = warehouse.address.as_data()
    avatax_config.from_street_address = address_data.get("street_address_1")
    avatax_config.from_city = address_data.get("city")
    avatax_config.from_postal_code = address_data.get("postal_code")
    avatax_config.from_country = address_data.get("country")

    # when
    response = get_order_tax_data(order, avatax_config)

    # then
    assert len(response.get("addresses", [])) == 1


def test_get_order_tax_data_empty_data(
    order,
    plugin_configuration,
):
    # given
    conf = plugin_configuration()

    # when
    response = get_order_tax_data(order, conf)

    # then
    assert response is None


@patch("saleor.plugins.avatax.get_order_request_data")
@patch("saleor.plugins.avatax.get_cached_response_or_fetch")
def test_get_order_tax_data_raised_error(
    get_cached_response_or_fetch_mock,
    get_order_request_data_mock,
    order,
    plugin_configuration,
):
    # given
    conf = plugin_configuration()

    return_value = {"error": {"message": "test error"}}
    get_cached_response_or_fetch_mock.return_value = return_value

    # when
    with pytest.raises(TaxError) as e:
        get_order_tax_data(order, conf)

    # then
    assert e._excinfo[1].args[0] == return_value["error"]


@pytest.mark.vcr
@patch("saleor.plugins.avatax.cache.set")
def test_get_order_tax_data_address_error_logging(
    mock_cache_set,
    order_line,
    avatax_config,
    address,
    caplog,
):
    # given
    order = order_line.order
    invalid_postal_code = "invalid postal code"
    address.validation_skipped = True
    address.postal_code = invalid_postal_code
    address.save(update_fields=["postal_code", "validation_skipped"])
    order.shipping_address = address
    order.billing_address = address
    order.save(update_fields=["shipping_address", "billing_address"])

    avatax_config.from_postal_code = invalid_postal_code

    # when
    with pytest.raises(TaxError):
        get_order_tax_data(order, avatax_config)

    # then
    assert f"Unable to calculate taxes for order {order.pk}" in caplog.text
    assert (
        f"Fetching tax data for order with address validation skipped. "
        f"Address ID: {address.pk}" in caplog.text
    )


@pytest.mark.parametrize(
    (
        "shipping_address_none",
        "shipping_method_none",
        "billing_address_none",
        "is_shipping_required",
        "expected_is_valid",
    ),
    [
        (False, False, False, True, True),
        (True, True, False, True, False),
        (True, True, False, False, True),
        (False, True, False, True, False),
        (True, False, False, True, False),
    ],
)
def test_validate_address_details(
    shipping_address_none,
    shipping_method_none,
    billing_address_none,
    is_shipping_required,
    expected_is_valid,
    checkout_ready_to_complete,
):
    shipping_address = checkout_ready_to_complete.shipping_address
    shipping_address = None if shipping_address_none else shipping_address
    billing_address = checkout_ready_to_complete.billing_address
    billing_address = None if billing_address_none else billing_address
    address = shipping_address or billing_address
    shipping_method = checkout_ready_to_complete.shipping_method
    shipping_method = None if shipping_method_none else shipping_method
    is_valid = _validate_address_details(
        shipping_address, is_shipping_required, address, shipping_method
    )
    assert is_valid is expected_is_valid


def test_validate_order_no_lines(order):
    # given
    assert not order.lines.all()

    # when
    response = _validate_order(order)

    # then
    assert response is False


def test_validate_order_not_shipping_required_no_shipping_method(order_line, address):
    # given
    order = order_line.order
    order_line.is_shipping_required = False
    order_line.save(update_fields=["is_shipping_required"])

    order.shipping_method = None
    order.shipping_address = address
    order.billing_address = address
    order.save(update_fields=["shipping_address", "billing_address", "shipping_method"])

    # when
    response = _validate_order(order)

    # then
    assert response is True


def test_validate_order_click_and_collect(order_line, address, warehouse):
    # given
    warehouse.is_private = False
    warehouse.save(update_fields=["is_private"])
    order = order_line.order
    order.collection_point = warehouse
    order.shipping_method = None
    order.shipping_address = None
    order.billing_address = address
    order.save(
        update_fields=[
            "shipping_address",
            "billing_address",
            "shipping_method",
            "collection_point",
        ]
    )

    # when
    response = _validate_order(order)

    # then
    assert response is True


def test_validate_checkout_click_and_collect(
    user_checkout_with_items_for_cc, address, warehouse
):
    # given
    warehouse.is_private = False
    warehouse.save(update_fields=["is_private"])
    user_checkout_with_items_for_cc.collection_point = warehouse
    user_checkout_with_items_for_cc.shipping_method = None
    user_checkout_with_items_for_cc.shipping_address = None
    user_checkout_with_items_for_cc.billing_address = address
    user_checkout_with_items_for_cc.save(
        update_fields=[
            "shipping_address",
            "billing_address",
            "shipping_method",
            "collection_point",
        ]
    )
    lines_info, _ = fetch_checkout_lines(user_checkout_with_items_for_cc)
    checkout_info = fetch_checkout_info(
        user_checkout_with_items_for_cc,
        lines_info,
        get_plugins_manager(allow_replica=False),
    )

    # when
    response = _validate_checkout(checkout_info, lines_info)

    # then
    assert response is True


def test_generate_request_data_from_checkout_lines_uses_tax_code_from_product_tax_class(
    settings, channel_USD, plugin_configuration, checkout_with_item, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = checkout_with_item.lines.first()
    tax_class = line.variant.product.tax_class
    tax_code = "banana"
    tax_class.store_value_in_metadata(
        {META_CODE_KEY: tax_code, META_DESCRIPTION_KEY: "tax_description"}
    )
    tax_class.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, get_plugins_manager(allow_replica=False)
    )

    config = avatax_config

    # when
    lines_data = generate_request_data_from_checkout_lines(checkout_info, lines, config)

    # then
    assert lines_data[0]["taxCode"] == tax_code


def test_generate_request_data_from_checkout_lines_uses_tax_code_from_product_type_tax_class(  # noqa: E501
    settings, channel_USD, plugin_configuration, checkout_with_item, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.tax_class = None
    product.save()

    tax_class = product.product_type.tax_class
    tax_code = "banana"
    tax_class.store_value_in_metadata(
        {META_CODE_KEY: tax_code, META_DESCRIPTION_KEY: "tax_description"}
    )
    tax_class.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, get_plugins_manager(allow_replica=False)
    )

    config = avatax_config

    # when
    lines_data = generate_request_data_from_checkout_lines(checkout_info, lines, config)

    # then
    assert lines_data[0]["taxCode"] == tax_code


def test_generate_request_data_from_checkout_lines_sets_different_tax_code_for_zero_amount(  # noqa: E501
    settings, channel_USD, plugin_configuration, checkout_with_item, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = checkout_with_item.lines.first()
    variant = line.variant
    variant.channel_listings.all().update(price_amount=Decimal("0"))
    variant.product.tax_class.store_value_in_metadata(
        {META_CODE_KEY: "taxcode", META_DESCRIPTION_KEY: "tax_description"}
    )
    variant.product.tax_class.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, get_plugins_manager(allow_replica=False)
    )

    config = avatax_config

    # when
    lines_data = generate_request_data_from_checkout_lines(checkout_info, lines, config)

    # then
    assert lines_data[0]["amount"] == "0.00"
    assert lines_data[0]["taxCode"] == DEFAULT_TAX_CODE


def test_generate_request_data_from_checkout_lines_sets_different_tax_code_only_for_zero_amount(  # noqa: E501
    settings, channel_USD, plugin_configuration, checkout_with_item, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = checkout_with_item.lines.first()
    line.quantity = 1
    line.save()

    variant = line.variant
    variant.channel_listings.all().update(price_amount=Decimal("11"))
    variant.product.tax_class.store_value_in_metadata(
        {META_CODE_KEY: "taxcode", META_DESCRIPTION_KEY: "tax_description"}
    )
    variant.product.tax_class.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, get_plugins_manager(allow_replica=False)
    )

    config = avatax_config

    # when
    lines_data = generate_request_data_from_checkout_lines(checkout_info, lines, config)

    # then
    assert lines_data[0]["amount"] == "11.00"
    assert lines_data[0]["taxCode"] == "taxcode"


def test_generate_request_data_from_checkout_lines_with_collection_point(
    settings,
    channel_USD,
    plugin_configuration,
    checkout_with_item,
    avatax_config,
    warehouse,
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = checkout_with_item.lines.first()
    line.quantity = 1
    line.save()

    variant = line.variant
    variant.channel_listings.all().update(price_amount=Decimal("11"))
    variant.product.tax_class.store_value_in_metadata(
        {META_CODE_KEY: "taxcode", META_DESCRIPTION_KEY: "tax_description"}
    )
    variant.product.tax_class.save()

    checkout_with_item.shipping_method = None
    checkout_with_item.collection_point = warehouse
    checkout_with_item.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, get_plugins_manager(allow_replica=False)
    )
    config = avatax_config

    # when
    lines_data = generate_request_data_from_checkout_lines(checkout_info, lines, config)

    # then
    assert len(lines_data) == checkout_with_item.lines.count()


def test_generate_request_data_from_checkout_lines_with_shipping_method(
    settings,
    channel_USD,
    plugin_configuration,
    checkout_with_item,
    avatax_config,
    shipping_method,
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = checkout_with_item.lines.first()
    line.quantity = 1
    line.save()

    variant = line.variant
    variant.channel_listings.all().update(price_amount=Decimal("11"))
    variant.product.tax_class.store_value_in_metadata(
        {META_CODE_KEY: "taxcode", META_DESCRIPTION_KEY: "tax_description"}
    )
    variant.product.tax_class.save()

    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.collection_point = None
    checkout_with_item.save()

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, get_plugins_manager(allow_replica=False)
    )
    config = avatax_config

    # when
    lines_data = generate_request_data_from_checkout_lines(checkout_info, lines, config)

    # then
    assert len(lines_data) == checkout_with_item.lines.count() + 1
    assert lines_data[-1]["itemCode"] == "Shipping"


def test_generate_request_data_from_checkout_lines_adds_lines_with_taxes_disabled_for_line(  # noqa: E501
    settings,
    channel_USD,
    plugin_configuration,
    checkout_with_item,
    avatax_config,
    tax_class_zero_rates,
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = checkout_with_item.lines.first()
    line.variant.product.tax_class = tax_class_zero_rates
    line.variant.product.save(update_fields=["tax_class"])

    checkout_with_item.shipping_method = None
    checkout_with_item.save(update_fields=["shipping_method"])

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, get_plugins_manager(allow_replica=False)
    )

    # when
    lines_data = generate_request_data_from_checkout_lines(
        checkout_info, lines, avatax_config
    )

    # then
    assert len(lines_data) == len(checkout_with_item.lines.all())


def test_get_order_lines_data_gets_tax_code_from_product_tax_class(
    settings, channel_USD, plugin_configuration, order_with_lines, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = order_with_lines.lines.first()
    tax_class = line.variant.product.tax_class
    tax_code = "banana"
    tax_class.store_value_in_metadata(
        {META_CODE_KEY: tax_code, META_DESCRIPTION_KEY: "tax_description"}
    )
    tax_class.save()

    # when
    lines_data = get_order_lines_data(order_with_lines, avatax_config, discounted=False)

    # then
    assert lines_data[0]["taxCode"] == tax_code


def test_get_order_lines_data_gets_tax_code_from_product_type_tax_class(
    settings, channel_USD, plugin_configuration, order_with_lines, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = order_with_lines.lines.first()
    product = line.variant.product
    product.tax_class = None
    product.save()

    tax_class = product.product_type.tax_class
    tax_code = "banana"
    tax_class.store_value_in_metadata(
        {META_CODE_KEY: tax_code, META_DESCRIPTION_KEY: "tax_description"}
    )
    tax_class.save()

    # when
    lines_data = get_order_lines_data(order_with_lines, avatax_config, discounted=False)

    # then
    assert lines_data[0]["taxCode"] == tax_code


def test_get_order_lines_data_sets_different_tax_code_for_zero_amount(
    settings, channel_USD, plugin_configuration, order_with_lines, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = order_with_lines.lines.first()
    line.base_unit_price_amount = Decimal("0")
    line.undiscounted_base_unit_price_amount = Decimal("0")
    line.save(
        update_fields=[
            "base_unit_price_amount",
            "undiscounted_base_unit_price_amount",
        ]
    )
    variant = line.variant
    variant.product.tax_class.store_value_in_metadata(
        {META_CODE_KEY: "taxcode", META_DESCRIPTION_KEY: "tax_description"}
    )
    variant.product.tax_class.save()

    # when
    lines_data = get_order_lines_data(order_with_lines, avatax_config, discounted=False)

    # then
    assert lines_data[0]["amount"] == "0.000"
    assert lines_data[0]["taxCode"] == DEFAULT_TAX_CODE


def test_get_order_lines_data_with_discounted(
    settings, channel_USD, plugin_configuration, order, order_line, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    order_line.unit_price_gross_amount = Decimal("10")
    order_line.undiscounted_unit_price_gross_amount = Decimal("20")
    order_line.quantity = 1
    order_line.save(
        update_fields=[
            "quantity",
            "unit_price_gross_amount",
            "undiscounted_unit_price_gross_amount",
        ]
    )
    variant = order_line.variant
    variant.product.tax_class.store_value_in_metadata(
        {META_CODE_KEY: "taxcode", META_DESCRIPTION_KEY: "tax_description"}
    )
    variant.product.tax_class.save()

    # when
    lines_data = get_order_lines_data(order, avatax_config, discounted=True)

    # then
    assert len(lines_data) == 1
    line_data = lines_data[0]
    assert line_data["amount"] == "12.300"
    assert line_data["discounted"] is True


def test_get_order_lines_data_sets_different_tax_code_only_for_zero_amount(
    settings, channel_USD, plugin_configuration, order_with_lines, avatax_config
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    line = order_with_lines.lines.first()
    line.quantity = 1
    line.base_unit_price_amount = Decimal("10.0")
    line.undiscounted_base_unit_price_amount = Decimal("10.0")
    line.save(
        update_fields=[
            "quantity",
            "base_unit_price_amount",
            "undiscounted_base_unit_price_amount",
        ]
    )
    variant = line.variant
    variant.product.tax_class.store_value_in_metadata(
        {META_CODE_KEY: "taxcode", META_DESCRIPTION_KEY: "tax_description"}
    )
    variant.product.tax_class.save()

    config = avatax_config

    # when
    lines_data = get_order_lines_data(order_with_lines, config, discounted=False)

    # then
    assert lines_data[0]["amount"] == "10.000"
    assert lines_data[0]["taxCode"] == "taxcode"


def test_get_order_lines_data_adds_lines_with_taxes_disabled_for_line(
    settings,
    channel_USD,
    plugin_configuration,
    order_with_lines,
    avatax_config,
    tax_class_zero_rates,
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)

    order_with_lines.base_shipping_price_amount = Decimal("0")
    order_with_lines.save(update_fields=["base_shipping_price_amount"])

    line = order_with_lines.lines.first()
    line.variant.product.tax_class = tax_class_zero_rates
    line.variant.product.save(update_fields=["tax_class"])

    # when
    lines_data = get_order_lines_data(order_with_lines, avatax_config, discounted=False)

    # then
    assert len(lines_data) == len(order_with_lines.lines.all())


@patch("saleor.plugins.avatax.plugin.get_checkout_tax_data")
def test_calculate_checkout_shipping_validates_checkout(
    mocked_func, settings, channel_USD, plugin_configuration, checkout_with_item
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)

    checkout.shipping_method = None
    checkout.save(update_fields=["shipping_method"])

    for line in lines:
        line.product_type.is_shipping_required = True
        line.product_type.save()

    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    manager.calculate_checkout_shipping(
        checkout_info,
        lines,
        checkout.shipping_address,
    )

    # then
    assert not mocked_func.called


@patch("saleor.plugins.avatax.plugin.get_checkout_tax_data")
def test_calculate_checkout_line_total_validates_checkout(
    mocked_func, settings, channel_USD, plugin_configuration, checkout_with_item
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)

    checkout.shipping_method = None
    checkout.save(update_fields=["shipping_method"])

    for line in lines:
        line.product_type.is_shipping_required = True
        line.product_type.save()

    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        lines[0],
        checkout.shipping_address,
    )

    # then
    assert not mocked_func.called


@patch("saleor.plugins.avatax.plugin.get_checkout_tax_data")
def test_calculate_checkout_line_unit_price_validates_checkout(
    mocked_func, settings, channel_USD, plugin_configuration, checkout_with_item
):
    # given
    settings.PLUGINS = ["saleor.plugins.avatax.plugin.AvataxPlugin"]
    plugin_configuration(channel=channel_USD)
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_with_item
    lines, _ = fetch_checkout_lines(checkout)

    checkout.shipping_method = None
    checkout.save(update_fields=["shipping_method"])

    for line in lines:
        line.product_type.is_shipping_required = True
        line.product_type.save()

    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    manager.calculate_checkout_line_unit_price(
        checkout_info,
        lines,
        lines[0],
        checkout.shipping_address,
    )

    # then
    assert not mocked_func.called


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_with_tax_app_id_as_plugin(
    api_post_request_task_mock,
    checkout_with_item,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    # given
    channel = checkout_with_item.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.tax_app_id = "test_app"
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    manager.preprocess_order_creation(checkout_info, lines)

    # then
    api_post_request_task_mock.assert_not_called()


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_preprocess_order_creation_with_country_exception_tax_app_id_plugin(
    api_post_request_task_mock,
    checkout_with_item,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    # given
    channel = checkout_with_item.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_app_id = None
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    tax_configuration.country_exceptions.create(
        country="PL",
        tax_calculation_strategy=TaxCalculationStrategy.TAX_APP,
        tax_app_id="test_app",
    )

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    manager.preprocess_order_creation(checkout_info, lines)

    # then
    api_post_request_task_mock.assert_not_called()


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_order_confirmed_skip_with_tax_app_id_as_plugin(
    api_post_request_task_mock, order, plugin_configuration
):
    # given
    channel = order.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tax_configuration.tax_app_id = "test_app"
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)

    # when
    manager.order_confirmed(order)

    # then
    api_post_request_task_mock.assert_not_called()


@patch("saleor.plugins.avatax.plugin.api_post_request_task.delay")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_order_confirmed_skip_with_country_exception_tax_app_id_plugin(
    api_post_request_task_mock, order, order_line, plugin_configuration
):
    # given
    channel = order.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_app_id = None
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    tax_configuration.country_exceptions.create(
        country="PL",
        tax_calculation_strategy=TaxCalculationStrategy.TAX_APP,
        tax_app_id="test_app",
    )

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)

    # when
    manager.order_confirmed(order)

    # then
    api_post_request_task_mock.assert_not_called()


@patch("saleor.plugins.avatax.plugin.get_order_tax_data")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_order_tax_data_set_tax_error(
    mock_get_order_tax_data, order, order_line, plugin_configuration
):
    # given
    mock_get_order_tax_data.return_value = None

    channel = order.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_app_id = AvataxPlugin.PLUGIN_IDENTIFIER
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)

    # when
    manager.calculate_order_total(order, order.lines.all())

    # then
    assert order.tax_error == "Empty tax data."


@patch("saleor.plugins.avatax.plugin.get_checkout_tax_data")
@override_settings(PLUGINS=["saleor.plugins.avatax.plugin.AvataxPlugin"])
def test_get_checkout_tax_data_set_tax_error(
    mock_get_checkout_tax_data,
    checkout_with_item,
    address,
    ship_to_pl_address,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    # given
    mock_get_checkout_tax_data.return_value = None

    channel = checkout_with_item.channel
    tax_configuration = channel.tax_configuration
    tax_configuration.tax_app_id = AvataxPlugin.PLUGIN_IDENTIFIER
    tax_configuration.save()
    tax_configuration.country_exceptions.all().delete()

    plugin_configuration(
        from_street_address="Tęczowa 7",
        from_city="WROCŁAW",
        from_postal_code="53-603",
        from_country="PL",
        shipping_tax_code="FR00001",
    )

    manager = get_plugins_manager(allow_replica=True)
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = ship_to_pl_address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)

    # when
    manager.calculate_checkout_total(
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    )

    # then
    assert checkout_with_item.tax_error == "Empty tax data."
