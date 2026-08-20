from unittest.mock import patch

import graphene

from .....graphql.tests.utils import get_graphql_content
from .....product import MEDIA_TAGS_LIMIT
from .....product.error_codes import ProductErrorCode

PRODUCT_MEDIA_UPDATE_QUERY = """
    mutation updateProductMedia($mediaId: ID!, $alt: String) {
        productMediaUpdate(id: $mediaId, input: {alt: $alt}) {
            media {
                alt
                tags
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


PRODUCT_MEDIA_UPDATE_TAGS_QUERY = """
    mutation updateProductMedia($mediaId: ID!, $tags: [String!]) {
        productMediaUpdate(id: $mediaId, input: {tags: $tags}) {
            media {
                alt
                tags
            }
            errors {
                code
                field
                message
            }
        }
    }
    """


def test_update_tags_replaces_existing_tags(
    staff_api_client, product_with_image, permission_manage_products
):
    # given
    media_obj = product_with_image.media.get()
    media_obj.tags = ["content", "old"]
    media_obj.save(update_fields=["tags"])
    variables = {
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
        "tags": [" Gallery ", "gallery", "HERO"],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_TAGS_QUERY,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["productMediaUpdate"]["errors"]
    media_obj.refresh_from_db(fields=("tags",))
    assert media_obj.tags == ["gallery", "hero"]
    assert content["data"]["productMediaUpdate"]["media"]["tags"] == ["gallery", "hero"]


def test_update_with_empty_tags_clears_them(
    staff_api_client, product_with_image, permission_manage_products
):
    # given
    media_obj = product_with_image.media.get()
    media_obj.tags = ["content"]
    media_obj.save(update_fields=["tags"])
    variables = {
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
        "tags": [],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_TAGS_QUERY,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["productMediaUpdate"]["media"]["tags"] == []
    media_obj.refresh_from_db(fields=("tags",))
    assert media_obj.tags == []


def test_update_without_tags_keeps_them(
    staff_api_client, product_with_image, permission_manage_products
):
    # given
    tags = ["content"]
    media_obj = product_with_image.media.get()
    media_obj.tags = tags
    media_obj.save(update_fields=["tags"])
    alt = "new alt"
    variables = {
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
        "alt": alt,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_QUERY,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["productMediaUpdate"]["media"]["alt"] == alt
    media_obj.refresh_from_db(fields=("alt", "tags"))
    assert media_obj.tags == tags


def test_update_with_too_many_tags(
    staff_api_client, product_with_image, permission_manage_products
):
    # given
    tags = ["content"]
    media_obj = product_with_image.media.get()
    media_obj.tags = tags
    media_obj.save(update_fields=["tags"])
    variables = {
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
        "tags": [f"tag-{index}" for index in range(MEDIA_TAGS_LIMIT + 1)],
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_TAGS_QUERY,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productMediaUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "tags"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == f"Number of tags exceeds the limit of {MEDIA_TAGS_LIMIT}."
    )
    media_obj.refresh_from_db(fields=("tags",))
    assert media_obj.tags == tags
