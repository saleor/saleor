import pytest
from prices import Money, TaxedMoney

from saleor.checkout.utils import add_variant_to_checkout
from saleor.core.taxes import TaxError, quantize_price
from saleor.extensions.manager import get_extensions_manager
from saleor.extensions.plugins.avatax import (
    checkout_needs_new_fetch,
    generate_request_data_from_checkout,
    get_cached_tax_codes_or_fetch,
)


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, taxes_in_prices",
    [
        (True, "12.20", "15.00", True),
        (False, "24.39", "30.00", True),
        (True, "15.00", "18.45", False),
        (False, "30.00", "36.90", False),
    ],
)
def test_calculate_checkout_line_total(
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    discount_info,
    checkout_with_item,
    address,
    address_usa,
    site_settings,
    monkeypatch,
    shipping_zone,
    settings,
):
    settings.AVATAX_USERNAME_OR_ACCOUNT = "test"
    settings.AVATAX_PASSWORD_OR_LICENSE = "test"
    settings.PLUGINS = ["saleor.extensions.plugins.avatax.plugin.AvataxPlugin"]
    monkeypatch.setattr(
        "saleor.extensions.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda: {"PC040156": "desc"},
    )
    manager = get_extensions_manager(plugins=settings.PLUGINS)

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "PC040156")
    product.save()
    discounts = [discount_info] if with_discount else None
    total = manager.calculate_checkout_line_total(line, discounts)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, voucher_amount, taxes_in_prices",
    [
        (True, "20.33", "25.00", "0.0", True),
        (True, "20.00", "25.75", "5.0", False),
        (False, "40.00", "49.20", "0.0", False),
        (False, "29.52", "37.00", "3.0", True),
    ],
)
def test_calculate_checkout_total(
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    taxes_in_prices,
    checkout_with_item,
    discount_info,
    shipping_zone,
    address,
    address_usa,
    site_settings,
    monkeypatch,
    settings,
):
    settings.AVATAX_USERNAME_OR_ACCOUNT = "test"
    settings.AVATAX_PASSWORD_OR_LICENSE = "test"
    settings.PLUGINS = ["saleor.extensions.plugins.avatax.plugin.AvataxPlugin"]
    monkeypatch.setattr(
        "saleor.extensions.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda: {"PC040156": "desc"},
    )
    manager = get_extensions_manager(plugins=settings.PLUGINS)
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices

    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount_amount = voucher_amount
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "PC040156")
    product.save()

    discounts = [discount_info] if with_discount else None
    total = manager.calculate_checkout_total(checkout_with_item, discounts)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
def test_calculate_checkout_shipping(
    checkout_with_item,
    shipping_zone,
    discount_info,
    address,
    address_usa,
    site_settings,
    monkeypatch,
    settings,
):
    settings.AVATAX_USERNAME_OR_ACCOUNT = "test"
    settings.AVATAX_PASSWORD_OR_LICENSE = "test"
    settings.PLUGINS = ["saleor.extensions.plugins.avatax.plugin.AvataxPlugin"]
    monkeypatch.setattr(
        "saleor.extensions.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda: {"PC040156": "desc"},
    )
    manager = get_extensions_manager(plugins=settings.PLUGINS)
    site_settings.company_address = address_usa
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    shipping_price = manager.calculate_checkout_shipping(
        checkout_with_item, [discount_info]
    )
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, taxes_in_prices",
    [
        (True, "25.00", "30.75", False),
        (False, "40.65", "50.00", True),
        (False, "50.00", "61.50", False),
        (True, "20.33", "25.00", True),
    ],
)
def test_calculate_checkout_subtotal(
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    discount_info,
    checkout_with_item,
    variant,
    monkeypatch,
    site_settings,
    address_usa,
    shipping_zone,
    address,
    settings,
):
    settings.AVATAX_USERNAME_OR_ACCOUNT = "test"
    settings.AVATAX_PASSWORD_OR_LICENSE = "test"
    settings.PLUGINS = ["saleor.extensions.plugins.avatax.plugin.AvataxPlugin"]
    monkeypatch.setattr(
        "saleor.extensions.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda: {"PC040156": "desc"},
    )
    manager = get_extensions_manager(plugins=settings.PLUGINS)
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    discounts = [discount_info] if with_discount else None
    add_variant_to_checkout(checkout_with_item, variant, 2)
    total = manager.calculate_checkout_subtotal(checkout_with_item, discounts)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
def test_calculate_order_shipping(
    order_line, shipping_zone, site_settings, address_usa, settings
):
    settings.AVATAX_USERNAME_OR_ACCOUNT = "test"
    settings.AVATAX_PASSWORD_OR_LICENSE = "test"
    settings.PLUGINS = ["saleor.extensions.plugins.avatax.plugin.AvataxPlugin"]
    manager = get_extensions_manager(plugins=settings.PLUGINS)
    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = order.billing_address.get_copy()
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    site_settings.company_address = address_usa
    site_settings.save()

    price = manager.calculate_order_shipping(order)
    price = quantize_price(price, price.currency)
    assert price == TaxedMoney(net=Money("8.13", "USD"), gross=Money("10.00", "USD"))


@pytest.mark.vcr
def test_calculate_order_line_unit(
    order_line, shipping_zone, site_settings, address_usa, settings
):
    settings.AVATAX_USERNAME_OR_ACCOUNT = "test"
    settings.AVATAX_PASSWORD_OR_LICENSE = "test"
    settings.PLUGINS = ["saleor.extensions.plugins.avatax.plugin.AvataxPlugin"]

    manager = get_extensions_manager(plugins=settings.PLUGINS)
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

    site_settings.company_address = address_usa
    site_settings.save()

    line_price = manager.calculate_order_line_unit(order_line)
    line_price = quantize_price(line_price, line_price.currency)
    assert line_price == TaxedMoney(
        net=Money("8.13", "USD"), gross=Money("10.00", "USD")
    )


@pytest.mark.vcr
def test_preprocess_order_creation(
    checkout_with_item,
    settings,
    monkeypatch,
    address,
    address_usa,
    site_settings,
    shipping_zone,
    discount_info,
):

    settings.AVATAX_USERNAME_OR_ACCOUNT = "test"
    settings.AVATAX_PASSWORD_OR_LICENSE = "test"
    settings.PLUGINS = ["saleor.extensions.plugins.avatax.plugin.AvataxPlugin"]
    monkeypatch.setattr(
        "saleor.extensions.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda: {"PC040156": "desc"},
    )
    manager = get_extensions_manager(plugins=settings.PLUGINS)
    site_settings.company_address = address_usa
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    manager.preprocess_order_creation(checkout_with_item, discounts)


@pytest.mark.vcr
def test_preprocess_order_creation_wrong_data(
    checkout_with_item,
    settings,
    monkeypatch,
    address,
    address_usa,
    site_settings,
    shipping_zone,
    discount_info,
):
    settings.AVATAX_USERNAME_OR_ACCOUNT = "wrong"
    settings.AVATAX_PASSWORD_OR_LICENSE = "wrong"
    settings.PLUGINS = ["saleor.extensions.plugins.avatax.plugin.AvataxPlugin"]
    monkeypatch.setattr(
        "saleor.extensions.plugins.avatax.plugin.get_cached_tax_codes_or_fetch",
        lambda: {"PC040156": "desc"},
    )
    manager = get_extensions_manager(plugins=settings.PLUGINS)

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    with pytest.raises(TaxError):
        manager.preprocess_order_creation(checkout_with_item, discounts)


@pytest.mark.vcr
def test_get_cached_tax_codes_or_fetch(monkeypatch, settings):
    monkeypatch.setattr("saleor.extensions.plugins.avatax.cache.get", lambda x, y: {})
    settings.AVATAX_USERNAME_OR_ACCOUNT = "test"
    settings.AVATAX_PASSWORD_OR_LICENSE = "test"
    tax_codes = get_cached_tax_codes_or_fetch()
    assert len(tax_codes) > 0


@pytest.mark.vcr
def test_get_cached_tax_codes_or_fetch_wrong_response(monkeypatch, settings):
    monkeypatch.setattr("saleor.extensions.plugins.avatax.cache.get", lambda x, y: {})
    settings.AVATAX_USERNAME_OR_ACCOUNT = "wrong_data"
    settings.AVATAX_PASSWORD_OR_LICENSE = "wrong_data"
    tax_codes = get_cached_tax_codes_or_fetch()
    assert len(tax_codes) == 0


def test_checkout_needs_new_fetch(monkeypatch, settings, checkout_with_item, address):
    monkeypatch.setattr("saleor.extensions.plugins.avatax.cache.get", lambda x: None)
    checkout_with_item.shipping_address = address
    checkout_data = generate_request_data_from_checkout(checkout_with_item)
    assert checkout_needs_new_fetch(checkout_data, str(checkout_with_item.token))
