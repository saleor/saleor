import datetime
from unittest import mock
from unittest.mock import ANY, patch

import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....checkout.actions import call_checkout_info_event
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import Checkout
from .....checkout.utils import (
    add_variant_to_checkout,
    add_voucher_to_checkout,
    invalidate_checkout,
)
from .....core.models import EventDelivery
from .....plugins.manager import get_plugins_manager
from .....product.models import ProductChannelListing, ProductVariantChannelListing
from .....warehouse.models import Reservation, Stock
from .....webhook.event_types import WebhookEventAsyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content
from ...mutations.utils import mark_checkout_deliveries_as_stale_if_needed
from ..utils import assert_address_data

MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE = """
    mutation checkoutShippingAddressUpdate(
            $id: ID,
            $shippingAddress: AddressInput!,
            $validationRules: CheckoutAddressValidationRules
            $saveAddress: Boolean
        ) {
        checkoutShippingAddressUpdate(
                id: $id,
                shippingAddress: $shippingAddress,
                validationRules: $validationRules
                saveAddress: $saveAddress
        ) {
            checkout {
                token
                id
                shippingMethods{
                    id
                    name
                }
                shippingAddress {
                    postalCode
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
    "mark_checkout_deliveries_as_stale_if_needed",
    wraps=mark_checkout_deliveries_as_stale_if_needed,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_address_with_metadata_update(
    mocked_invalidate_checkout,
    mocked_mark_shipping_methods_as_stale,
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
    assert_address_data(checkout.shipping_address, shipping_address)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_mark_shipping_methods_as_stale.assert_called_once_with(
        checkout_info.checkout, lines
    )
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1
    assert checkout.save_shipping_address is True


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "mark_checkout_deliveries_as_stale_if_needed",
    wraps=mark_checkout_deliveries_as_stale_if_needed,
)
@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "invalidate_checkout",
    wraps=invalidate_checkout,
)
def test_checkout_shipping_address_when_variant_without_listing(
    mocked_invalidate_checkout,
    mocked_mark_shipping_methods_as_stale,
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item,
    graphql_address_data,
):
    # given
    checkout = checkout_with_item
    line = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id, **{listing_filter_field: line.variant_id}
    ).delete()

    assert checkout.shipping_address is None
    previous_last_change = checkout.last_change

    shipping_address = graphql_address_data
    variables = {
        "id": to_global_id_or_none(checkout_with_item),
        "shippingAddress": shipping_address,
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_WITH_METADATA_UPDATE, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert_address_data(checkout.shipping_address, shipping_address)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_mark_shipping_methods_as_stale.assert_called_once_with(
        checkout_info.checkout, lines
    )
    assert checkout.last_change != previous_last_change
    assert mocked_invalidate_checkout.call_count == 1
    assert checkout.save_shipping_address is True


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "mark_checkout_deliveries_as_stale_if_needed",
    wraps=mark_checkout_deliveries_as_stale_if_needed,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_changes_checkout_country(
    mocked_mark_shipping_methods_as_stale,
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
    assert_address_data(checkout.shipping_address, shipping_address)
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    mocked_mark_shipping_methods_as_stale.assert_called_once_with(
        checkout_info.checkout, lines
    )
    assert checkout.country == shipping_address["country"]
    assert checkout.last_change != previous_last_change
    assert checkout.save_shipping_address is True


@mock.patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update."
    "mark_checkout_deliveries_as_stale_if_needed",
    wraps=mark_checkout_deliveries_as_stale_if_needed,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_insufficient_stocks(
    mocked_mark_shipping_methods_as_stale,
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
    "mark_checkout_deliveries_as_stale_if_needed",
    wraps=mark_checkout_deliveries_as_stale_if_needed,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_doesnt_raise_error(
    mocked_mark_shipping_methods_as_stale,
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
    "mark_checkout_deliveries_as_stale_if_needed",
    wraps=mark_checkout_deliveries_as_stale_if_needed,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_with_reserved_stocks(
    mocked_mark_shipping_methods_as_stale,
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
        undiscounted_unit_price_amount=variant.channel_listings.get(
            channel=channel_USD
        ).price_amount,
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
    "mark_checkout_deliveries_as_stale_if_needed",
    wraps=mark_checkout_deliveries_as_stale_if_needed,
)
@override_settings(DEFAULT_COUNTRY="DE")
def test_checkout_shipping_address_update_against_reserved_stocks(
    mocked_mark_shipping_methods_as_stale,
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
        undiscounted_unit_price_amount=variant.channel_listings.get(
            channel=channel_USD
        ).price_amount,
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

    assert not data["errors"]
    assert data["checkout"]["shippingAddress"]

    # Ensure the address was set
    checkout.refresh_from_db(fields=["shipping_address"])
    assert checkout.shipping_address
    assert_address_data(checkout.shipping_address, graphql_address_data)


def test_checkout_shipping_address_update_with_not_applicable_voucher(
    user_api_client,
    checkout_with_item,
    voucher_shipping_type,
    graphql_address_data,
    address_other_country,
    checkout_delivery,
):
    assert checkout_with_item.shipping_address is None
    assert checkout_with_item.voucher_code is None

    checkout_with_item.shipping_address = address_other_country
    checkout_with_item.assigned_delivery = checkout_delivery(checkout_with_item)
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
        "saveAddress": False,
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


MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE_WITH_ONLY_ID = """
    mutation checkoutShippingAddressUpdate(
            $id: ID,
            $shippingAddress: AddressInput!,
            $validationRules: CheckoutAddressValidationRules
            $saveAddress: Boolean
        ) {
        checkoutShippingAddressUpdate(
                id: $id,
                shippingAddress: $shippingAddress,
                validationRules: $validationRules
                saveAddress: $saveAddress
        ) {
            checkout {
                id
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@patch(
    "saleor.graphql.checkout.mutations.checkout_shipping_address_update.call_checkout_info_event",
    wraps=call_checkout_info_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_shipping_address_update_triggers_webhooks(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_info_event,
    setup_checkout_webhooks,
    settings,
    user_api_client,
    checkout_with_item,
    graphql_address_data,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    checkout = checkout_with_item
    assert checkout.shipping_address is None

    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": graphql_address_data,
    }

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE_WITH_ONLY_ID, variables
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutShippingAddressUpdate"]["errors"]

    assert wrapped_call_checkout_info_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )

    mocked_generate_deferred_payloads.assert_called_once_with(
        kwargs={
            "event_delivery_ids": [checkout_update_delivery.id],
            "deferred_payload_data": {
                "model_name": "checkout.checkout",
                "object_id": checkout_with_item.pk,
                "requestor_model_name": "account.user",
                "requestor_object_id": user_api_client.user.pk,
                "request_time": None,
            },
            "send_webhook_queue": settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            "telemetry_context": ANY,
        },
        MessageGroupId="example.com",
    )

    # Deferred payload covers the sync and async actions
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


def test_checkout_shipping_address_update_reset_the_save_address_flag_to_default_value(
    checkout_with_items,
    user_api_client,
    graphql_address_data,
    address,
):
    checkout = checkout_with_items
    # given checkout shipping and billing address set both save shipping flags different
    # than default value - set to False
    checkout.shipping_address = address
    checkout.billing_address = address
    checkout.save_shipping_address = False
    checkout.save_billing_address = False
    checkout.save(
        update_fields=[
            "shipping_address",
            "billing_address",
            "save_shipping_address",
            "save_billing_address",
        ]
    )

    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": graphql_address_data,
    }

    # when the checkout shipping address is updated without providing saveAddress flag
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
        variables,
    )
    content = get_graphql_content(response)

    # then the checkout shipping address is updated, and `save_shipping_address` is
    # reset to the default True value; the `save_billing_address` is not changed
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]

    checkout.refresh_from_db()
    assert_address_data(checkout.shipping_address, graphql_address_data)
    assert checkout.save_shipping_address is True
    assert checkout.save_billing_address is False


def test_checkout_shipping_address_update_with_save_address_to_false(
    checkout_with_items,
    user_api_client,
    graphql_address_data,
):
    # given checkout with default saving address values
    checkout = checkout_with_items

    save_address = False
    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": graphql_address_data,
        "saveAddress": save_address,
    }

    # when update shipping address with saveAddress flag set to False
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
        variables,
    )
    content = get_graphql_content(response)

    # then the address should be saved and the save_shipping_address should be False
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert_address_data(checkout.shipping_address, graphql_address_data)
    assert checkout.save_shipping_address is save_address
    assert checkout.save_billing_address is True


def test_checkout_shipping_address_update_change_save_address_option_to_true(
    checkout_with_items,
    user_api_client,
    graphql_address_data,
):
    # given checkout with save addresses settings to False
    checkout = checkout_with_items
    checkout.save_shipping_address = False
    checkout.save_billing_address = False
    checkout.save(update_fields=["save_shipping_address", "save_billing_address"])

    variables = {
        "id": to_global_id_or_none(checkout_with_items),
        "shippingAddress": graphql_address_data,
        "saveAddress": True,
    }

    # when the shipping address is updated with saveAddress flag set to True
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE,
        variables,
    )
    content = get_graphql_content(response)

    # then the address should be saved and the save_shipping_address should be True
    # the save_billing_address should not be changed
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert_address_data(checkout.shipping_address, graphql_address_data)
    assert checkout.save_shipping_address is True
    assert checkout.save_billing_address is False


def test_checkout_shipping_address_update_when_switching_from_cc(
    checkout_with_items,
    app_api_client,
    graphql_address_data_skipped_validation,
    permission_handle_checkouts,
    shipping_method,
    address,
):
    # given
    checkout = checkout_with_items
    address_data = graphql_address_data_skipped_validation
    # after switching for cc to standard shipping method - the shipping method is set
    # and the shipping address is cleared
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.shipping_address = None
    checkout.save(
        update_fields=["shipping_method", "billing_address", "shipping_address"]
    )

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
    assert checkout.shipping_address


@freeze_time("2024-05-31 12:00:01")
def test_checkout_shipping_address_marks_shipping_as_stale(
    user_api_client,
    checkout_with_item,
    graphql_address_data,
    checkout_delivery,
    address,
):
    # given
    checkout = checkout_with_item
    assert checkout.shipping_address is None

    expected_stale_time = timezone.now() + timezone.timedelta(minutes=10)
    checkout = checkout_with_item
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = expected_stale_time
    checkout.save(
        update_fields=[
            "assigned_delivery",
            "shipping_address",
            "delivery_methods_stale_at",
        ]
    )

    query = MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE_WITH_ONLY_ID
    shipping_address = graphql_address_data

    variables = {
        "id": to_global_id_or_none(checkout),
        "shippingAddress": shipping_address,
    }

    # when
    new_now = timezone.now()
    with freeze_time(new_now):
        response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.delivery_methods_stale_at == new_now
