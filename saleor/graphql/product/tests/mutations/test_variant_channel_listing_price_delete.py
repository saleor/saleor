from unittest.mock import patch

import graphene
import pytest

from .....product.error_codes import VariantChannelListingPriceErrorCode
from .....product.models import (
    VariantChannelListingPrice,
    VariantChannelListingPriceCustomerType,
)
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

VARIANT_CHANNEL_LISTING_PRICE_DELETE_MUTATION = """
    mutation VariantChannelListingPriceDelete($id: ID!) {
        variantChannelListingPriceDelete(id: $id) {
            variantChannelListingPrice {
                id
                price {
                    amount
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def _row_id(row):
    return graphene.Node.to_global_id("VariantChannelListingPrice", row.pk)


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
    variables = {"id": _row_id(row)}

    # when
    response = client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_DELETE_MUTATION, variables
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["variantChannelListingPriceDelete"]
        assert data["errors"] == []
        assert VariantChannelListingPrice.objects.filter(pk=row.pk).exists() is False
        assert product_variant_updated_mock.call_count == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["variantChannelListingPriceDelete"] is None
        assert VariantChannelListingPrice.objects.filter(pk=row.pk).exists() is True
        assert product_variant_updated_mock.call_count == 0


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_removes_the_row_and_marks_the_product_dirty(
    product_variant_updated_mock,
    staff_api_client,
    permission_manage_products,
    variant,
    product,
    variant_channel_listing_price_for_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    row = variant_channel_listing_price_for_customer_type
    listing = variant.channel_listings.get()
    product_listing = product.channel_listings.get(channel=listing.channel)
    assert product_listing.discounted_price_dirty is False
    variables = {"id": _row_id(row)}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_DELETE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceDelete"]
    assert data["errors"] == []
    assert data["variantChannelListingPrice"] == {
        "id": _row_id(row),
        "price": {"amount": float(row.price_amount)},
    }
    assert VariantChannelListingPrice.objects.filter(pk=row.pk).exists() is False
    assert (
        VariantChannelListingPriceCustomerType.objects.filter(
            listing_price_id=row.pk
        ).exists()
        is False
    )
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True
    product_variant_updated_mock.assert_called_once()
    assert product_variant_updated_mock.call_args.args[0] == variant


def test_rejects_an_unknown_row(staff_api_client, permission_manage_products):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {"id": graphene.Node.to_global_id("VariantChannelListingPrice", -1)}

    # when
    response = staff_api_client.post_graphql(
        VARIANT_CHANNEL_LISTING_PRICE_DELETE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["variantChannelListingPriceDelete"]
    assert data["variantChannelListingPrice"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == VariantChannelListingPriceErrorCode.NOT_FOUND.name
    assert error["message"] == f"Couldn't resolve to a node: {variables['id']}"
