from unittest.mock import patch

import graphene
import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....product import MediaOwnerTypes
from .....product.error_codes import MediaReorderErrorCode
from .....product.media import (
    MEDIA_OWNER_PERMISSION_MAP,
    OWNER_TYPE_TO_GRAPHQL_TYPE,
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)

MEDIA_REORDER_MUTATION = """
    mutation reorderMedia($id: ID!, $mediaIds: [ID!]!) {
        mediaReorder(id: $id, mediaIds: $mediaIds) {
            media {
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


def _owner_global_id(owner_type, owner):
    return graphene.Node.to_global_id(OWNER_TYPE_TO_GRAPHQL_TYPE[owner_type], owner.pk)


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
def test_reorder(
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
    first = media_owner.media.create(alt="first", sort_order=0)
    second = media_owner.media.create(alt="second", sort_order=1)
    variables = {
        "id": _owner_global_id(owner_type, media_owner),
        "mediaIds": [
            _media_global_id(owner_type, second),
            _media_global_id(owner_type, first),
        ],
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_REORDER_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaReorder"]
    assert data["errors"] == []
    assert [item["id"] for item in data["media"]] == variables["mediaIds"]

    first.refresh_from_db(fields=("sort_order",))
    second.refresh_from_db(fields=("sort_order",))
    assert second.sort_order == 0
    assert first.sort_order == 1


def test_reorder_rejects_media_of_another_owner(
    staff_api_client, page, page_list, permission_manage_pages
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    other_page = page_list[0]
    own_media = page.media.create(alt="own", sort_order=0)
    foreign_media = other_page.media.create(alt="foreign", sort_order=0)
    foreign_media_id = _media_global_id(MediaOwnerTypes.PAGE, foreign_media)
    variables = {
        "id": _owner_global_id(MediaOwnerTypes.PAGE, page),
        "mediaIds": [foreign_media_id],
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_REORDER_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaReorderErrorCode.NOT_MEDIA_OWNER.name
    assert errors[0]["field"] == "mediaIds"
    assert errors[0]["message"] == (
        f"Media {foreign_media_id} does not belong to this entity."
    )
    own_media.refresh_from_db(fields=("sort_order",))
    assert own_media.sort_order == 0


def test_reorder_rejects_incomplete_media_list(
    staff_api_client, page, permission_manage_pages
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    first = page.media.create(alt="first", sort_order=0)
    page.media.create(alt="second", sort_order=1)
    variables = {
        "id": _owner_global_id(MediaOwnerTypes.PAGE, page),
        "mediaIds": [_media_global_id(MediaOwnerTypes.PAGE, first)],
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_REORDER_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaReorderErrorCode.INVALID.name
    assert errors[0]["field"] == "mediaIds"
    assert errors[0]["message"] == "Incorrect number of media IDs provided."


def test_reorder_rejects_more_ids_than_the_limit(
    staff_api_client, page, permission_manage_pages
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    media = page.media.create(alt="only", sort_order=0)
    media_id = _media_global_id(MediaOwnerTypes.PAGE, media)
    variables = {
        "id": _owner_global_id(MediaOwnerTypes.PAGE, page),
        "mediaIds": [media_id] * 101,
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_REORDER_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaReorderErrorCode.INVALID.name
    assert errors[0]["field"] == "mediaIds"
    assert errors[0]["message"] == "Cannot reorder more than 100 media at once."


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
@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_reorder_authorization(
    mock_product_updated,
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

    first = media_owner.media.create(alt="first", sort_order=0)
    second = media_owner.media.create(alt="second", sort_order=1)
    variables = {
        "id": _owner_global_id(owner_type, media_owner),
        "mediaIds": [
            _media_global_id(owner_type, second),
            _media_global_id(owner_type, first),
        ],
    }

    # when
    response = client.post_graphql(MEDIA_REORDER_MUTATION, variables)

    # then
    first.refresh_from_db(fields=("sort_order",))
    second.refresh_from_db(fields=("sort_order",))
    if is_allowed:
        content = get_graphql_content(response)
        assert content["data"]["mediaReorder"]["errors"] == []
        assert second.sort_order == 0
        assert first.sort_order == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["mediaReorder"] is None
        assert first.sort_order == 0
        assert second.sort_order == 1
        mock_product_updated.assert_not_called()


def test_reorder_rejects_duplicated_media_ids(
    staff_api_client, page, permission_manage_pages
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    first = page.media.create(alt="first", sort_order=0)
    second = page.media.create(alt="second", sort_order=1)
    first_id = _media_global_id(MediaOwnerTypes.PAGE, first)
    variables = {
        "id": _owner_global_id(MediaOwnerTypes.PAGE, page),
        "mediaIds": [first_id, first_id],
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_REORDER_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaReorderErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "mediaIds"
    assert errors[0]["message"] == "Duplicate media IDs provided."
    first.refresh_from_db(fields=("sort_order",))
    second.refresh_from_db(fields=("sort_order",))
    assert first.sort_order == 0
    assert second.sort_order == 1


def test_reorder_rejects_media_id_typed_after_another_owner(
    staff_api_client, page, permission_manage_pages
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    media = page.media.create(alt="only", sort_order=0)
    mistyped_id = _media_global_id(MediaOwnerTypes.PRODUCT, media)
    variables = {
        "id": _owner_global_id(MediaOwnerTypes.PAGE, page),
        "mediaIds": [mistyped_id],
    }

    # when
    response = staff_api_client.post_graphql(MEDIA_REORDER_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaReorder"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaReorderErrorCode.NOT_MEDIA_OWNER.name
    assert errors[0]["field"] == "mediaIds"


def test_reorder_locks_rows_before_write(
    staff_api_client, page, permission_manage_pages, assert_locks_rows_before_write
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    first = page.media.create(alt="first", sort_order=0)
    second = page.media.create(alt="second", sort_order=1)
    variables = {
        "id": _owner_global_id(MediaOwnerTypes.PAGE, page),
        "mediaIds": [
            _media_global_id(MediaOwnerTypes.PAGE, second),
            _media_global_id(MediaOwnerTypes.PAGE, first),
        ],
    }

    # when
    with assert_locks_rows_before_write():
        response = staff_api_client.post_graphql(MEDIA_REORDER_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["mediaReorder"]["errors"] == []
