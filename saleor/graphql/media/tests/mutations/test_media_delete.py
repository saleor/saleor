from unittest.mock import patch

import graphene
import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....product import MediaOwnerTypes
from .....product.error_codes import MediaDeleteErrorCode
from .....product.media import (
    MEDIA_OWNER_PERMISSION_MAP,
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)
from .....product.models import ProductMedia

MEDIA_DELETE_MUTATION = """
    mutation deleteMedia($id: ID!) {
        mediaDelete(id: $id) {
            media {
                __typename
                id
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
@patch("saleor.plugins.manager.PluginsManager.media_deleted")
def test_delete(
    mock_media_deleted,
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
    media = media_owner.media.create(alt="alt")
    media_id = _media_global_id(owner_type, media)
    variables = {"id": media_id}

    # when
    response = staff_api_client.post_graphql(MEDIA_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaDelete"]
    assert data["errors"] == []
    assert data["media"]["id"] == media_id
    assert data["media"]["__typename"] == OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE[owner_type]
    assert ProductMedia.objects.filter(pk=media.pk).exists() is False
    mock_media_deleted.assert_called_once()


def test_delete_rejects_unknown_media(staff_api_client, permission_manage_pages):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    media_id = graphene.Node.to_global_id("PageMedia", -1)

    # when
    response = staff_api_client.post_graphql(MEDIA_DELETE_MUTATION, {"id": media_id})

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaDelete"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaDeleteErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "id"
    assert errors[0]["message"] == f"Couldn't resolve to an object: {media_id}"


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
@patch("saleor.plugins.manager.PluginsManager.media_deleted")
def test_delete_authorization(
    mock_media_deleted,
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

    media = media_owner.media.create(alt="alt")
    variables = {"id": _media_global_id(owner_type, media)}

    # when
    response = client.post_graphql(MEDIA_DELETE_MUTATION, variables)

    # then
    if is_allowed:
        content = get_graphql_content(response)
        assert content["data"]["mediaDelete"]["errors"] == []
        assert ProductMedia.objects.filter(pk=media.pk).exists() is False
        assert mock_media_deleted.call_count == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["mediaDelete"] is None
        assert ProductMedia.objects.filter(pk=media.pk).exists() is True
        mock_media_deleted.assert_not_called()
