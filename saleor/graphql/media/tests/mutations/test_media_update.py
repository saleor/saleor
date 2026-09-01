from unittest.mock import patch

import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....product import MediaOwnerTypes
from .....product.error_codes import MediaUpdateErrorCode
from .....product.media import (
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)
from ..utils import (
    MEDIA_AUTH_CASES,
    MEDIA_AUTH_PARAMS,
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
    staff_api_client, page, permission_manage_pages, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_pages, permission_manage_products
    )
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
