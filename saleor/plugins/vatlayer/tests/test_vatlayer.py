from decimal import Decimal
from unittest.mock import Mock
from urllib.parse import urlparse

import pytest
from django.core.exceptions import ValidationError
from django_countries.fields import Country
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ....checkout import CheckoutLineInfo, calculations
from ....checkout.utils import add_variant_to_checkout, fetch_checkout_lines
from ....core.prices import quantize_price
from ....core.taxes import zero_taxed_money
from ....product.models import Product
from ...manager import get_plugins_manager
from ...models import PluginConfiguration
from ...vatlayer import (
    DEFAULT_TAX_RATE_NAME,
    apply_tax_to_price,
    get_tax_rate_by_name,
    get_taxed_shipping_price,
    get_taxes_for_country,
)
from ..plugin import VatlayerPlugin


def get_url_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    return get_url_path(response["Location"])


@pytest.fixture
def compare_taxes():
    def fun(taxes_1, taxes_2):
        assert len(taxes_1) == len(taxes_2)

        for rate_name, tax in taxes_1.items():
            value_1 = tax["value"]
            value_2 = taxes_2.get(rate_name)["value"]
            assert value_1 == value_2

    return fun


def test_get_tax_rate_by_name(taxes):
    rate_name = "pharmaceuticals"
    tax_rate = get_tax_rate_by_name(rate_name, taxes)

    assert tax_rate == taxes[rate_name]["value"]


def test_get_tax_rate_by_name_fallback_to_standard(taxes):
    rate_name = "unexisting tax rate"
    tax_rate = get_tax_rate_by_name(rate_name, taxes)

    assert tax_rate == taxes[DEFAULT_TAX_RATE_NAME]["value"]


def test_get_tax_rate_by_name_empty_taxes(product):
    rate_name = "unexisting tax rate"
    tax_rate = get_tax_rate_by_name(rate_name)

    assert tax_rate == 0


@pytest.mark.parametrize(
    "price, charge_taxes, expected_price",
    [
        (
            Money(10, "USD"),
            False,
            TaxedMoney(net=Money(10, "USD"), gross=Money(10, "USD")),
        ),
        (
            Money(10, "USD"),
            True,
            TaxedMoney(net=Money("8.13", "USD"), gross=Money(10, "USD")),
        ),
    ],
)
def test_get_taxed_shipping_price(
    site_settings, vatlayer, price, charge_taxes, expected_price
):
    site_settings.charge_taxes_on_shipping = charge_taxes
    site_settings.save()

    shipping_price = get_taxed_shipping_price(price, taxes=vatlayer)

    assert shipping_price == expected_price


def test_get_taxes_for_country(vatlayer, compare_taxes):
    taxes = get_taxes_for_country(Country("PL"))
    compare_taxes(taxes, vatlayer)


def test_apply_tax_to_price_do_not_include_tax(site_settings, taxes):
    site_settings.include_taxes_in_prices = False
    site_settings.save()

    money = Money(100, "USD")
    assert apply_tax_to_price(taxes, "standard", money) == TaxedMoney(
        net=Money(100, "USD"), gross=Money(123, "USD")
    )
    assert apply_tax_to_price(taxes, "medical", money) == TaxedMoney(
        net=Money(100, "USD"), gross=Money(108, "USD")
    )

    taxed_money = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))
    assert apply_tax_to_price(taxes, "standard", taxed_money) == TaxedMoney(
        net=Money(100, "USD"), gross=Money(123, "USD")
    )
    assert apply_tax_to_price(taxes, "medical", taxed_money) == TaxedMoney(
        net=Money(100, "USD"), gross=Money(108, "USD")
    )


def test_apply_tax_to_price_do_not_include_tax_fallback_to_standard_rate(
    site_settings, taxes
):
    site_settings.include_taxes_in_prices = False
    site_settings.save()

    money = Money(100, "USD")
    taxed_money = TaxedMoney(net=Money(100, "USD"), gross=Money(123, "USD"))
    assert apply_tax_to_price(taxes, "space suits", money) == taxed_money


def test_apply_tax_to_price_include_tax(taxes):
    money = Money(100, "USD")
    assert apply_tax_to_price(taxes, "standard", money) == TaxedMoney(
        net=Money("81.30", "USD"), gross=Money(100, "USD")
    )
    assert apply_tax_to_price(taxes, "medical", money) == TaxedMoney(
        net=Money("92.59", "USD"), gross=Money(100, "USD")
    )


def test_apply_tax_to_price_include_fallback_to_standard_rate(taxes):
    money = Money(100, "USD")
    assert apply_tax_to_price(taxes, "space suits", money) == TaxedMoney(
        net=Money("81.30", "USD"), gross=Money(100, "USD")
    )

    taxed_money = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))
    assert apply_tax_to_price(taxes, "space suits", taxed_money) == TaxedMoney(
        net=Money("81.30", "USD"), gross=Money(100, "USD")
    )


def test_apply_tax_to_price_raise_typeerror_for_invalid_type(taxes):
    with pytest.raises(TypeError):
        assert apply_tax_to_price(taxes, "standard", 100)


def test_apply_tax_to_price_no_taxes_return_taxed_money():
    money = Money(100, "USD")
    taxed_money = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))

    assert apply_tax_to_price(None, "standard", money) == taxed_money
    assert apply_tax_to_price(None, "medical", taxed_money) == taxed_money


def test_apply_tax_to_price_no_taxes_return_taxed_money_range():
    money_range = MoneyRange(Money(100, "USD"), Money(200, "USD"))
    taxed_money_range = TaxedMoneyRange(
        TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD")),
        TaxedMoney(net=Money(200, "USD"), gross=Money(200, "USD")),
    )

    assert apply_tax_to_price(None, "standard", money_range) == taxed_money_range
    assert apply_tax_to_price(None, "standard", taxed_money_range) == taxed_money_range


def test_apply_tax_to_price_no_taxes_raise_typeerror_for_invalid_type():
    with pytest.raises(TypeError):
        assert apply_tax_to_price(None, "standard", 100)


def test_vatlayer_plugin_caches_taxes(
    vatlayer, monkeypatch, product, address, channel_USD
):
    mocked_taxes = Mock(wraps=get_taxes_for_country)
    monkeypatch.setattr(
        "saleor.plugins.vatlayer.plugin.get_taxes_for_country", mocked_taxes
    )

    manager = get_plugins_manager()
    plugin = manager.get_plugin(VatlayerPlugin.PLUGIN_ID)
    variant = product.variants.first()
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    price = variant.get_price(product, [], channel_USD, channel_listing, None)
    address.country = Country("de")
    plugin.apply_taxes_to_product(
        product, price, address.country, TaxedMoney(price, price)
    )
    plugin.apply_taxes_to_shipping(price, address, TaxedMoney(price, price))
    assert mocked_taxes.call_count == 1


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, taxes_in_prices",
    [
        (True, "20.34", "25.00", "0.0", True),
        (True, "20.00", "25.75", "5.0", False),
        (False, "40.00", "49.20", "0.0", False),
        (False, "29.52", "37.00", "3.0", True),
    ],
)
def test_calculate_checkout_total(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    taxes_in_prices,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount = voucher_amount
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    discounts = [discount_info] if with_discount else None
    lines = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_total(
        checkout_with_item, lines, address, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, taxes_in_prices",
    [
        (True, "25.00", "30.75", False),
        (False, "40.65", "50.00", True),
        (False, "50.00", "61.50", False),
        (True, "20.35", "25.00", True),
    ],
)
def test_calculate_checkout_subtotal(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
    discount_info,
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    stock,
):
    variant = stock.product_variant
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )

    product = variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    discounts = [discount_info] if with_discount else None
    add_variant_to_checkout(checkout_with_item, variant, 2)
    lines = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_subtotal(
        checkout_with_item, lines, address, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_order_shipping(vatlayer, order_line, shipping_zone, site_settings):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()
    price = manager.calculate_order_shipping(order)
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("8.13", "USD"), gross=Money("10.00", "USD"))


def test_calculate_order_shipping_for_order_without_shipping(
    vatlayer, order_line, shipping_zone, site_settings
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    order = order_line.order
    order.shipping_method = None
    order.save()
    price = manager.calculate_order_shipping(order)
    assert price == zero_taxed_money(order.currency)


def test_calculate_order_line_unit(vatlayer, order_line, shipping_zone, site_settings):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    order_line.unit_price = TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )
    order_line.save()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    product = order_line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    line_price = manager.calculate_order_line_unit(order_line)
    line_price = quantize_price(line_price, line_price.currency)
    assert line_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


def test_get_tax_rate_percentage_value(
    vatlayer, order_line, shipping_zone, site_settings, product
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    country = Country("PL")
    tax_rate = manager.get_tax_rate_percentage_value(product, country)
    assert tax_rate == Decimal("23")


def test_save_plugin_configuration(vatlayer, settings):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    manager.save_plugin_configuration(VatlayerPlugin.PLUGIN_ID, {"active": False})

    configuration = PluginConfiguration.objects.get(identifier=VatlayerPlugin.PLUGIN_ID)
    assert not configuration.active


def test_save_plugin_configuration_cannot_be_enabled_without_config(settings):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    with pytest.raises(ValidationError):
        manager.save_plugin_configuration(
            VatlayerPlugin.PLUGIN_ID,
            {"active": True},
        )


def test_show_taxes_on_storefront(vatlayer, settings):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    assert manager.show_taxes_on_storefront() is True


def test_get_tax_rate_type_choices(vatlayer, settings, monkeypatch):
    expected_choices = [
        "accommodation",
        "admission to cultural events",
        "admission to entertainment events",
    ]
    monkeypatch.setattr(
        "saleor.plugins.vatlayer.plugin.get_tax_rate_types",
        lambda: expected_choices,
    )
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    choices = manager.get_tax_rate_type_choices()

    # add a default choice
    expected_choices.append("standard")

    assert len(choices) == 4
    for choice in choices:
        assert choice.code in expected_choices


def test_apply_taxes_to_shipping_price_range(vatlayer, settings):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    money_range = MoneyRange(Money(100, "USD"), Money(200, "USD"))
    country = Country("PL")
    manager = get_plugins_manager()

    expected_start = TaxedMoney(net=Money("81.30", "USD"), gross=Money("100", "USD"))
    expected_stop = TaxedMoney(net=Money("162.60", "USD"), gross=Money("200", "USD"))

    price_range = manager.apply_taxes_to_shipping_price_range(money_range, country)

    assert price_range.start == expected_start
    assert price_range.stop == expected_stop


def test_apply_taxes_to_product(
    vatlayer, settings, variant, discount_info, channel_USD
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    country = Country("PL")
    manager = get_plugins_manager()
    variant.product.metadata = {
        "vatlayer.code": "standard",
        "vatlayer.description": "standard",
    }
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    price = manager.apply_taxes_to_product(
        variant.product,
        variant.get_price(
            variant.product, [], channel_USD, variant_channel_listing, [discount_info]
        ),
        country,
    )
    assert price == TaxedMoney(net=Money("4.07", "USD"), gross=Money("5.00", "USD"))


def test_apply_taxes_to_product_uses_taxes_from_product_type(
    vatlayer, settings, variant, discount_info, channel_USD
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    country = Country("PL")
    manager = get_plugins_manager()
    product = variant.product
    product.metadata = {}
    product.product_type.metadata = {
        "vatlayer.code": "standard",
        "vatlayer.description": "standard",
    }
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    price = manager.apply_taxes_to_product(
        product,
        variant.get_price(
            product, [], channel_USD, variant_channel_listing, [discount_info]
        ),
        country,
    )
    assert price == TaxedMoney(net=Money("4.07", "USD"), gross=Money("5.00", "USD"))


def test_calculations_checkout_total_with_vatlayer(
    vatlayer, settings, checkout_with_item
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_subtotal = calculations.checkout_total(
        manager=manager,
        checkout=checkout_with_item,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert checkout_subtotal == TaxedMoney(
        net=Money("30", "USD"), gross=Money("30", "USD")
    )


def test_calculations_checkout_subtotal_with_vatlayer(
    vatlayer, settings, checkout_with_item
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout=checkout_with_item,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert checkout_subtotal == TaxedMoney(
        net=Money("30", "USD"), gross=Money("30", "USD")
    )


def test_calculations_checkout_shipping_price_with_vatlayer(
    vatlayer, settings, checkout_with_item
):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_item)
    checkout_shipping_price = calculations.checkout_shipping_price(
        manager=manager,
        checkout=checkout_with_item,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    assert checkout_shipping_price == TaxedMoney(
        net=Money("0", "USD"), gross=Money("0", "USD")
    )


def test_skip_diabled_plugin(settings):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_plugins_manager()
    plugin: VatlayerPlugin = manager.get_plugin(VatlayerPlugin.PLUGIN_ID)

    assert (
        plugin._skip_plugin(
            previous_value=TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))
        )
        is True
    )


def test_get_checkout_line_tax_rate(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.230")


def test_get_checkout_line_tax_rate_order_not_valid(
    site_settings,
    vatlayer,
    checkout_with_item,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    tax_rate = manager.get_checkout_line_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.25")


def test_get_order_line_tax_rate(
    site_settings,
    vatlayer,
    order_line,
    address,
    shipping_zone,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)
    product.save()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_line_tax_rate(order, product, address, unit_price)
    assert tax_rate == Decimal("0.230")


def test_get_order_line_tax_rate_order_no_address_given(
    site_settings,
    order_line,
    vatlayer,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_line_tax_rate(order, product, None, unit_price)
    assert tax_rate == Decimal("0.25")


def test_get_checkout_shipping_tax_rate(
    site_settings,
    vatlayer,
    checkout_with_item,
    address,
    shipping_zone,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_with_item,
        [checkout_line_info],
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.230")


def test_get_checkout_shipping_tax_rate_no_address(
    site_settings,
    vatlayer,
    checkout_with_item,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.25")


def test_get_checkout_shipping_tax_rate_skip_plugin(
    site_settings, vatlayer, checkout_with_item, monkeypatch, address, shipping_zone
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    monkeypatch.setattr(
        "saleor.plugins.vatlayer.plugin.VatlayerPlugin._skip_plugin",
        lambda *_: True,
    )

    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    unit_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    variant = line.variant
    checkout_line_info = CheckoutLineInfo(
        line=line,
        variant=variant,
        channel_listing=variant.channel_listings.first(),
        product=variant.product,
        collections=[],
    )

    tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_with_item,
        checkout_line_info,
        checkout_with_item.shipping_address,
        [],
        unit_price,
    )
    assert tax_rate == Decimal("0.25")


def test_get_order_shipping_tax_rate(
    site_settings,
    vatlayer,
    order_line,
    address,
    shipping_zone,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)
    product.save()

    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
    assert tax_rate == Decimal("0.230")


def test_get_order_shipping_tax_rate_no_address_given(
    site_settings,
    order_line,
    vatlayer,
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    order.shipping_address = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "billing_address"])

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
    assert tax_rate == Decimal("0.25")


def test_get_order_shipping_tax_rate_skip_plugin(
    site_settings, order_line, vatlayer, monkeypatch
):
    manager = get_plugins_manager(
        plugins=["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    monkeypatch.setattr(
        "saleor.plugins.vatlayer.plugin.VatlayerPlugin._skip_plugin",
        lambda *_: True,
    )
    order = order_line.order
    product = Product.objects.get(name=order_line.product_name)

    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = True
    site_settings.save()

    shipping_price = TaxedMoney(Money(12, "USD"), Money(15, "USD"))

    tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
    assert tax_rate == Decimal("0.25")
