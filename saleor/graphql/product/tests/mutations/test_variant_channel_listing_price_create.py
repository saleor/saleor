import datetime
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from django.utils import timezone

from .....attribute.models import AttributeValue
from .....product.error_codes import VariantChannelListingPriceErrorCode
from .....product.models import VariantChannelListingPrice
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION = """
    mutation VariantChannelListingPriceCreate(
        $input: VariantChannelListingPriceCreateInput!
    ) {
        variantChannelListingPriceCreate(input: $input) {
            variantChannelListingPrice {
                id
                price {
                    amount
                    currency
                }
                customerTypes {
                    id
                }
                attributeValues {
                    id
                }
                validFrom
                validTo
            }
            errors {
                field
                code
                message
                customerTypes
                attributeValues
            }
        }
    }
"""

PRICE = "7.50"
DAY = datetime.timedelta(days=1)


def _listing_id(variant):
    listing = variant.channel_listings.get()
    return graphene.Node.to_global_id("ProductVariantChannelListing", listing.pk)


def _gold_value(loyalty_customer_attribute):
    return AttributeValue.objects.get(attribute=loyalty_customer_attribute, slug="gold")


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", None, False),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
            None,
            False,
        ),
        (
            "Authenticated user w/o the permission should be rejected",
            "staff_api_client",
            None,
            False,
        ),
        (
            "Authenticated user w/ the correct permission should be allowed",
            "staff_api_client",
            "permission_manage_products",
            True,
        ),
        (
            "App w/ the correct permission should be allowed",
            "app_api_client",
            "permission_manage_products",
            True,
        ),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_authorization(
    product_variant_updated_mock,
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    request,
    variant,
    customer_type,
):
    # given
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        permission = request.getfixturevalue(permission_fixture)
        if client.app:
            client.app.permissions.add(permission)
        else:
            client.user.user_permissions.add(permission)
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            "customerTypes": [
                graphene.Node.to_global_id("CustomerType", customer_type.pk)
            ],
        }
    }

    # when
    response = client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
        assert data["errors"] == []
        assert VariantChannelListingPrice.objects.count() == 1
        assert product_variant_updated_mock.call_count == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["variantChannelListingPriceCreate"] is None
        assert VariantChannelListingPrice.objects.exists() is False
        assert product_variant_updated_mock.call_count == 0


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_with_every_condition(
    product_variant_updated_mock,
    staff_api_client,
    permission_manage_products,
    variant,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    listing = variant.channel_listings.get()
    gold_value = _gold_value(loyalty_customer_attribute)
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)
    value_id = graphene.Node.to_global_id("AttributeValue", gold_value.pk)
    valid_from = timezone.now().replace(microsecond=0)
    valid_to = valid_from + DAY
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            "customerTypes": [customer_type_id],
            "attributeValues": [value_id],
            "validFrom": valid_from.isoformat(),
            "validTo": valid_to.isoformat(),
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert data["errors"] == []
    row = VariantChannelListingPrice.objects.get()
    assert row.variant_channel_listing_id == listing.pk
    assert row.price_amount == Decimal(PRICE)
    assert row.currency == listing.currency
    assert row.valid_from == valid_from
    assert row.valid_to == valid_to
    assert list(row.customer_types.values_list("pk", flat=True)) == [customer_type.pk]
    assert list(row.attribute_values.values_list("pk", flat=True)) == [gold_value.pk]
    assert row.is_applied is False
    price_data = data["variantChannelListingPrice"]
    assert price_data["id"] == graphene.Node.to_global_id(
        "VariantChannelListingPrice", row.pk
    )
    assert price_data["price"] == {
        "amount": float(row.price_amount),
        "currency": row.currency,
    }
    assert price_data["customerTypes"] == [{"id": customer_type_id}]
    assert price_data["attributeValues"] == [{"id": value_id}]
    assert price_data["validFrom"] == valid_from.isoformat()
    assert price_data["validTo"] == valid_to.isoformat()
    product_variant_updated_mock.assert_called_once()
    assert product_variant_updated_mock.call_args.args[0] == variant


def test_a_window_row_folds_it_into_the_stored_price(
    staff_api_client, permission_manage_products, variant, product
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    assert product_listing.discounted_price_dirty is False
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            "validFrom": (timezone.now() - DAY).isoformat(),
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert data["errors"] == []
    row = VariantChannelListingPrice.objects.get()
    assert row.is_applied is True
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


@pytest.mark.parametrize(
    ("_case", "scope"),
    [
        ("no_condition_field", {}),
        ("null_conditions", {"customerTypes": None, "attributeValues": None}),
        ("empty_lists", {"customerTypes": [], "attributeValues": []}),
    ],
)
def test_rejects_a_row_without_conditions(
    _case, scope, staff_api_client, permission_manage_products, variant
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            **scope,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert data["variantChannelListingPrice"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] is None
    assert error["code"] == VariantChannelListingPriceErrorCode.REQUIRED.name
    assert error["message"] == (
        "A scoped price needs at least one customer type, one attribute value or "
        "a validity window."
    )
    assert VariantChannelListingPrice.objects.exists() is False


@pytest.mark.parametrize(
    ("_case", "valid_from_offset", "valid_to_offset"),
    [
        ("empty_window", DAY, DAY),
        ("inverted_window", 2 * DAY, DAY),
    ],
)
def test_rejects_a_window_that_does_not_end_after_it_starts(
    _case,
    valid_from_offset,
    valid_to_offset,
    staff_api_client,
    permission_manage_products,
    variant,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    now = timezone.now()
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            "validFrom": (now + valid_from_offset).isoformat(),
            "validTo": (now + valid_to_offset).isoformat(),
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "validTo"
    assert error["code"] == VariantChannelListingPriceErrorCode.INVALID.name
    assert error["message"] == (
        "The end of the validity window must be after its start."
    )
    assert VariantChannelListingPrice.objects.exists() is False


def test_rejects_values_of_non_customer_attributes(
    staff_api_client,
    permission_manage_products,
    variant,
    color_attribute,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    color_value = color_attribute.values.first()
    color_value_id = graphene.Node.to_global_id("AttributeValue", color_value.pk)
    gold_value_id = graphene.Node.to_global_id(
        "AttributeValue", _gold_value(loyalty_customer_attribute).pk
    )
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            "attributeValues": [gold_value_id, color_value_id],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributeValues"
    assert error["code"] == VariantChannelListingPriceErrorCode.INVALID.name
    assert error["message"] == (
        "Only values of customer attributes with a fixed set of choices can scope "
        "a price."
    )
    assert error["attributeValues"] == [color_value_id]
    assert VariantChannelListingPrice.objects.exists() is False


@pytest.mark.parametrize(
    ("_case", "field", "type_name"),
    [
        ("unknown_customer_type", "customerTypes", "CustomerType"),
        ("unknown_attribute_value", "attributeValues", "AttributeValue"),
    ],
)
def test_rejects_unknown_condition_ids(
    _case, field, type_name, staff_api_client, permission_manage_products, variant
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    unknown_id = graphene.Node.to_global_id(type_name, -1)
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            field: [unknown_id],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == field
    assert error["code"] == VariantChannelListingPriceErrorCode.GRAPHQL_ERROR.name
    assert error["message"] == (
        f"Could not resolve to a node with the global id list of '['{unknown_id}']'."
    )
    assert VariantChannelListingPrice.objects.exists() is False


def test_rejects_an_unknown_listing(
    staff_api_client, permission_manage_products, customer_type
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "input": {
            "variantChannelListing": graphene.Node.to_global_id(
                "ProductVariantChannelListing", -1
            ),
            "price": PRICE,
            "customerTypes": [
                graphene.Node.to_global_id("CustomerType", customer_type.pk)
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "variantChannelListing"
    assert error["code"] == VariantChannelListingPriceErrorCode.NOT_FOUND.name
    assert error["message"] == (
        f"Couldn't resolve to a node: {variables['input']['variantChannelListing']}"
    )
    assert VariantChannelListingPrice.objects.exists() is False


def test_rejects_a_price_with_too_many_decimal_places(
    staff_api_client, permission_manage_products, variant, customer_type
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": "7.123",
            "customerTypes": [
                graphene.Node.to_global_id("CustomerType", customer_type.pk)
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "price"
    assert error["code"] == VariantChannelListingPriceErrorCode.INVALID.name
    assert error["message"] == "Value cannot have more than 2 decimal places."
    assert VariantChannelListingPrice.objects.exists() is False


def test_rejects_the_row_above_the_listing_cap(
    staff_api_client,
    permission_manage_products,
    variant,
    variant_channel_listing_price,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            "customerTypes": [
                graphene.Node.to_global_id("CustomerType", customer_type.pk)
            ],
        }
    }

    # when
    with patch(
        "saleor.product.utils.scoped_price_rows.MAX_SCOPED_PRICES_PER_LISTING", 1
    ):
        response = staff_api_client.post_graphql(
            VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
        )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "variantChannelListing"
    assert error["code"] == VariantChannelListingPriceErrorCode.LIMIT_EXCEEDED.name
    assert error["message"] == (
        "A variant channel listing can hold at most 1 scoped prices."
    )
    assert VariantChannelListingPrice.objects.count() == 1


def test_rejects_too_many_condition_ids(
    staff_api_client, permission_manage_products, variant, customer_type
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            "customerTypes": [customer_type_id] * 101,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "customerTypes"
    assert error["code"] == VariantChannelListingPriceErrorCode.INVALID.name
    assert error["message"] == "Provide at most 100 items."
    assert VariantChannelListingPrice.objects.exists() is False


def test_deduplicates_condition_ids(
    staff_api_client, permission_manage_products, variant, customer_type
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)
    variables = {
        "input": {
            "variantChannelListing": _listing_id(variant),
            "price": PRICE,
            "customerTypes": [customer_type_id, customer_type_id],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_CREATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceCreate"]
    assert data["errors"] == []
    row = VariantChannelListingPrice.objects.get()
    assert list(row.customer_types.values_list("pk", flat=True)) == [customer_type.pk]
