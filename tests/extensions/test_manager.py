import pytest
from django_countries.fields import Country
from prices import Money, TaxedMoney

from saleor.core.extensions.manager import ExtensionsManager, get_extensions_manager
from saleor.core.extensions.plugin import BasePlugin
from saleor.core.taxes import TaxType


class TestPlugin(BasePlugin):
    """"""

    def calculate_checkout_total(self, checkout, discounts, previous_value):
        total = Money("1.0", currency=checkout.get_total().currency)
        return TaxedMoney(total, total)

    def calculate_checkout_subtotal(self, checkout, discounts, previous_value):
        subtotal = Money("1.0", currency=checkout.get_total().currency)
        return TaxedMoney(subtotal, subtotal)

    def calculate_checkout_shipping(self, checkout, discounts, previous_value):
        price = Money("1.0", currency=checkout.get_total().currency)
        return TaxedMoney(price, price)

    def calculate_order_shipping(self, order, previous_value):
        price = Money("1.0", currency=order.total.currency)
        return TaxedMoney(price, price)

    def calculate_checkout_line_total(self, checkout_line, discounts, previous_value):
        price = Money("1.0", currency=checkout_line.get_total().currency)
        return TaxedMoney(price, price)

    def calculate_order_line_unit(self, order_line, previous_value):
        currency = order_line.unit_price.currency
        price = Money("1.0", currency)
        return TaxedMoney(price, price)

    def get_tax_rate_type_choices(self, previous_value):
        return [TaxType(code="123", description="abc")]

    def show_taxes_on_storefront(self, previous_value: bool) -> bool:
        return True

    def taxes_are_enabled(self, previous_value: bool) -> bool:
        return True

    def apply_taxes_to_product(self, product, price, country, previous_value, **kwargs):
        price = Money("1.0", price.currency)
        return TaxedMoney(price, price)

    def apply_taxes_to_shipping(
        self, price, shipping_address, previous_value
    ) -> TaxedMoney:
        price = Money("1.0", price.currency)
        return TaxedMoney(price, price)


def test_get_extensions_manager():
    manager_path = "saleor.core.extensions.manager.ExtensionsManager"
    plugin_path = "tests.extensions.test_manager.TestPlugin"
    manager = get_extensions_manager(manager_path=manager_path, plugins=[plugin_path])
    assert isinstance(manager, ExtensionsManager)
    assert len(manager.plugins) == 1


@pytest.mark.parametrize(
    "plugins, total_amount",
    [(["tests.extensions.test_manager.TestPlugin"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_total(
    checkout_with_item, discount_info, plugins, total_amount
):
    currency = checkout_with_item.get_total().currency
    expected_total = Money(total_amount, currency)
    manager = ExtensionsManager(plugins=plugins)
    taxed_total = manager.calculate_checkout_total(checkout_with_item, [discount_info])
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    "plugins, subtotal_amount",
    [(["tests.extensions.test_manager.TestPlugin"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_subtotal(
    checkout_with_item, discount_info, plugins, subtotal_amount
):
    currency = checkout_with_item.get_total().currency
    expected_subtotal = Money(subtotal_amount, currency)
    taxed_subtotal = ExtensionsManager(plugins=plugins).calculate_checkout_subtotal(
        checkout_with_item, [discount_info]
    )
    assert TaxedMoney(expected_subtotal, expected_subtotal) == taxed_subtotal


@pytest.mark.parametrize(
    "plugins, shipping_amount",
    [(["tests.extensions.test_manager.TestPlugin"], "1.0"), ([], "0.0")],
)
def test_manager_calculates_checkout_shipping(
    checkout_with_item, discount_info, plugins, shipping_amount
):
    currency = checkout_with_item.get_total().currency
    expected_shipping_price = Money(shipping_amount, currency)
    taxed_shipping_price = ExtensionsManager(
        plugins=plugins
    ).calculate_checkout_shipping(checkout_with_item, [discount_info])
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    "plugins, shipping_amount",
    [(["tests.extensions.test_manager.TestPlugin"], "1.0"), ([], "10.0")],
)
def test_manager_calculates_order_shipping(order_with_lines, plugins, shipping_amount):
    currency = order_with_lines.total.currency
    expected_shipping_price = Money(shipping_amount, currency)

    taxed_shipping_price = ExtensionsManager(plugins=plugins).calculate_order_shipping(
        order_with_lines
    )
    assert (
        TaxedMoney(expected_shipping_price, expected_shipping_price)
        == taxed_shipping_price
    )


@pytest.mark.parametrize(
    "plugins, amount",
    [(["tests.extensions.test_manager.TestPlugin"], "1.0"), ([], "15.0")],
)
def test_manager_calculates_checkout_line_total(
    checkout_with_item, discount_info, plugins, amount
):
    line = checkout_with_item.lines.all()[0]
    currency = line.get_total().currency
    expected_total = Money(amount, currency)
    taxed_total = ExtensionsManager(plugins=plugins).calculate_checkout_line_total(
        line, [discount_info]
    )
    assert TaxedMoney(expected_total, expected_total) == taxed_total


@pytest.mark.parametrize(
    "plugins, amount",
    [(["tests.extensions.test_manager.TestPlugin"], "1.0"), ([], "12.30")],
)
def test_manager_calculates_order_line(order_line, plugins, amount):
    currency = order_line.unit_price.currency
    expected_price = Money(amount, currency)
    unit_price = ExtensionsManager(plugins=plugins).calculate_order_line_unit(
        order_line
    )
    assert expected_price == unit_price.gross


@pytest.mark.parametrize(
    "plugins, tax_rate_list",
    [
        (
            ["tests.extensions.test_manager.TestPlugin"],
            [TaxType(code="123", description="abc")],
        ),
        ([], []),
    ],
)
def test_manager_uses_get_tax_rate_choices(plugins, tax_rate_list):
    assert (
        tax_rate_list == ExtensionsManager(plugins=plugins).get_tax_rate_type_choices()
    )


@pytest.mark.parametrize(
    "plugins, show_taxes",
    [(["tests.extensions.test_manager.TestPlugin"], True), ([], False)],
)
def test_manager_show_taxes_on_storefront(plugins, show_taxes):
    assert show_taxes == ExtensionsManager(plugins=plugins).show_taxes_on_storefront()


@pytest.mark.parametrize(
    "plugins, taxes_enabled",
    [(["tests.extensions.test_manager.TestPlugin"], True), ([], False)],
)
def test_manager_taxes_are_enabled(plugins, taxes_enabled):
    assert taxes_enabled == ExtensionsManager(plugins=plugins).taxes_are_enabled()


@pytest.mark.parametrize(
    "plugins, price",
    [(["tests.extensions.test_manager.TestPlugin"], "1.0"), ([], "10.0")],
)
def test_manager_apply_taxes_to_product(product, plugins, price):
    country = Country("PL")
    variant = product.variants.all()[0]
    currency = variant.get_price().currency
    expected_price = Money(price, currency)
    taxed_price = ExtensionsManager(plugins=plugins).apply_taxes_to_product(
        product, variant.get_price(), country
    )
    assert TaxedMoney(expected_price, expected_price) == taxed_price


@pytest.mark.parametrize(
    "plugins, price_amount",
    [(["tests.extensions.test_manager.TestPlugin"], "1.0"), ([], "10.0")],
)
def test_manager_apply_taxes_to_shipping(
    shipping_method, address, plugins, price_amount
):
    expected_price = Money(price_amount, "USD")
    taxed_price = ExtensionsManager(plugins=plugins).apply_taxes_to_shipping(
        shipping_method.price, address
    )
    assert TaxedMoney(expected_price, expected_price) == taxed_price
