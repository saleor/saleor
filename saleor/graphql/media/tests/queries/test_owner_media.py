import graphene
import pytest

from .....graphql.tests.utils import get_graphql_content
from .....product import MediaOwnerTypes, ProductMediaTypes
from .....product.media import OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE

OWNER_MEDIA_QUERIES = {
    MediaOwnerTypes.PRODUCT: """
        query ($id: ID!, $channel: String) {
            product(id: $id, channel: $channel) {
                media { __typename id alt mediaType ownerType ownerId }
            }
        }
    """,
    MediaOwnerTypes.CATEGORY: """
        query ($id: ID!) {
            category(id: $id) {
                media { __typename id alt mediaType ownerType ownerId }
            }
        }
    """,
    MediaOwnerTypes.COLLECTION: """
        query ($id: ID!, $channel: String) {
            collection(id: $id, channel: $channel) {
                media { __typename id alt mediaType ownerType ownerId }
            }
        }
    """,
    MediaOwnerTypes.PAGE: """
        query ($id: ID!) {
            page(id: $id) {
                media { __typename id alt mediaType ownerType ownerId }
            }
        }
    """,
}

OWNER_QUERY_FIELDS = {
    MediaOwnerTypes.PRODUCT: "product",
    MediaOwnerTypes.CATEGORY: "category",
    MediaOwnerTypes.COLLECTION: "collection",
    MediaOwnerTypes.PAGE: "page",
}

OWNER_GRAPHQL_TYPES = {
    MediaOwnerTypes.PRODUCT: "Product",
    MediaOwnerTypes.CATEGORY: "Category",
    MediaOwnerTypes.COLLECTION: "Collection",
    MediaOwnerTypes.PAGE: "Page",
}


@pytest.mark.parametrize("owner_type", MediaOwnerTypes.ALL)
def test_owner_media_resolves_to_the_owner_specific_type(
    owner_type,
    media_owner,
    staff_api_client,
    channel_USD,
    permission_manage_products,
    permission_manage_pages,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    alt = "an alt"
    media = media_owner.media.create(alt=alt, type=ProductMediaTypes.IMAGE)
    owner_id = graphene.Node.to_global_id(
        OWNER_GRAPHQL_TYPES[owner_type], media_owner.pk
    )
    variables = {"id": owner_id, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(OWNER_MEDIA_QUERIES[owner_type], variables)

    # then
    content = get_graphql_content(response)
    media_data = content["data"][OWNER_QUERY_FIELDS[owner_type]]["media"]
    assert len(media_data) == 1
    assert media_data[0]["__typename"] == OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type]
    assert media_data[0]["id"] == graphene.Node.to_global_id(
        OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type], media.pk
    )
    assert media_data[0]["alt"] == alt
    assert media_data[0]["mediaType"] == ProductMediaTypes.IMAGE
    assert media_data[0]["ownerType"] == owner_type.upper()
    assert media_data[0]["ownerId"] == owner_id


@pytest.mark.parametrize("owner_type", MediaOwnerTypes.ALL)
def test_owner_media_does_not_leak_other_owners_media(
    owner_type,
    media_owner,
    product,
    category,
    published_collection,
    page,
    staff_api_client,
    channel_USD,
    permission_manage_products,
    permission_manage_pages,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    for owner in (product, category, published_collection, page):
        owner.media.create(alt=f"{owner.__class__.__name__} media")
    variables = {
        "id": graphene.Node.to_global_id(
            OWNER_GRAPHQL_TYPES[owner_type], media_owner.pk
        ),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(OWNER_MEDIA_QUERIES[owner_type], variables)

    # then
    content = get_graphql_content(response)
    media_data = content["data"][OWNER_QUERY_FIELDS[owner_type]]["media"]
    assert len(media_data) == 1
    assert media_data[0]["alt"] == f"{media_owner.__class__.__name__} media"


PRODUCT_MEDIA_LEGACY_TYPE_QUERY = """
    query ($id: ID!, $channel: String) {
        product(id: $id, channel: $channel) {
            media { __typename type mediaType }
        }
    }
"""


@pytest.mark.parametrize(
    "media_type", [ProductMediaTypes.IMAGE, ProductMediaTypes.VIDEO]
)
def test_product_media_keeps_the_deprecated_type_field(
    media_type, product, staff_api_client, channel_USD, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product.media.create(alt="alt", type=media_type)
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(PRODUCT_MEDIA_LEGACY_TYPE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    media_data = content["data"]["product"]["media"]
    assert len(media_data) == 1
    assert media_data[0]["__typename"] == "ProductMedia"
    assert media_data[0]["type"] == media_type
    assert media_data[0]["mediaType"] == media_type


PAGE_MEDIA_INTERFACE_QUERY = """
    query ($id: ID!) {
        page(id: $id) {
            media {
                ... on Media { id alt mediaType ownerType }
                ... on PageMedia { metadata { key value } }
            }
        }
    }
"""


def test_media_interface_fragment_matches_page_media(
    page, staff_api_client, permission_manage_pages
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    media = page.media.create(alt="alt", metadata={"key": "value"})
    variables = {"id": graphene.Node.to_global_id("Page", page.pk)}

    # when
    response = staff_api_client.post_graphql(PAGE_MEDIA_INTERFACE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    media_data = content["data"]["page"]["media"]
    assert len(media_data) == 1
    assert media_data[0]["id"] == graphene.Node.to_global_id("PageMedia", media.pk)
    assert media_data[0]["ownerType"] == MediaOwnerTypes.PAGE.upper()
    assert media_data[0]["metadata"] == [{"key": "key", "value": "value"}]
