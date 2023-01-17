from unittest.mock import patch

import before_after
import graphene
import pytest
from django.db import transaction

from .....graphql.tests.utils import get_graphql_content
from .....product.error_codes import ProductErrorCode

PRODUCT_MEDIA_REORDER = """
    mutation reorderMedia($product_id: ID!, $media_ids: [ID!]!) {
        productMediaReorder(productId: $product_id, mediaIds: $media_ids) {
            product {
                id
            }
            errors{
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_reorder_media(
    product_updated_mock,
    staff_api_client,
    product_with_images,
    permission_manage_products,
):
    query = PRODUCT_MEDIA_REORDER
    product = product_with_images
    media = product.media.all()
    media_0 = media[0]
    media_1 = media[1]
    media_0_id = graphene.Node.to_global_id("ProductMedia", media_0.id)
    media_1_id = graphene.Node.to_global_id("ProductMedia", media_1.id)
    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {"product_id": product_id, "media_ids": [media_1_id, media_0_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    # Check if order has been changed
    product.refresh_from_db()
    reordered_media = product.media.all()
    reordered_media_0 = reordered_media[0]
    reordered_media_1 = reordered_media[1]

    assert media_0.id == reordered_media_1.id
    assert media_1.id == reordered_media_0.id
    product_updated_mock.assert_called_once_with(product)


def test_reorder_media_not_enough_ids(
    staff_api_client,
    product_with_images,
    permission_manage_products,
):
    query = PRODUCT_MEDIA_REORDER
    product = product_with_images
    media = product.media.all()
    media_0 = media[0]
    media_1 = media[1]
    product_id = graphene.Node.to_global_id("Product", product.id)
    media_1_id = graphene.Node.to_global_id("ProductMedia", media_1.id)

    variables = {"product_id": product_id, "media_ids": [media_1_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # Check if order has not been changed
    product.refresh_from_db()
    reordered_media = product.media.all()
    reordered_media_0 = reordered_media[0]
    reordered_media_1 = reordered_media[1]

    assert media_0.id == reordered_media_0.id
    assert media_1.id == reordered_media_1.id
    assert (
        content["data"]["productMediaReorder"]["errors"][0]["code"]
        == ProductErrorCode.INVALID.name
    )


@pytest.mark.django_db(transaction=True)
def test_reorder_not_existing_media(
    staff_api_client,
    product_with_images,
    permission_manage_products,
):
    query = PRODUCT_MEDIA_REORDER
    product = product_with_images
    media = product.media.all()
    media_0 = media[0]
    media_1 = media[1]
    media_0_id = graphene.Node.to_global_id("ProductMedia", media_0.id)
    media_1_id = graphene.Node.to_global_id("ProductMedia", media_1.id)
    product_id = graphene.Node.to_global_id("Product", product.id)

    def delete_media(*args, **kwargs):
        with transaction.atomic():
            media.delete()

    with before_after.before(
        "saleor.graphql.product.mutations.product.product_media_reorder"
        ".update_ordered_media",
        delete_media,
    ):
        variables = {"product_id": product_id, "media_ids": [media_1_id, media_0_id]}
        response = staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_products]
        )
    response = get_graphql_content(response, ignore_errors=True)
    assert (
        response["data"]["productMediaReorder"]["errors"][0]["code"]
        == ProductErrorCode.NOT_FOUND.name
    )
