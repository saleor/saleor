from unittest.mock import patch

import graphene
import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....product import MediaOwnerTypes
from .....product.error_codes import MediaUpdateErrorCode
from .....product.media import (
    MEDIA_OWNER_PERMISSION_MAP,
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
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


def _media_global_id(owner_type, media):
    return graphene.Node.to_global_id(
        OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type], media.pk
    )


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
    variables = {"id": _media_global_id(owner_type, media), "alt": new_alt}

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
        "id": _media_global_id(MediaOwnerTypes.PAGE, media),
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
    media_id = _media_global_id(MediaOwnerTypes.PRODUCT, media)
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
@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", None, False),
        ("Unprivileged user should be rejected", "user_api_client", None, False),
        (
            "Staff user without the permission should be rejected",
            "staff_api_client",
            None,
            False,
        ),
        (
            "Staff user with the owner's permission should be allowed",
            "staff_api_client",
            "owner",
            True,
        ),
        (
            "Staff user with the other domain's permission should be rejected",
            "staff_api_client",
            "other",
            False,
        ),
    ],
)
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
):
    # given
    client = request.getfixturevalue(client_fixture)
    owner_permission = MEDIA_OWNER_PERMISSION_MAP[owner_type]
    other_permission = next(
        permission
        for permission in MEDIA_OWNER_PERMISSION_MAP.values()
        if permission != owner_permission
    )
    if permission_fixture:
        permission = {"owner": owner_permission, "other": other_permission}[
            permission_fixture
        ]
        codename = permission.value.split(".")[1]
        perm_object = request.getfixturevalue(f"permission_{codename}")
        if client.user:
            client.user.user_permissions.add(perm_object)

    original_alt = "keep me"
    media = media_owner.media.create(alt=original_alt)
    variables = {"id": _media_global_id(owner_type, media), "alt": "new alt"}

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
