from unittest.mock import patch

import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....media import MediaOwnerTypes
from .....media.error_codes import MediaUpdateErrorCode
from .....media.utils import (
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)
from ..utils import (
    MEDIA_AUTH_CASES,
    MEDIA_AUTH_PARAMS,
    NON_PRODUCT_OWNER_TYPES,
    create_colliding_media,
    media_global_id,
)

MEDIA_UPDATE_MUTATION = """
    mutation updateMedia($id: ID!, $alt: String) {
        mediaUpdate(id: $id, input: {alt: $alt}) {
            media {
                __typename
                id
                alt
            }
            errors {
                code
                field
                message
            }
        }
    }
"""

ALL_OWNER_TYPES = MediaOwnerTypes.ALL


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
@patch("saleor.plugins.manager.PluginsManager.media_updated")
def test_update_alt(
    mock_media_updated,
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
    permission_manage_pages,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    media = media_owner.media.create(alt="old alt")
    new_alt = "new alt"
    variables = {"id": media_global_id(owner_type, media), "alt": new_alt}

    # when
    response = staff_api_client.post_graphql(MEDIA_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaUpdate"]
    assert data["errors"] == []
    assert data["media"]["__typename"] == OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type]
    assert data["media"]["alt"] == new_alt

    media.refresh_from_db(fields=("alt",))
    assert media.alt == new_alt
    mock_media_updated.assert_called_once()


def test_update_rejects_alt_over_limit(staff_api_client, page, permission_manage_pages):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    original_alt = "keep me"
    media = page.media.create(alt=original_alt)
    variables = {
        "id": media_global_id(MediaOwnerTypes.PAGE, media),
        "alt": "a" * 251,
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaUpdateErrorCode.INVALID.name
    assert errors[0]["field"] == "input"
    assert errors[0]["message"] == "Alt field exceeds the character limit of 250."
    media.refresh_from_db(fields=("alt",))
    assert media.alt == original_alt


def test_update_rejects_id_of_a_different_owner_type(
    staff_api_client, page, permission_manage_products
):
    """A page media addressed as `ProductMedia` must not resolve.

    The client holds only `MANAGE_PRODUCTS`, so the type name in the ID is the
    single thing that could grant it reach into the page's gallery.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    original_alt = "keep me"
    media = page.media.create(alt=original_alt)
    # The row exists, but it is addressed as if it belonged to a product.
    media_id = media_global_id(MediaOwnerTypes.PRODUCT, media)
    variables = {"id": media_id, "alt": "new alt"}

    # when
    response = staff_api_client.post_graphql(MEDIA_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaUpdateErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "id"
    assert errors[0]["message"] == f"Couldn't resolve to an object: {media_id}"
    media.refresh_from_db(fields=("alt",))
    assert media.alt == original_alt


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_update_writes_the_product_row_when_pks_collide(
    owner_type,
    media_owner,
    product,
    staff_api_client,
    permission_manage_products,
):
    """One pk names a real row in every media table; the type name picks one.

    Without a colliding row the mistyped-ID test above can only prove the other
    table was empty, so this case asserts which of the two rows was written.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_media, other_media = create_colliding_media(
        owner_type, media_owner, product
    )
    original_alt = other_media.alt
    new_alt = "written by the mutation"
    media_id = media_global_id(MediaOwnerTypes.PRODUCT, product_media)

    # when
    response = staff_api_client.post_graphql(
        MEDIA_UPDATE_MUTATION, {"id": media_id, "alt": new_alt}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaUpdate"]
    assert data["errors"] == []
    assert data["media"]["id"] == media_id
    assert data["media"]["alt"] == new_alt
    product_media.refresh_from_db(fields=("alt",))
    assert product_media.alt == new_alt
    other_media.refresh_from_db(fields=("alt",))
    assert other_media.alt == original_alt


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_update_denies_a_colliding_pk_without_the_product_permission(
    owner_type,
    media_owner,
    product,
    staff_api_client,
    permission_manage_pages,
):
    """`MANAGE_PAGES` must not write a product media, even at a shared pk."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    product_media, other_media = create_colliding_media(
        owner_type, media_owner, product
    )
    original_product_alt = product_media.alt
    original_other_alt = other_media.alt

    # when
    response = staff_api_client.post_graphql(
        MEDIA_UPDATE_MUTATION,
        {
            "id": media_global_id(MediaOwnerTypes.PRODUCT, product_media),
            "alt": "should not be written",
        },
    )

    # then
    assert_no_permission(response)
    content = get_graphql_content_from_response(response)
    assert content["data"]["mediaUpdate"] is None
    product_media.refresh_from_db(fields=("alt",))
    assert product_media.alt == original_product_alt
    other_media.refresh_from_db(fields=("alt",))
    assert other_media.alt == original_other_alt


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
@pytest.mark.parametrize(MEDIA_AUTH_PARAMS, MEDIA_AUTH_CASES)
@patch("saleor.plugins.manager.PluginsManager.media_updated")
def test_update_authorization(
    mock_media_updated,
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    owner_type,
    media_owner,
    request,
    grant_media_permission,
):
    # given
    client = request.getfixturevalue(client_fixture)
    grant_media_permission(client, permission_fixture)

    original_alt = "keep me"
    media = media_owner.media.create(alt=original_alt)
    variables = {"id": media_global_id(owner_type, media), "alt": "new alt"}

    # when
    response = client.post_graphql(MEDIA_UPDATE_MUTATION, variables)

    # then
    if is_allowed:
        content = get_graphql_content(response)
        assert content["data"]["mediaUpdate"]["errors"] == []
        media.refresh_from_db(fields=("alt",))
        assert media.alt == "new alt"
        assert mock_media_updated.call_count == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["mediaUpdate"] is None
        media.refresh_from_db(fields=("alt",))
        assert media.alt == original_alt
        mock_media_updated.assert_not_called()


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
@patch("saleor.plugins.manager.PluginsManager.product_media_updated")
@patch("saleor.plugins.manager.PluginsManager.media_updated")
def test_update_also_fires_the_deprecated_product_media_event(
    mock_media_updated,
    mock_product_media_updated,
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
    permission_manage_pages,
):
    """`PRODUCT_MEDIA_UPDATED` must keep firing for product-owned media."""
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    media = media_owner.media.create(alt="old alt")
    variables = {"id": media_global_id(owner_type, media), "alt": "new alt"}

    # when
    response = staff_api_client.post_graphql(MEDIA_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["mediaUpdate"]["errors"] == []
    mock_media_updated.assert_called_once_with(media)
    if owner_type == MediaOwnerTypes.PRODUCT:
        mock_product_media_updated.assert_called_once_with(media)
    else:
        mock_product_media_updated.assert_not_called()
