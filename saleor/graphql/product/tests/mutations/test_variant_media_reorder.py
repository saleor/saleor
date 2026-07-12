from unittest.mock import patch

import pytest
from django.db import transaction
from graphql_relay import to_global_id

from .....graphql.tests.utils import get_graphql_content
from .....product.error_codes import VariantMediaReorderErrorCode
from .....product.models import VariantMedia
from .....tests import race_condition

VARIANT_MEDIA_REORDER = """
    mutation reorderVariantMedia($variantId: ID!, $mediaIds: [ID!]!) {
        variantMediaReorder(variantId: $variantId, mediaIds: $mediaIds) {
            productVariant {
                id
            }
            media {
                id
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
def test_reorder_variant_media(
    product_variant_updated_mock,
    staff_api_client,
    product_with_image_list,
    permission_manage_products,
):
    # given
    query = VARIANT_MEDIA_REORDER
    product = product_with_image_list
    variant = product.variants.first()
    media_0, media_1 = product.media.all()
    VariantMedia.objects.create(variant=variant, media=media_0)
    VariantMedia.objects.create(variant=variant, media=media_1)
    variant_id = to_global_id("ProductVariant", variant.pk)
    media_0_id = to_global_id("ProductMedia", media_0.pk)
    media_1_id = to_global_id("ProductMedia", media_1.pk)

    variables = {"variantId": variant_id, "mediaIds": [media_1_id, media_0_id]}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    # then
    reordered_variant_media = variant.variant_media.order_by("sort_order")
    assert reordered_variant_media[0].media_id == media_1.id
    assert reordered_variant_media[1].media_id == media_0.id
    # product-level media order must stay independent from the variant order
    reordered_product_media = product.media.all()
    assert reordered_product_media[0].id == media_0.id
    assert reordered_product_media[1].id == media_1.id
    product_variant_updated_mock.assert_called_once_with(variant)


def test_reorder_variant_media_not_enough_ids(
    staff_api_client,
    product_with_image_list,
    permission_manage_products,
):
    # given
    query = VARIANT_MEDIA_REORDER
    product = product_with_image_list
    variant = product.variants.first()
    media_0, media_1 = product.media.all()
    VariantMedia.objects.create(variant=variant, media=media_0)
    VariantMedia.objects.create(variant=variant, media=media_1)
    variant_id = to_global_id("ProductVariant", variant.pk)
    media_1_id = to_global_id("ProductMedia", media_1.pk)

    variables = {"variantId": variant_id, "mediaIds": [media_1_id]}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["variantMediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == VariantMediaReorderErrorCode.INVALID.name
    reordered_variant_media = variant.variant_media.order_by("sort_order")
    assert reordered_variant_media[0].media_id == media_0.id
    assert reordered_variant_media[1].media_id == media_1.id


def test_reorder_variant_media_too_many_ids(
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    # given
    query = VARIANT_MEDIA_REORDER
    product = product_with_image
    variant = product.variants.first()
    media = product.media.first()
    VariantMedia.objects.create(variant=variant, media=media)
    variant_id = to_global_id("ProductVariant", variant.pk)
    media_id = to_global_id("ProductMedia", media.pk)

    variables = {"variantId": variant_id, "mediaIds": [media_id] * 101}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["variantMediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == VariantMediaReorderErrorCode.INVALID.name


def test_reorder_variant_media_not_assigned_to_variant(
    staff_api_client,
    product_with_image_list,
    permission_manage_products,
):
    # given
    query = VARIANT_MEDIA_REORDER
    product = product_with_image_list
    variant = product.variants.first()
    media_0, media_1 = product.media.all()
    # only media_0 is assigned to the variant, so the submitted count (1) matches,
    # but media_1 (submitted below) belongs to the product and not to this variant
    VariantMedia.objects.create(variant=variant, media=media_0)
    variant_id = to_global_id("ProductVariant", variant.pk)
    media_1_id = to_global_id("ProductMedia", media_1.pk)

    variables = {"variantId": variant_id, "mediaIds": [media_1_id]}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["variantMediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == VariantMediaReorderErrorCode.NOT_FOUND.name


@pytest.mark.django_db(transaction=True)
def test_reorder_variant_media_race_condition(
    staff_api_client,
    product_with_image_list,
    permission_manage_products,
):
    # given
    query = VARIANT_MEDIA_REORDER
    product = product_with_image_list
    variant = product.variants.first()
    media_0, media_1 = product.media.all()
    variant_media_0 = VariantMedia.objects.create(variant=variant, media=media_0)
    VariantMedia.objects.create(variant=variant, media=media_1)
    variant_id = to_global_id("ProductVariant", variant.pk)
    media_0_id = to_global_id("ProductMedia", media_0.pk)
    media_1_id = to_global_id("ProductMedia", media_1.pk)

    def delete_variant_media(*args, **kwargs):
        with transaction.atomic():
            variant_media_0.delete()

    # when
    with race_condition.RunBefore(
        "saleor.graphql.product.mutations.product_variant.variant_media_reorder"
        ".update_ordered_variant_media",
        delete_variant_media,
    ):
        variables = {"variantId": variant_id, "mediaIds": [media_1_id, media_0_id]}
        response = staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_products]
        )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["data"]["variantMediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == VariantMediaReorderErrorCode.NOT_FOUND.name
