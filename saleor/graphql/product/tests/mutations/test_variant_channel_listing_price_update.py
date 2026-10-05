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

VARIANT_CHANNEL_LISTING_PRICE_UPDATE_MUTATION = """
    mutation VariantChannelListingPriceUpdate(
        $id: ID!, $input: VariantChannelListingPriceUpdateInput!
    ) {
        variantChannelListingPriceUpdate(id: $id, input: $input) {
            variantChannelListingPrice {
                id
                price {
                    amount
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
                attributeValues
            }
        }
    }
"""

DAY = datetime.timedelta(days=1)


def _row_id(row):
    return graphene.Node.to_global_id("VariantChannelListingPrice", row.pk)


def _post(client, row, input_data):
    variables = {"id": _row_id(row), "input": input_data}
    response = client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_UPDATE_MUTATION, variables
    )
    return get_graphql_content(response)["data"]["variantChannelListingPriceUpdate"]


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
    variant_channel_listing_price_for_customer_type,
):
    # given
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        permission = request.getfixturevalue(permission_fixture)
        if client.app:
            client.app.permissions.add(permission)
        else:
            client.user.user_permissions.add(permission)
    row = variant_channel_listing_price_for_customer_type
    old_price = row.price_amount
    new_price = Decimal("5.50")
    variables = {"id": _row_id(row), "input": {"price": str(new_price)}}

    # when
    response = client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_UPDATE_MUTATION, variables
    )

    # then
    row.refresh_from_db(fields=["price_amount"])
    if is_allowed:
        data = get_graphql_content(response)["data"]["variantChannelListingPriceUpdate"]
        assert data["errors"] == []
        assert row.price_amount == new_price
        assert product_variant_updated_mock.call_count == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["variantChannelListingPriceUpdate"] is None
        assert row.price_amount == old_price
        assert product_variant_updated_mock.call_count == 0


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_replaces_the_given_dimensions_and_keeps_the_others(
    product_variant_updated_mock,
    staff_api_client,
    permission_manage_products,
    variant,
    variant_channel_listing_price_for_customer_type,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    row = variant_channel_listing_price_for_customer_type
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )
    gold_value_id = graphene.Node.to_global_id("AttributeValue", gold_value.pk)
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)
    valid_to = (timezone.now() + DAY).replace(microsecond=0)
    new_price = Decimal("6.25")

    # when
    data = _post(
        staff_api_client,
        row,
        {
            "price": str(new_price),
            "attributeValues": [gold_value_id],
            "validTo": valid_to.isoformat(),
        },
    )

    # then
    assert data["errors"] == []
    row.refresh_from_db()
    assert row.price_amount == new_price
    assert list(row.customer_types.values_list("pk", flat=True)) == [customer_type.pk]
    assert list(row.attribute_values.values_list("pk", flat=True)) == [gold_value.pk]
    assert row.valid_from is None
    assert row.valid_to == valid_to
    price_data = data["variantChannelListingPrice"]
    assert price_data["price"]["amount"] == float(new_price)
    assert price_data["customerTypes"] == [{"id": customer_type_id}]
    assert price_data["attributeValues"] == [{"id": gold_value_id}]
    assert price_data["validFrom"] is None
    assert price_data["validTo"] == valid_to.isoformat()
    product_variant_updated_mock.assert_called_once()
    assert product_variant_updated_mock.call_args.args[0] == variant


@pytest.mark.parametrize(
    ("_case", "customer_types_input"),
    [
        ("null_clears", None),
        ("empty_list_clears", []),
    ],
)
def test_clears_a_dimension(
    _case,
    customer_types_input,
    staff_api_client,
    permission_manage_products,
    variant_channel_listing_price_for_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    row = variant_channel_listing_price_for_customer_type
    valid_from = (timezone.now() - DAY).replace(microsecond=0)

    # when
    data = _post(
        staff_api_client,
        row,
        {"customerTypes": customer_types_input, "validFrom": valid_from.isoformat()},
    )

    # then
    assert data["errors"] == []
    assert row.customer_types.exists() is False
    row.refresh_from_db(fields=["valid_from"])
    assert row.valid_from == valid_from
    assert data["variantChannelListingPrice"]["customerTypes"] == []


def test_rejects_clearing_the_last_condition(
    staff_api_client,
    permission_manage_products,
    variant_channel_listing_price_for_customer_type,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    row = variant_channel_listing_price_for_customer_type

    # when
    data = _post(staff_api_client, row, {"customerTypes": []})

    # then
    assert data["variantChannelListingPrice"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] is None
    assert error["code"] == VariantChannelListingPriceErrorCode.REQUIRED.name
    assert error["message"] == (
        "A scoped price needs at least one customer type, one attribute value or "
        "a validity window."
    )
    assert list(row.customer_types.values_list("pk", flat=True)) == [customer_type.pk]


def test_rejects_a_window_that_does_not_end_after_it_starts(
    staff_api_client, permission_manage_products, variant_channel_listing_price
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    row = variant_channel_listing_price
    old_valid_to = row.valid_to

    # when
    data = _post(staff_api_client, row, {"validTo": row.valid_from.isoformat()})

    # then
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "validTo"
    assert error["code"] == VariantChannelListingPriceErrorCode.INVALID.name
    assert error["message"] == (
        "The end of the validity window must be after its start."
    )
    row.refresh_from_db(fields=["valid_to"])
    assert row.valid_to == old_valid_to


def test_rejects_values_of_non_customer_attributes(
    staff_api_client,
    permission_manage_products,
    variant_channel_listing_price_for_customer_type,
    color_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    row = variant_channel_listing_price_for_customer_type
    color_value_id = graphene.Node.to_global_id(
        "AttributeValue", color_attribute.values.first().pk
    )

    # when
    data = _post(staff_api_client, row, {"attributeValues": [color_value_id]})

    # then
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributeValues"
    assert error["code"] == VariantChannelListingPriceErrorCode.INVALID.name
    assert error["message"] == (
        "Only values of customer attributes with a fixed set of choices can scope "
        "a price."
    )
    assert error["attributeValues"] == [color_value_id]
    assert row.attribute_values.exists() is False


def test_withdraws_an_applied_row_moved_to_the_future(
    staff_api_client,
    permission_manage_products,
    variant,
    product,
    variant_channel_listing_price,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    row = variant_channel_listing_price
    row.is_applied = True
    row.save(update_fields=["is_applied"])
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    assert product_listing.discounted_price_dirty is False
    valid_from = (timezone.now() + DAY).replace(microsecond=0)

    # when
    data = _post(
        staff_api_client, row, {"validFrom": valid_from.isoformat(), "validTo": None}
    )

    # then
    assert data["errors"] == []
    row.refresh_from_db(fields=["is_applied", "valid_from", "valid_to"])
    assert row.is_applied is False
    assert row.valid_from == valid_from
    assert row.valid_to is None
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True


def test_rejects_an_unknown_row(staff_api_client, permission_manage_products):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("VariantChannelListingPrice", -1),
        "input": {"price": "1.00"},
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_UPDATE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceUpdate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == VariantChannelListingPriceErrorCode.NOT_FOUND.name
    assert error["message"] == f"Couldn't resolve to a node: {variables['id']}"
    assert VariantChannelListingPrice.objects.exists() is False


def test_rejects_a_null_price(
    staff_api_client,
    permission_manage_products,
    variant_channel_listing_price_for_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    row = variant_channel_listing_price_for_customer_type
    old_price = row.price_amount

    # when
    data = _post(staff_api_client, row, {"price": None})

    # then
    assert data["variantChannelListingPrice"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "price"
    assert error["code"] == VariantChannelListingPriceErrorCode.REQUIRED.name
    assert error["message"] == "The price cannot be null. Leave it out to keep it."
    row.refresh_from_db(fields=["price_amount"])
    assert row.price_amount == old_price
