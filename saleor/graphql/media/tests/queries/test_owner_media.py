import json

import graphene
import pytest

from .....graphql.tests.utils import get_graphql_content
from .....media import MediaOwnerTypes
from .....media.models import ProductMedia
from .....media.utils import (
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)
from .....product import ProductMediaTypes
from .....product.error_codes import ProductErrorCode
from ..utils import NON_PRODUCT_OWNER_TYPES, create_colliding_media, owner_global_id

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
    owner_id = owner_global_id(owner_type, media_owner)
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
        "id": owner_global_id(owner_type, media_owner),
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


PRODUCT_MEDIA_DELETE_MUTATION = """
    mutation ($id: ID!) {
        productMediaDelete(id: $id) {
            media { id }
            errors { field code message }
        }
    }
"""


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_product_media_lookup_rejects_media_of_another_owner(
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
):
    """A non-product media PK typed as `ProductMedia` must not resolve to it.

    `MANAGE_PRODUCTS` must not reach a page's or a category's media, whether or
    not a product media happens to sit at the same pk.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = media_owner.media.create(alt="not a product media")
    mistyped_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_DELETE_MUTATION, {"id": mistyped_id}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaDelete"]
    assert data["media"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == ProductErrorCode.NOT_FOUND.name
    assert data["errors"][0]["field"] == "id"
    assert media_owner.media.filter(pk=media.pk).exists() is True


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_product_media_lookup_resolves_the_product_row_when_pks_collide(
    owner_type,
    media_owner,
    product,
    staff_api_client,
    permission_manage_products,
):
    """Each media model has its own pk sequence, so one pk names two real rows.

    The type name in the global ID must decide which table is read: the product
    media is deleted and the other owner's row at the same pk is left alone.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_media, other_media = create_colliding_media(
        owner_type, media_owner, product
    )
    assert product_media.pk == other_media.pk

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_DELETE_MUTATION,
        {"id": graphene.Node.to_global_id("ProductMedia", product_media.pk)},
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaDelete"]
    assert data["errors"] == []
    assert data["media"]["id"] == graphene.Node.to_global_id(
        "ProductMedia", product_media.pk
    )
    assert ProductMedia.objects.filter(pk=product_media.pk).exists() is False
    assert media_owner.media.filter(pk=other_media.pk).exists() is True


PRODUCT_MEDIA_LEGACY_FIELDS_QUERY = """
    query ($id: ID!, $channel: String) {
        product(id: $id, channel: $channel) {
            media {
                __typename
                id
                sortOrder
                alt
                type
                oembedData
                url(size: 0)
                productId
                metadata { key value }
            }
        }
    }
"""


def test_product_media_legacy_fields_are_unchanged(
    product, staff_api_client, channel_USD, permission_manage_products
):
    """Every field `ProductMedia` exposed before the generic gallery still resolves."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    alt = "an alt"
    external_url = "https://videos.example.com/watch"
    oembed_data = {"title": "a title"}
    media = product.media.create(
        alt=alt,
        type=ProductMediaTypes.VIDEO,
        external_url=external_url,
        oembed_data=oembed_data,
        sort_order=0,
        metadata={"key": "value"},
    )
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_LEGACY_FIELDS_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    media_data = content["data"]["product"]["media"]
    assert len(media_data) == 1
    # `oembedData` is a JSON string, so it is compared as a dict.
    assert json.loads(media_data[0].pop("oembedData")) == oembed_data
    assert media_data[0] == {
        "__typename": "ProductMedia",
        "id": graphene.Node.to_global_id("ProductMedia", media.pk),
        "sortOrder": media.sort_order,
        "alt": alt,
        "type": ProductMediaTypes.VIDEO,
        "url": external_url,
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "metadata": [{"key": "key", "value": "value"}],
    }


PRODUCT_MEDIA_UPDATE_MUTATION = """
    mutation ($id: ID!, $alt: String!) {
        productMediaUpdate(id: $id, input: {alt: $alt}) {
            media { id alt }
            errors { field code message }
        }
    }
"""


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_product_media_update_writes_the_product_row_when_pks_collide(
    owner_type,
    media_owner,
    product,
    staff_api_client,
    permission_manage_products,
):
    """The deprecated write path must pick its table by type name too."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_media, other_media = create_colliding_media(
        owner_type, media_owner, product
    )
    original_alt = other_media.alt
    new_alt = "written by the mutation"

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_UPDATE_MUTATION,
        {
            "id": graphene.Node.to_global_id("ProductMedia", product_media.pk),
            "alt": new_alt,
        },
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaUpdate"]
    assert data["errors"] == []
    assert data["media"]["alt"] == new_alt
    product_media.refresh_from_db(fields=("alt",))
    assert product_media.alt == new_alt
    other_media.refresh_from_db(fields=("alt",))
    assert other_media.alt == original_alt


def test_product_media_lookup_hides_an_owner_less_product_media(
    staff_api_client, permission_manage_products
):
    """Owner-less legacy rows are unreachable through `get_node`.

    They cannot satisfy the non-null `ownerId` on the `Media` interface, so every
    resolver filters them out. `productMediaBulkDelete` is the deliberate
    exception - see `test_deletes_an_owner_less_legacy_row` - and remains the
    only way to clear them.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = ProductMedia.objects.create(alt="owner-less legacy row")
    assert media.product_id is None
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_DELETE_MUTATION, {"id": media_id}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaDelete"]
    assert data["media"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == ProductErrorCode.NOT_FOUND.name
    assert data["errors"][0]["field"] == "id"
    assert ProductMedia.objects.filter(pk=media.pk).exists() is True
