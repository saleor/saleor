import json
import uuid
from dataclasses import asdict
from decimal import Decimal
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from prices import Money, TaxedMoney
from requests import RequestException

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import add_variant_to_checkout
from ....core.prices import quantize_price
from ....core.taxes import TaxError
from ....plugins.manager import get_plugins_manager
from ....plugins.models import PluginConfiguration
from ..plugin import AvataxExcisePlugin
from ..utils import (
    AvataxConfiguration,
    api_post_request,
    get_metadata_key,
    get_order_request_data,
)


@patch("saleor.plugins.avatax_excise.plugin.api_get_request")
def test_save_plugin_configuration(api_get_request_mock, settings, channel_USD):
    settings.PLUGINS = ["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"]
    api_get_request_mock.return_value = {"authenticated": True}
    manager = get_plugins_manager()
    manager.save_plugin_configuration(
        AvataxExcisePlugin.PLUGIN_ID,
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
        AvataxExcisePlugin.PLUGIN_ID, channel_USD, {"active": True}
    )
    plugin_configuration = PluginConfiguration.objects.get(
        identifier=AvataxExcisePlugin.PLUGIN_ID
    )
    assert plugin_configuration.active


def test_save_plugin_configuration_invalid(settings, channel_USD):
    settings.PLUGINS = ["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"]
    manager = get_plugins_manager()
    with pytest.raises(ValidationError):
        manager.save_plugin_configuration(
            AvataxExcisePlugin.PLUGIN_ID,
            channel_USD.slug,
            {
                "active": True,
                "configuration": [
                    {"name": "Username or account", "value": ""},
                    {"name": "Password or license", "value": ""},
                ],
            },
        )
    plugin_configuration = PluginConfiguration.objects.get(
        identifier=AvataxExcisePlugin.PLUGIN_ID
    )
    assert not plugin_configuration.active


@patch("saleor.plugins.avatax_excise.plugin.api_get_request")
def test_save_plugin_configuration_authentication_failed(
    api_get_request_mock, settings, channel_USD
):
    settings.PLUGINS = ["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"]
    api_get_request_mock.return_value = {"authenticated": False}
    manager = get_plugins_manager()

    with pytest.raises(ValidationError) as e:
        manager.save_plugin_configuration(
            AvataxExcisePlugin.PLUGIN_ID,
            channel_USD.slug,
            {
                "active": True,
                "configuration": [
                    {"name": "Username or account", "value": "test"},
                    {"name": "Password or license", "value": "test"},
                ],
            },
        )
    msg = "Authentication failed. Please check provided data."
    assert e._excinfo[1].args[0] == msg
    plugin_configuration = PluginConfiguration.objects.get(
        identifier=AvataxExcisePlugin.PLUGIN_ID
    )
    assert not plugin_configuration.active


@pytest.mark.vcr
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, taxes_in_prices",
    [
        (False, "30.00", "31.80", False),
        (True, "15.00", "16.80", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_checkout_line_total(
    reset_sequences,  # pylint: disable=unused-argument
    with_discount,
    expected_net,
    expected_gross,
    taxes_in_prices,
    discount_info,
    checkout_with_item,
    address_usa_va,
    address_usa,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address_usa_va
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()
    line = checkout_with_item.lines.first()
    product = line.variant.product
    product.metadata = {}  # TODO consider adding ATE fields here
    product.charge_taxes = True
    product.save()
    product.product_type.save()

    discounts = [discount_info] if with_discount else None

    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)

    total = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        lines[0],
        checkout_with_item.shipping_address,
        discounts,
    )
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )

    checkout_with_item.refresh_from_db()
    taxes_metadata = checkout_with_item.metadata.get(get_metadata_key("itemized_taxes"))

    sales_tax = checkout_with_item.metadata.get(get_metadata_key("sales_tax"))
    other_tax = checkout_with_item.metadata.get(get_metadata_key("other_tax"))

    assert taxes_metadata is not None
    assert len(taxes_metadata) > 0
    assert sales_tax >= 0
    assert other_tax >= 0


@pytest.mark.vcr
@pytest.mark.parametrize(
    "with_discount, expected_net, expected_gross, " "voucher_amount, taxes_in_prices",
    [
        (False, "43.98", "45.90", "0.0", False),
        (False, "39.98", "41.65", "4.0", False),
        (True, "28.98", "30.01", "0.0", False),
        (True, "24.98", "25.76", "4.0", False),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_checkout_total(
    reset_sequences,  # pylint: disable=unused-argument
    with_discount,
    expected_net,
    expected_gross,
    voucher_amount,
    taxes_in_prices,
    checkout_with_item,
    product_with_single_variant,
    discount_info,
    shipping_zone,
    address_usa_va,
    address_usa,
    site_settings,
    voucher,
    monkeypatch,
    plugin_configuration,
    non_default_category,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin._skip_plugin",
        lambda *_: False,
    )
    manager = get_plugins_manager()
    checkout_with_item.shipping_address = address_usa_va
    checkout_with_item.save()

    checkout_variant = checkout_with_item.lines.first().variant
    checkout_variant.sku = "202015500"
    checkout_variant.save(update_fields=["sku"])

    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    voucher_amount = Money(voucher_amount, "USD")
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.voucher_code = voucher.code
    checkout_with_item.discount = voucher_amount
    checkout_with_item.save()

    product_with_single_variant.charge_taxes = False
    product_with_single_variant.category = non_default_category
    product_with_single_variant.save()

    variant = product_with_single_variant.variants.first()
    variant.sku = "202165300"
    variant.save(update_fields=["sku"])

    discounts = [discount_info] if with_discount else None
    checkout_info = fetch_checkout_info(checkout_with_item, [], discounts, manager)

    add_variant_to_checkout(checkout_info, product_with_single_variant.variants.get())

    lines, _ = fetch_checkout_lines(checkout_with_item)
    total = manager.calculate_checkout_total(
        checkout_info, lines, address_usa_va, discounts
    )
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_checkout_shipping(
    reset_sequences,  # pylint: disable=unused-argument
    checkout_with_item,
    shipping_zone,
    discount_info,
    address_usa_va,
    address,
    site_settings,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager()
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = address_usa_va
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(
        checkout_with_item, lines, [discount_info], manager
    )
    shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, [discount_info]
    )
    shipping_price = quantize_price(shipping_price, shipping_price.currency)
    assert shipping_price == TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )

    checkout_with_item.refresh_from_db()
    taxes_metadata = checkout_with_item.metadata.get(get_metadata_key("itemized_taxes"))

    sales_tax = checkout_with_item.metadata.get(get_metadata_key("sales_tax"))
    other_tax = checkout_with_item.metadata.get(get_metadata_key("other_tax"))

    assert taxes_metadata is not None
    assert len(taxes_metadata) > 0
    assert sales_tax >= 0
    assert other_tax >= 0


@patch("saleor.plugins.avatax.plugin.AvataxPlugin._skip_plugin")
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_checkout_total_skip(
    skip_mock, checkout_with_item, address_usa, plugin_configuration
):
    skip_mock.return_value = True
    plugin_configuration()
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout_with_item, [], [], manager)
    manager.calculate_checkout_total(checkout_info, [], [], [])
    skip_mock.assert_called_once


@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_checkout_total_invalid_checkout(
    checkout_with_item, address_usa, plugin_configuration
):
    plugin_configuration()
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout_with_item, [], [], manager)
    total = manager.calculate_checkout_total(checkout_info, [], [], [])
    assert total == TaxedMoney(net=Money("0.00", "USD"), gross=Money("0.00", "USD"))


@pytest.mark.vcr
@pytest.mark.parametrize(
    "expected_net, expected_gross, taxes_in_prices, "
    "variant_sku, price, destination, metadata",
    [
        (
            "20",
            "38.76",
            False,
            "202000000",
            172,
            {"city": "Richmond", "postal_code": "23226", "country_area": "VA"},
            {
                "UnitQuantity": 25,
                "CustomNumeric1": 81.46,
                "CustomNumeric2": 85.65,
                "CustomNumeric3": 95.72,
            },
        ),
        (
            "20.00",
            "24.95",
            False,
            "202015500",
            170,
            {"city": "Tempe", "postal_code": "85281", "country_area": "AZ"},
            {
                "UnitQuantity": 18,
                "CustomNumeric1": 102.51,
                "CustomNumeric2": 108.00,
                "CustomNumeric3": 115.25,
            },
        ),
    ],
)
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_checkout_total_excise_data(
    reset_sequences,  # pylint: disable=unused-argument
    expected_net,
    expected_gross,
    taxes_in_prices,
    variant_sku,
    price,
    destination,
    metadata,
    checkout,
    product,
    shipping_zone,
    address_usa,
    site_settings,
    monkeypatch,
    plugin_configuration,
    cigar_product_type,
):
    plugin_configuration()
    monkeypatch.setattr(
        "saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin._skip_plugin",
        lambda *_: False,
    )
    manager = get_plugins_manager()

    address_usa.city = destination["city"]
    address_usa.postal_code = destination["postal_code"]
    address_usa.country_area = destination["country_area"]
    address_usa.save()

    checkout.shipping_address = address_usa
    checkout.billing_address = address_usa
    shipping_method = shipping_zone.shipping_methods.get()
    shipping_method.price_amount = 0
    shipping_method.save()
    checkout.shipping_method = shipping_method

    metadata = {
        get_metadata_key("UnitQuantity"): metadata["UnitQuantity"],
        get_metadata_key("CustomNumeric1"): metadata["CustomNumeric1"],
        get_metadata_key("CustomNumeric2"): metadata["CustomNumeric2"],
        get_metadata_key("CustomNumeric3"): metadata["CustomNumeric3"],
    }

    product.product_type = cigar_product_type
    product.save()

    variant = product.variants.get()
    variant.sku = variant_sku
    variant.private_metadata = metadata
    variant.price_amount = Decimal(price)
    variant.save()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()

    site_settings.company_address = address_usa
    site_settings.include_taxes_in_prices = taxes_in_prices
    site_settings.save()

    lines, _ = fetch_checkout_lines(checkout)
    total = manager.calculate_checkout_total(checkout_info, lines, address_usa, [])
    total = quantize_price(total, total.currency)
    assert total == TaxedMoney(
        net=Money(expected_net, "USD"), gross=Money(expected_gross, "USD")
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_preprocess_order_creation(
    checkout_with_item,
    address,
    address_usa_va,
    site_settings,
    shipping_zone,
    discount_info,
    plugin_configuration,
):
    plugin_configuration()
    manager = get_plugins_manager()
    site_settings.company_address = address
    site_settings.save()

    checkout_with_item.shipping_address = address_usa_va
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = [discount_info]
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, discounts, manager)
    manager.preprocess_order_creation(checkout_info, discounts, lines)


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_preprocess_order_creation_wrong_data(
    checkout_with_item,
    address,
    shipping_zone,
    plugin_configuration,
):
    plugin_configuration()

    manager = get_plugins_manager()

    checkout_with_item.shipping_address = address
    checkout_with_item.shipping_method = shipping_zone.shipping_methods.get()
    checkout_with_item.save()
    discounts = []
    checkout_info = fetch_checkout_info(checkout_with_item, [], discounts, manager)
    lines, _ = fetch_checkout_lines(checkout_with_item)

    with pytest.raises(TaxError) as e:
        manager.preprocess_order_creation(checkout_info, discounts, lines)
    # Fails due to no ATE scenario these from/to addresses
    assert "No Scenario record found" in e._excinfo[1].args[0]


@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
@patch("saleor.plugins.avatax_excise.plugin.api_post_request_task.delay")
def test_preprocess_order_creation_no_lines(
    api_post_request_task_mock,
    checkout,
    address,
    shipping_zone,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager()

    checkout.shipping_address = address
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    # when
    manager.preprocess_order_creation(checkout_info, [], lines)

    # then
    api_post_request_task_mock.assert_not_called()


def test_api_post_request_handles_request_errors(product, monkeypatch):
    mocked_response = Mock(side_effect=RequestException())
    monkeypatch.setattr(
        "saleor.plugins.avatax_excise.utils.requests.post", mocked_response
    )

    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
    )
    url = "https://www.avatax.api.com/some-get-path"

    response = api_post_request(url, {}, config)

    assert mocked_response.called
    assert response == {}


def test_api_post_request_handles_json_errors(product, monkeypatch):
    mocked_response = Mock(side_effect=json.JSONDecodeError("", "", 0))
    monkeypatch.setattr(
        "saleor.plugins.avatax_excise.utils.requests.post", mocked_response
    )

    config = AvataxConfiguration(
        username_or_account="test",
        password_or_license="test",
        use_sandbox=False,
    )
    url = "https://www.avatax.api.com/some-get-path"

    response = api_post_request(url, {}, config)

    assert mocked_response.called
    assert response == {}


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
@patch("saleor.plugins.avatax_excise.plugin.api_post_request_task.delay")
def test_order_created_calls_task(
    api_post_request_task_mock,
    order_with_lines,
    address,
    address_usa_va,
    site_settings,
    shipping_zone,
    plugin_configuration,
):
    config = plugin_configuration()
    manager = get_plugins_manager()

    site_settings.company_address = address
    site_settings.save()

    order_with_lines.shipping_address = address_usa_va
    order_with_lines.shipping_method = shipping_zone.shipping_methods.get()
    order_with_lines.save()

    manager.order_created(order_with_lines)

    base_url = "https://excisesbx.avalara.com/"
    transaction_url = urljoin(base_url, "api/v1/AvaTaxExcise/transactions/create")
    commit_url = urljoin(base_url, "api/v1/AvaTaxExcise/transactions/{}/commit")
    data = get_order_request_data(order_with_lines)
    conf = {data["name"]: data["value"] for data in config.configuration}
    configuration = {
        "username_or_account": conf["Username or account"],
        "password_or_license": conf["Password or license"],
        "use_sandbox": True,
        "company_name": conf["Company name"],
        "autocommit": False,
        "shipping_product_code": "TAXFREIGHT",
    }

    api_post_request_task_mock.assert_called_once_with(
        transaction_url,
        asdict(data),
        configuration,
        order_with_lines.id,
        commit_url,
    )


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_order_created(
    order_with_lines,
    product,
    shipping_zone,
    address_usa_va,
    site_settings,
    plugin_configuration,
    cigar_product_type,
):
    plugin_configuration()
    manager = get_plugins_manager()

    site_settings.company_address = address_usa_va
    site_settings.save()

    order_with_lines.shipping_address = address_usa_va
    order_with_lines.shipping_method = shipping_zone.shipping_methods.get()
    shipping_method = shipping_zone.shipping_methods.get()
    shipping_method.price_amount = 0
    shipping_method.save()
    order_with_lines.shipping_method = shipping_method

    product.product_type = cigar_product_type
    product.save()

    variant = product.variants.first()
    variant.sku = "202015500"
    variant.price_amount = Decimal(170)
    variant.save()

    for order_line in order_with_lines.lines.all():
        order_line.product_name = product.name
        order_line.variant_name = variant.name
        order_line.product_sku = variant.sku
        order_line.variant = variant
        order_line.save()

    order_with_lines.save()

    manager.order_created(order_with_lines)


@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
@patch("saleor.plugins.avatax_excise.plugin.api_post_request_task.delay")
def test_order_created_no_lines(
    api_post_request_task_mock,
    order,
    plugin_configuration,
):
    # given
    plugin_configuration()
    manager = get_plugins_manager()

    # when
    manager.order_created(order)

    # then
    api_post_request_task_mock.assert_not_called()


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_order_line_unit(
    order_line,
    shipping_zone,
    site_settings,
    address_usa,
    plugin_configuration,
    cigar_product_type,
    address_usa_va,
):
    plugin_configuration()
    manager = get_plugins_manager()

    site_settings.company_address = address_usa_va
    site_settings.save()
    order_line.id = uuid.uuid4()
    unit_price = TaxedMoney(net=Money("10.00", "USD"), gross=Money("10.00", "USD"))
    order_line.unit_price = unit_price
    order_line.base_unit_price = unit_price.gross
    order_line.undiscounted_unit_price = unit_price
    order_line.undiscounted_base_unit_price = unit_price.gross
    order_line.save()

    variant = order_line.variant
    variant.sku = "202015500"
    variant.save()

    product = variant.product
    product.product_type = cigar_product_type
    product.save()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address_usa_va
    order.billing_address = address_usa_va
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    line_price_data = manager.calculate_order_line_unit(
        order, order_line, order_line.variant, order_line.variant.product
    )

    expected_line_price = TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.57", "USD")
    )
    assert line_price_data.price_with_discounts == expected_line_price


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_order_line_unit_the_order_changed(
    order_line,
    shipping_zone,
    site_settings,
    address_usa,
    plugin_configuration,
    cigar_product_type,
    address_usa_va,
):
    """Ensure that when the order order lines have changed the method will return
    the correct value.
    """
    plugin_configuration()
    manager = get_plugins_manager()

    site_settings.company_address = address_usa_va
    site_settings.save()

    order_line.id = None
    unit_price = TaxedMoney(net=Money("10.00", "USD"), gross=Money("10.00", "USD"))
    order_line.unit_price = unit_price
    order_line.base_unit_price = unit_price.gross
    order_line.undiscounted_unit_price = unit_price
    order_line.undiscounted_base_unit_price = unit_price.gross
    order_line.save()

    variant = order_line.variant
    variant.sku = "202015500"
    variant.save()

    product = variant.product
    product.product_type = cigar_product_type
    product.save()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address_usa_va
    order.billing_address = address_usa_va
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.save()

    # calculating the order line unit for the first time
    line_price_data = manager.calculate_order_line_unit(
        order, order_line, order_line.variant, order_line.variant.product
    )

    expected_line_price = TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.57", "USD")
    )
    assert line_price_data.price_with_discounts == expected_line_price

    # remove the first line add a new one
    order.lines.first().delete()
    second_order_line = order.lines.last()
    second_order_line.id = None
    # set different price than the first line
    second_order_line.unit_price = TaxedMoney(
        net=Money("25.00", "USD"), gross=Money("25.00", "USD")
    )
    second_order_line.undiscounted_unit_price = TaxedMoney(
        net=Money("25.00", "USD"), gross=Money("25.00", "USD")
    )
    second_order_line.save()

    # calculating the order line unit for the second time
    line_price_data = manager.calculate_order_line_unit(
        order, order_line, order_line.variant, order_line.variant.product
    )

    expected_line_price = TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.57", "USD")
    )
    assert line_price_data.price_with_discounts == expected_line_price


@pytest.mark.vcr
@override_settings(PLUGINS=["saleor.plugins.avatax_excise.plugin.AvataxExcisePlugin"])
def test_calculate_order_total(
    order_line,
    shipping_zone,
    site_settings,
    address_usa,
    plugin_configuration,
    cigar_product_type,
    address_usa_va,
):
    plugin_configuration()
    manager = get_plugins_manager()

    site_settings.company_address = address_usa_va
    site_settings.save()
    order_line.id = uuid.uuid4()
    unit_price = TaxedMoney(net=Money("10.00", "USD"), gross=Money("10.00", "USD"))
    order_line.unit_price = unit_price
    order_line.base_unit_price = unit_price.gross
    order_line.undiscounted_unit_price = unit_price
    order_line.undiscounted_base_unit_price = unit_price.gross
    order_line.save()

    variant = order_line.variant
    variant.sku = "202015500"
    variant.save()

    product = variant.product
    product.product_type = cigar_product_type
    product.save()

    order = order_line.order
    method = shipping_zone.shipping_methods.get()
    order.shipping_address = address_usa_va
    order.billing_address = address_usa_va
    order.shipping_method_name = method.name
    order.shipping_method = method
    order.base_shipping_price = method.channel_listings.get(channel=order.channel).price
    order.save()

    total_price = manager.calculate_order_total(order, order.lines.all())

    expected_total = TaxedMoney(net=Money("76.90", "USD"), gross=Money("80.30", "USD"))
    assert total_price == expected_total
