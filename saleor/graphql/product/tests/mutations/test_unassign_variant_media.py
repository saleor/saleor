from graphql_relay import to_global_id

from .....graphql.tests.utils import get_graphql_content
from .....product.models import ProductMedia

UNASSIGN_VARIANT_IMAGE_QUERY = """
    mutation unassignVariantMediaMutation($variantId: ID!, $mediaId: ID!) {
        variantMediaUnassign(variantId: $variantId, mediaId: $mediaId) {
            errors {
                field
                message
            }
            productVariant {
                id
            }
        }
    }
"""


def test_unassign_variant_media_image(
    staff_api_client, product_with_image, permission_manage_products
):
    query = UNASSIGN_VARIANT_IMAGE_QUERY

    media = product_with_image.media.first()
    variant = product_with_image.variants.first()
    variant.variant_media.create(media=media)

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.media.count() == 0


def test_unassign_not_assigned_variant_media_image(
    staff_api_client, product_with_image, permission_manage_products
):
    query = UNASSIGN_VARIANT_IMAGE_QUERY
    variant = product_with_image.variants.first()
    media = ProductMedia.objects.create(product=product_with_image)
    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["variantMediaUnassign"]["errors"][0]["field"] == ("mediaId")
