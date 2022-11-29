from graphql_relay import to_global_id

from .....product.error_codes import ProductErrorCode
from .....product.models import ProductMedia
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

ASSIGN_VARIANT_QUERY = """
    mutation assignVariantMediaMutation($variantId: ID!, $mediaId: ID!) {
        variantMediaAssign(variantId: $variantId, mediaId: $mediaId) {
            errors {
                field
                message
                code
            }
            productVariant {
                id
            }
        }
    }
"""


def test_assign_variant_media(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    media_obj = product_with_image.media.first()

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media_obj.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.media.first() == media_obj


def test_assign_variant_media_second_time(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    # given
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    media_obj = product_with_image.media.first()
    media_obj.variant_media.create(variant=variant)

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media_obj.pk),
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content_from_response(response)["data"]["variantMediaAssign"]
    assert "errors" in content
    errors = content["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.MEDIA_ALREADY_ASSIGNED.name


def test_assign_variant_media_from_different_product(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    product_with_image.pk = None
    product_with_image.slug = "product-with-image"
    product_with_image.save()

    media_obj_2 = ProductMedia.objects.create(product=product_with_image)
    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media_obj_2.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["variantMediaAssign"]["errors"][0]["field"] == "mediaId"

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)
