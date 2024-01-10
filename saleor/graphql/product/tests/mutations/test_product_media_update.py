from unittest.mock import patch

import graphene

from .....graphql.tests.utils import get_graphql_content
from .....product.error_codes import ProductErrorCode

PRODUCT_MEDIA_UPDATE_QUERY = """
    mutation updateProductMedia($mediaId: ID!, $alt: String) {
        productMediaUpdate(id: $mediaId, input: {alt: $alt}) {
            media {
                alt
            }
            errors {
                code
                field
            }
        }
    }
    """


@patch("saleor.plugins.manager.PluginsManager.product_media_updated")
@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_image_update_mutation(
    product_updated_mock,
    product_media_update_mock,
    monkeypatch,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    # given

    media_obj = product_with_image.media.first()
    alt = "damage alt"
    assert media_obj.alt != alt
    variables = {
        "alt": alt,
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_QUERY, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    media_obj.refresh_from_db()
    assert content["data"]["productMediaUpdate"]["media"]["alt"] == alt
    assert media_obj.alt == alt

    product_updated_mock.assert_called_once_with(product_with_image)
    product_media_update_mock.assert_called_once_with(media_obj)


def test_product_image_update_mutation_alt_over_char_limit(
    monkeypatch,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    # given
    media_obj = product_with_image.media.first()
    alt_over_250 = """
    Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
    Aenean commodo ligula eget dolor. Aenean massa. Cym sociis natoque penatibus et
    magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies
    nec, pellentesque eu, pretium quis, sem.
    """
    variables = {
        "alt": alt_over_250,
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_QUERY, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
