from decimal import Decimal
from unittest import mock
from unittest.mock import Mock
from urllib.parse import urlparse

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django_countries.fields import Country
from django_prices_vatlayer.models import VAT
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from saleor.checkout.utils import add_variant_to_checkout
from saleor.core.taxes import quantize_price
from saleor.dashboard.taxes.filters import get_country_choices_for_vat
from saleor.extensions.manager import get_extensions_manager
from saleor.extensions.plugins.vatlayer import (
    DEFAULT_TAX_RATE_NAME,
    apply_tax_to_price,
    get_tax_rate_by_name,
    get_taxed_shipping_price,
    get_taxes_for_country,
)
from saleor.extensions.plugins.vatlayer.plugin import VatlayerPlugin


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


def test_view_checkout_with_taxes(
    settings, client, request_checkout_with_item, vatlayer, address
):
    settings.DEFAULT_COUNTRY = "PL"
    checkout = request_checkout_with_item
    checkout.shipping_address = address
    checkout.save()
    product = checkout.lines.first().variant.product
    product.meta = {"taxes": {"vatlayer": {"code": "standard", "description": ""}}}
    product.save()
    response = client.get(reverse("checkout:index"))
    response_checkout_line = response.context[0]["checkout_lines"][0]
    line_net = Money(amount="8.13", currency="USD")
    line_gross = Money(amount="10.00", currency="USD")

    assert response_checkout_line["get_total"].tax.amount
    assert response_checkout_line["get_total"] == TaxedMoney(line_net, line_gross)
    assert response.status_code == 200


def test_view_update_checkout_quantity_with_taxes(
    client, request_checkout_with_item, vatlayer, monkeypatch
):
    monkeypatch.setattr(
        "saleor.checkout.views.to_local_currency", lambda price, currency: price
    )
    variant = request_checkout_with_item.lines.get().variant
    response = client.post(
        reverse("checkout:update-line", kwargs={"variant_id": variant.id}),
        {"quantity": 3},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert request_checkout_with_item.quantity == 3


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


def test_view_taxes_list(admin_client, vatlayer):
    url = reverse("dashboard:taxes")

    response = admin_client.get(url)

    tax_list = response.context["taxes"].object_list
    assert response.status_code == 200
    assert tax_list == list(VAT.objects.order_by("country_code"))


def test_view_tax_details(admin_client, vatlayer):
    tax = VAT.objects.get(country_code="PL")
    tax_rates = [(rate_name, tax["value"]) for rate_name, tax in vatlayer.items()]
    tax_rates = sorted(tax_rates)
    url = reverse("dashboard:tax-details", kwargs={"country_code": "PL"})

    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.context["tax"] == tax
    assert response.context["tax_rates"] == tax_rates


def test_configure_taxes(admin_client, site_settings):
    url = reverse("dashboard:configure-taxes")
    data = {
        "include_taxes_in_prices": False,
        "display_gross_prices": False,
        "charge_taxes_on_shipping": False,
    }

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse("dashboard:taxes")

    site_settings.refresh_from_db()
    assert not site_settings.include_taxes_in_prices
    assert not site_settings.display_gross_prices
    assert not site_settings.charge_taxes_on_shipping


@mock.patch("saleor.dashboard.taxes.views.messages", create=True)
@mock.patch("saleor.dashboard.taxes.views.call_command", create=True)
def test_fetch_tax_rates(mocked_call_command, mocked_messages, admin_client):
    # Ensure a valid fetch VAT rates request is correctly handled,
    # and is leading to the proper VAT fetching command being invoked.
    url = reverse("dashboard:fetch-tax-rates")
    response = admin_client.post(url)

    # Ensure the request was successful
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse("dashboard:taxes")
    assert mocked_messages.success.call_count == 1

    # Ensure the get VAT rates (mocked) command was invoked
    mocked_call_command.assert_called_once_with("get_vat_rates")


@mock.patch("saleor.dashboard.taxes.views.messages", create=True)
@mock.patch("saleor.dashboard.taxes.views.logger", create=True)
@mock.patch(
    "saleor.dashboard.taxes.views.call_command",
    side_effect=ImproperlyConfigured("Test"),
    create=True,
)
def test_fetch_tax_rates_improperly_configured(
    mocked_call_command, mocked_logger, mocked_messages, admin_client
):
    # Ensure a failing VAT rate fetching is leading to an error being
    # returned, and that error is handled.
    url = reverse("dashboard:fetch-tax-rates")
    response = admin_client.post(url)

    # Ensure the request was successful
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse("dashboard:taxes")

    # Ensure error was logged to the logger
    # and the error was returned to the client
    assert mocked_logger.exception.call_count == 1
    assert mocked_messages.warning.call_count == 1

    # Ensure the get VAT rates (mocked) command was invoked
    mocked_call_command.assert_called_once_with("get_vat_rates")


def test_fetch_tax_rates_invalid_method(admin_client):
    # Ensure the GET method is not allowed for tax rates fetching
    url = reverse("dashboard:fetch-tax-rates")
    assert admin_client.get(url).status_code == 405


def test_tax_list_filters_empty(admin_client, vatlayer):
    qs = VAT.objects.order_by("country_code")
    url = reverse("dashboard:taxes")
    data = {"country_code": [""], "sort_by": [""]}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context["filter_set"].qs) == list(qs)


def test_tax_list_filters_country_code(admin_client, vatlayer):
    qs = VAT.objects.filter(country_code="PL")
    url = reverse("dashboard:taxes")
    data = {"country_code": ["PL"], "sort_by": [""]}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context["filter_set"].qs) == list(qs)


def test_tax_list_filters_sort_by(admin_client, vatlayer):
    qs = VAT.objects.order_by("-country_code")
    url = reverse("dashboard:taxes")
    data = {"country_code": [""], "sort_by": ["-country_code"]}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context["filter_set"].qs) == list(qs)


def test_get_country_choices_for_vat(vatlayer):
    expected_choices = [("DE", "Germany"), ("PL", "Poland")]
    choices = get_country_choices_for_vat()
    assert choices == expected_choices


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


def test_vatlayer_plugin_caches_taxes(vatlayer, monkeypatch, product, address):

    mocked_taxes = Mock(wraps=get_taxes_for_country)
    monkeypatch.setattr(
        "saleor.extensions.plugins.vatlayer.plugin.get_taxes_for_country", mocked_taxes
    )
    plugin = VatlayerPlugin()
    price = product.variants.first().get_price()
    price = TaxedMoney(price, price)
    address.country = Country("de")
    plugin.apply_taxes_to_product(product, price, address.country, price)
    plugin.apply_taxes_to_shipping(price, address, price)
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
    manager = get_extensions_manager(
        plugins=["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    checkout_with_item.shipping_address = address
    checkout_with_item.save()
    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.discount_amount = voucher_amount
    checkout_with_item.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    discounts = [discount_info] if with_discount else None
    total = manager.calculate_checkout_total(checkout_with_item, discounts)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
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
    variant,
):
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()

    manager = get_extensions_manager(
        plugins=["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    )

    product = variant.product
    manager.assign_tax_code_to_object_meta(product, "standard")
    product.save()

    discounts = [discount_info] if with_discount else None
    add_variant_to_checkout(checkout_with_item, variant, 2)
    total = manager.calculate_checkout_subtotal(checkout_with_item, discounts)
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


def test_calculate_order_shipping(vatlayer, order_line, shipping_zone, site_settings):
    manager = get_extensions_manager(
        plugins=["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
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


def test_calculate_order_line_unit(vatlayer, order_line, shipping_zone, site_settings):
    manager = get_extensions_manager(
        plugins=["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
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
    manager = get_extensions_manager(
        plugins=["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    )
    country = Country("PL")
    tax_rate = manager.get_tax_rate_percentage_value(product, country)
    assert tax_rate == Decimal("23")


def test_get_plugin_configuration(vatlayer, settings):
    settings.PLUGINS = ["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_extensions_manager()
    configurations = manager.get_plugin_configurations()
    assert len(configurations) == 1
    configuration = configurations[0]

    assert configuration.name == "Vatlayer"
    assert configuration.active
    assert not configuration.configuration


def test_save_plugin_configuration(vatlayer, settings):
    settings.PLUGINS = ["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_extensions_manager()
    configuration = manager.get_plugin_configuration("Vatlayer")
    manager.save_plugin_configuration("Vatlayer", {"active": False})

    configuration.refresh_from_db()
    assert not configuration.active


def test_show_taxes_on_storefront(vatlayer, settings):
    settings.PLUGINS = ["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_extensions_manager()
    assert manager.show_taxes_on_storefront() is True


def test_get_tax_rate_type_choices(vatlayer, settings, monkeypatch):
    expected_choices = [
        "accommodation",
        "admission to cultural events",
        "admission to entertainment events",
    ]
    monkeypatch.setattr(
        "saleor.extensions.plugins.vatlayer.plugin.get_tax_rate_types",
        lambda: expected_choices,
    )
    settings.PLUGINS = ["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = get_extensions_manager()
    choices = manager.get_tax_rate_type_choices()

    # add a default choice
    expected_choices.append("standard")

    assert len(choices) == 4
    for choice in choices:
        assert choice.code in expected_choices


def test_apply_taxes_to_shipping_price_range(vatlayer, settings):
    settings.PLUGINS = ["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    money_range = MoneyRange(Money(100, "USD"), Money(200, "USD"))
    country = Country("PL")
    manager = get_extensions_manager()

    expected_start = TaxedMoney(net=Money("81.30", "USD"), gross=Money("100", "USD"))
    expected_stop = TaxedMoney(net=Money("162.60", "USD"), gross=Money("200", "USD"))

    price_range = manager.apply_taxes_to_shipping_price_range(money_range, country)

    assert price_range.start == expected_start
    assert price_range.stop == expected_stop


def test_apply_taxes_to_product(vatlayer, settings, variant, discount_info):
    settings.PLUGINS = ["saleor.extensions.plugins.vatlayer.plugin.VatlayerPlugin"]
    country = Country("PL")
    manager = get_extensions_manager()
    variant.product.meta = {
        "taxes": {"vatlayer": {"code": "standard", "description": "standard"}}
    }
    price = manager.apply_taxes_to_product(
        variant.product, variant.get_price([discount_info]), country
    )
    assert price == TaxedMoney(net=Money("4.07", "USD"), gross=Money("5.00", "USD"))
