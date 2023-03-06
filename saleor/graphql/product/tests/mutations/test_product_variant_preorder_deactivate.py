from unittest.mock import patch

import graphene

from .....core.exceptions import PreorderAllocationError
from .....product.error_codes import ProductErrorCode
from .....tests.utils import flush_post_commit_hooks
from .....warehouse.models import Allocation
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_VARIANT_DEACTIVATE_PREORDER = """
    mutation deactivatePreorder (
        $id: ID!
        ) {
            productVariantPreorderDeactivate(id: $id) {
                productVariant {
                    sku
                    preorder {
                        globalThreshold
                        endDate
                    }
                    stocks {
                        quantityAllocated
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


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
def test_product_variant_deactivate_preorder(
    updated_webhook_mock,
    staff_api_client,
    permission_manage_products,
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    allocations_before = Allocation.objects.filter(
        stock__product_variant_id=variant.pk
    ).count()

    response = staff_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
        permissions=[permission_manage_products],
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantPreorderDeactivate"]["productVariant"]

    assert not data["preorder"]
    assert data["stocks"][0]["quantityAllocated"] > allocations_before

    updated_webhook_mock.assert_called_once_with(variant)


def test_product_variant_deactivate_preorder_non_preorder_variant(
    staff_api_client,
    permission_manage_products,
    variant,
):
    assert variant.is_preorder is False
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = staff_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    error = content["data"]["productVariantPreorderDeactivate"]["errors"][0]

    assert error["field"] == "id"
    assert error["code"] == ProductErrorCode.INVALID.name


@patch(
    "saleor.graphql.product.mutations.product_variant"
    ".product_variant_preorder_deactivate.deactivate_preorder_for_variant"
)
def test_product_variant_deactivate_preorder_cannot_deactivate(
    mock_deactivate_preorder_for_variant,
    staff_api_client,
    permission_manage_products,
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    mock_deactivate_preorder_for_variant.side_effect = PreorderAllocationError(
        preorder_allocation.order_line
    )

    response = staff_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    error = content["data"]["productVariantPreorderDeactivate"]["errors"][0]

    assert error["field"] is None
    assert error["code"] == ProductErrorCode.PREORDER_VARIANT_CANNOT_BE_DEACTIVATED.name


def test_product_variant_deactivate_preorder_as_customer(
    user_api_client,
    preorder_variant_global_and_channel_threshold,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = user_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
    )

    assert_no_permission(response)


def test_product_variant_deactivate_preorder_as_anonymous(
    api_client,
    preorder_variant_global_and_channel_threshold,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
    )

    assert_no_permission(response)


def test_product_variant_deactivate_preorder_as_app_with_permission(
    app_api_client,
    preorder_variant_global_and_channel_threshold,
    permission_manage_products,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = app_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
        permissions=[permission_manage_products],
    )

    content = get_graphql_content(response)
    data = content["data"]["productVariantPreorderDeactivate"]["productVariant"]
    assert not data["preorder"]


def test_product_variant_deactivate_preorder_as_app(
    app_api_client,
    preorder_variant_global_and_channel_threshold,
):
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    response = app_api_client.post_graphql(
        QUERY_VARIANT_DEACTIVATE_PREORDER,
        {"id": variant_id},
    )

    assert_no_permission(response)
