import datetime
from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone

from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....checkout.utils import (
    add_variant_to_checkout,
    add_voucher_to_checkout,
    invalidate_checkout,
)
from .....plugins.base_plugin import ExcludedShippingMethod
from .....plugins.manager import get_plugins_manager
from .....warehouse.models import Reservation, Stock
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content
from ...mutations.utils import update_checkout_shipping_method_if_invalid

MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE = """
    mutation checkoutShippingAddressUpdate(
            $id: ID,
            $shippingAddress: AddressInput!,
            $validationRules: CheckoutAddressValidationRules
        ) {
        checkoutShippingAddressUpdate(
                id: $id,
                shippingAddress: $shippingAddress,
                validationRules: $validationRules
        ) {
            checkout {
                token
                id
                shippingMethods{
                    id
                    name
                }
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


MUTATION_CHECKOUT_SHIPPING_ADDRESS_WITH_METADATA_UPDATE = """
    mutation checkoutShippingAddressUpdate(
            $id: ID,
            $shippingAddress: AddressInput!,
            $validationRules: CheckoutAddressValidationRules
        ) {
        checkoutShippingAddressUpdate(
                id: $id,
                shippingAddress: $shippingAddress,
                validationRules: $validationRules
        ) {
            checkout {
                token
                id
                shippingMethods{
                    id
                    name
                }
                shippingAddress {
                    metadata {
                        key
                        value
                    }
                }
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_address_with_metadata_update(
    mocked_invalidate_checkout,
    mocked_update_shipping_method,
    user_api_client,
    checkout_with_item,
    graphql_address_data,
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_WITH_METADATA_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.shipping_address.metadata == {"public": "public_value"}

    assert checkout.shipping_address is not None
    assert checkout.shipping_address.first_name == shipping_address["firstName"]
    assert checkout.shipping_address.last_name == shipping_address["lastName"]
    assert (
        checkout.shipping_address.street_address_1 == shipping_address["streetAddress1"]
    )
    assert (
        checkout.shipping_address.street_address_2 == shipping_address["streetAddress2"]
    )
    assert checkout.shipping_address.postal_code == shipping_address["postalCode"]
    assert checkout.shipping_address.country == shipping_address["country"]
    assert checkout.shipping_address.city == shipping_address["city"].upper()
    assert checkout.shipping_address.validation_skipped is False
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_changes_checkout_country(
    mocked_update_shipping_method,
    user_api_client,
    channel_USD,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.shipping_address is not None
    assert checkout.shipping_address.first_name == shipping_address["firstName"]
    assert checkout.shipping_address.last_name == shipping_address["lastName"]
    assert (
        checkout.shipping_address.street_address_1 == shipping_address["streetAddress1"]
    )
    assert (
        checkout.shipping_address.street_address_2 == shipping_address["streetAddress2"]
    )
    assert checkout.shipping_address.postal_code == shipping_address["postalCode"]
    assert checkout.shipping_address.country == shipping_address["country"]
    assert checkout.shipping_address.city == shipping_address["city"].upper()
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_update_shipping_method.assert_called_once_with(checkout_info, lines)
    assert checkout.country == shipping_address["country"]
    assert checkout.last_change != previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_insufficient_stocks(
    mocked_update_shipping_method,
    channel_USD,
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 1)
    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=0)
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_doesnt_raise_error(
    mocked_update_shipping_method,
    channel_USD,
    user_api_client,
    product_list,
    graphql_address_data,
):
    variant_a = product_list[0].variants.first()
    variant_b = product_list[1].variants.first()
    Stock.objects.filter(product_variant=variant_a).update(quantity=4)
    Stock.objects.filter(product_variant=variant_b).update(quantity=1)
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant_b, 1)
    add_variant_to_checkout(checkout_info, variant_a, 4)
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_with_reserved_stocks(
    mocked_update_shipping_method,
    site_settings_with_reservations,
    channel_USD,
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 2)
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }
    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=variant,
        quantity=1,
    )
    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=variant.stocks.filter(
            warehouse__shipping_zones__countries__contains="US"
        ).first(),
        quantity_reserved=1,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "update_checkout_shipping_method_if_invalid",
    wraps=update_checkout_shipping_method_if_invalid,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_against_reserved_stocks(
    mocked_update_shipping_method,
    site_settings_with_reservations,
    channel_USD,
    user_api_client,
    variant_with_many_stocks_different_shipping_zones,
    graphql_address_data,
):
    variant = variant_with_many_stocks_different_shipping_zones
    checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    checkout.set_country("PL", commit=True)
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    add_variant_to_checkout(checkout_info, variant, 2)
    Stock.objects.filter(
        warehouse__shipping_zones__countries__contains="US", product_variant=variant
    ).update(quantity=2)
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["country"] = "US"
    shipping_address["countryArea"] = "New York"
    shipping_address["postalCode"] = "10001"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    other_checkout = Checkout.objects.create(channel=channel_USD, currency="USD")
    other_checkout_line = other_checkout.lines.create(
        variant=variant,
        quantity=3,
    )
    Reservation.objects.create(
        checkout_line=other_checkout_line,
        stock=variant.stocks.filter(
            warehouse__shipping_zones__countries__contains="US"
        ).first(),
        quantity_reserved=3,
        reserved_until=timezone.now() + datetime.timedelta(minutes=5),
    )

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"


def test_checkout_shipping_address_update_channel_without_shipping_zones(
    user_api_client,
    checkout_with_item,
    graphql_address_data,
):
    checkout = checkout_with_item
    checkout.channel.shipping_zones.clear()
    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.INSUFFICIENT_STOCK.name
    assert errors[0]["field"] == "quantity"
    checkout.refresh_from_db()
    assert checkout.last_change == previous_last_change


def test_checkout_shipping_address_with_invalid_phone_number_returns_error(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["phone"] = "+33600000"

    response = get_graphql_content(
        user_api_client.post_graphql(
            MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
            {
                "id": to_global_id_or_none(checkout),
                "shippingAddress": shipping_address,
            },
        )
    )["data"]["checkoutShippingAddressUpdate"]

    assert response["errors"] == [
        {
            "field": "phone",
            "message": "'+33600000' is not a valid phone number.",
            "code": CheckoutErrorCode.INVALID.name,
        }
    ]


@pytest.mark.parametrize(
    "number", ["+48321321888", "+44 (113) 892-1113", "00 44 (0) 20 7839 1377"]
)
def test_checkout_shipping_address_update_with_phone_country_prefix(
    number, user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["phone"] = number
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


def test_checkout_shipping_address_update_without_phone_country_prefix(
    user_api_client, checkout_with_item, graphql_address_data
):
    checkout = checkout_with_item
    assert checkout.shipping_address is None

    shipping_address = graphql_address_data
    shipping_address["phone"] = "+1-202-555-0132"
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]


@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_checkout_shipping_address_update_exclude_shipping_method(
    mocked_webhook,
    user_api_client,
    checkout_with_items_and_shipping,
    graphql_address_data,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    checkout = checkout_with_items_and_shipping
    shipping_method = checkout.shipping_method
    assert shipping_method is not None
    webhook_reason = "hello-there"
    mocked_webhook.return_value = [
        ExcludedShippingMethod(shipping_method.id, webhook_reason)
    ]
    shipping_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    user_api_client.post_graphql(MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables)
    checkout.refresh_from_db()
    assert checkout.shipping_method is None


@pytest.mark.parametrize(
    "address_data",
    [
        {"country": "PL"},  # missing postalCode, streetAddress
        {"country": "PL", "postalCode": ""},
        {"country": "PL", "postalCode": "53-601"},  # missing streetAddress
        {"country": "US"},
        {
            "country": "US",
            "city": "New York",
        },  # missing postalCode, streetAddress, countryArea
    ],
)
def test_checkout_shipping_address_update_with_skip_required_doesnt_raise_error(
    address_data, checkout_with_items, user_api_client
):
    # given
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": address_data,
        "validationRules": {"checkRequiredFields": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    assert checkout_with_items.shipping_address


def test_checkout_shipping_address_update_with_skip_required_overwrite_address(
    checkout_with_items, user_api_client, address
):
    # given
    checkout_with_items.shipping_address = address
    checkout_with_items.save()

    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": {
            "postalCode": "",
            "city": "",
            "country": "US",
        },
        "validationRules": {"checkRequiredFields": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]

    assert checkout_with_items.shipping_address.city == ""
    assert checkout_with_items.shipping_address.postal_code == ""


def test_checkout_shipping_address_update_with_skip_required_raises_validation_error(
    checkout_with_items, user_api_client
):
    # given
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": {"country": "US", "postalCode": "XX-123"},
        "validationRules": {"checkRequiredFields": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["field"] == "postalCode"
    assert not checkout_with_items.shipping_address


def test_checkout_shipping_address_update_with_skip_required_saves_address(
    checkout_with_items, user_api_client
):
    # given
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": {"country": "PL", "postalCode": "53-601"},
        "validationRules": {"checkRequiredFields": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]

    assert checkout_with_items.shipping_address
    assert checkout_with_items.shipping_address.country.code == "PL"
    assert checkout_with_items.shipping_address.postal_code == "53-601"


@pytest.mark.parametrize(
    "address_data",
    [
        {
            "country": "PL",
            "city": "Wroclaw",
            "postalCode": "XYZ",
            "streetAddress1": "Teczowa 7",
        },  # incorrect postalCode
        {
            "country": "US",
            "city": "New York",
            "countryArea": "ABC",
            "streetAddress1": "New street",
            "postalCode": "53-601",
        },  # incorrect postalCode
    ],
)
def test_checkout_shipping_address_update_with_skip_value_check_doesnt_raise_error(
    address_data, checkout_with_items, user_api_client
):
    # given
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": address_data,
        "validationRules": {"checkFieldsFormat": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    assert checkout_with_items.shipping_address


@pytest.mark.parametrize(
    "address_data",
    [
        {
            "country": "PL",
            "city": "Wroclaw",
            "postalCode": "XYZ",
        },  # incorrect postalCode
        {
            "country": "US",
            "city": "New York",
            "countryArea": "XYZ",
            "postalCode": "XYZ",
        },  # incorrect postalCode
    ],
)
def test_checkout_shipping_address_update_with_skip_value_raises_required_fields_error(
    address_data, checkout_with_items, user_api_client
):
    # given
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": address_data,
        "validationRules": {"checkFieldsFormat": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "REQUIRED"
    assert data["errors"][0]["field"] == "streetAddress1"
    assert not checkout_with_items.shipping_address


def test_checkout_shipping_address_update_with_skip_value_check_saves_address(
    checkout_with_items, user_api_client
):
    # given
    city = "Wroclaw"
    street_address = "Teczowa 7"
    postal_code = "XX-601"  # incorrect format for PL
    country_code = "PL"
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": {
            "country": country_code,
            "city": city,
            "streetAddress1": street_address,
            "postalCode": postal_code,
        },
        "validationRules": {"checkFieldsFormat": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]

    address = checkout_with_items.shipping_address
    assert address

    assert address.street_address_1 == street_address
    assert address.city == city
    assert address.country.code == country_code
    assert address.postal_code == postal_code


@pytest.mark.parametrize(
    "address_data",
    [
        {
            "country": "PL",
            "postalCode": "XYZ",
        },  # incorrect postalCode, missing city, streetAddress
        {
            "country": "US",
            "countryArea": "DC",
            "postalCode": "XYZ",
        },  # incorrect postalCode, missing city
    ],
)
def test_checkout_shipping_address_update_with_skip_value_and_skip_required_fields(
    address_data, checkout_with_items, user_api_client
):
    # given
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": address_data,
        "validationRules": {"checkFieldsFormat": False, "checkRequiredFields": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    assert checkout_with_items.shipping_address


def test_checkout_address_update_with_skip_value_and_skip_required_saves_address(
    checkout_with_items, user_api_client
):
    # given
    city = "Wroclaw"
    postal_code = "XX-601"  # incorrect format for PL
    country_code = "PL"

    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": {
            "country": country_code,
            "city": city,
            "postalCode": postal_code,
        },
        "validationRules": {"checkFieldsFormat": False, "checkRequiredFields": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    address = checkout_with_items.shipping_address
    assert not data["errors"]

    assert address
    assert address.country.code == country_code
    assert address.postal_code == postal_code
    assert address.city == city
    assert address.street_address_1 == ""


def test_checkout_shipping_address_update_with_disabled_fields_normalization(
    checkout_with_items, user_api_client
):
    # given
    address_data = {
        "country": "US",
        "city": "Washington",
        "countryArea": "District of Columbia",
        "streetAddress1": "1600 Pennsylvania Avenue NW",
        "postalCode": "20500",
    }
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": address_data,
        "validationRules": {"enableFieldsNormalization": False},
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    checkout_with_items.refresh_from_db()

    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    assert checkout_with_items
    shipping_address = checkout_with_items.shipping_address
    assert shipping_address
    assert shipping_address.city == address_data["city"]
    assert shipping_address.country_area == address_data["countryArea"]
    assert shipping_address.postal_code == address_data["postalCode"]
    assert shipping_address.street_address_1 == address_data["streetAddress1"]


def test_checkout_update_shipping_address_with_digital(
    api_client, checkout_with_digital_item, graphql_address_data
):
    """Test updating the shipping address of a digital order throws an error."""

    checkout = checkout_with_digital_item
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": graphql_address_data,
    }

    response = api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]

    assert data["errors"] == [
        {
            "field": "shippingAddress",
            "message": "This checkout doesn't need shipping",
            "code": CheckoutErrorCode.SHIPPING_NOT_REQUIRED.name,
        }
    ]

    # Ensure the address was unchanged
    checkout.refresh_from_db(fields=["shipping_address"])
    assert checkout.shipping_address is None


def test_checkout_shipping_address_update_with_not_applicable_voucher(
    user_api_client,
    checkout_with_item,
    voucher_shipping_type,
    graphql_address_data,
    address_other_country,
    shipping_method,
):
    assert checkout_with_item.shipping_address is None
    assert checkout_with_item.voucher_code is None

    checkout_with_item.shipping_address = address_other_country
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])
    assert checkout_with_item.shipping_address.country == address_other_country.country

    voucher = voucher_shipping_type
    code = voucher.codes.first()
    assert voucher.countries[0].code == address_other_country.country

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    add_voucher_to_checkout(manager, checkout_info, lines, voucher, code)
    assert checkout_with_item.voucher_code == code.code

    new_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "shippingAddress": new_address,
    }
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]

    checkout_with_item.refresh_from_db()
    checkout_with_item.shipping_address.refresh_from_db()

    assert checkout_with_item.shipping_address.country == new_address["country"]
    assert checkout_with_item.voucher_code is None


def test_with_active_problems_flow(
    api_client,
    checkout_with_problems,
    graphql_address_data,
):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    new_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "shippingAddress": new_address,
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutShippingAddressUpdate"]["errors"]


def test_checkout_shipping_address_update_with_collection_point_already_set(
    user_api_client,
    checkout_with_item,
    graphql_address_data,
    warehouse_for_cc,
):
    checkout = checkout_with_item
    checkout.collection_point_id = warehouse_for_cc.id
    checkout.save(update_fields=["collection_point_id"])

    shipping_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    errors = data["errors"]
    assert errors[0]["code"] == CheckoutErrorCode.SHIPPING_CHANGE_FORBIDDEN.name
    assert errors[0]["field"] == "shippingAddress"


def test_checkout_shipping_address_skip_validation_by_customer(
    checkout_with_items, user_api_client, graphql_address_data_skipped_validation
):
    # given
    address_data = graphql_address_data_skipped_validation
    invalid_postal_code = "invalid_postal_code"
    address_data["postalCode"] = invalid_postal_code

    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": address_data,
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )

    # then
    assert_no_permission(response)


def test_checkout_shipping_address_skip_validation_by_app(
    checkout_with_items,
    app_api_client,
    graphql_address_data_skipped_validation,
    permission_handle_checkouts,
):
    # given
    checkout = checkout_with_items
    address_data = graphql_address_data_skipped_validation
    invalid_postal_code = "invalid_postal_code"
    address_data["postalCode"] = invalid_postal_code

    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": address_data,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
        variables,
        permissions=[permission_handle_checkouts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.shipping_address.postal_code == invalid_postal_code
    assert checkout.shipping_address.validation_skipped is True
