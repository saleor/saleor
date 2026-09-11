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
    OWNER_TYPE_TO_MEDIA_GRAPHQL_TYPE,
)
from .....product.models import ProductMedia
from ..utils import (
    MEDIA_AUTH_CASES,
    MEDIA_AUTH_PARAMS,
    media_global_id,
)

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
    media_id = media_global_id(owner_type, media)
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
@pytest.mark.parametrize(MEDIA_AUTH_PARAMS, MEDIA_AUTH_CASES)
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
    grant_media_permission,
):
    # given
    client = request.getfixturevalue(client_fixture)
    grant_media_permission(client, permission_fixture)

    media = media_owner.media.create(alt="alt")
    variables = {"id": media_global_id(owner_type, media)}

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


@pytest.mark.parametrize("owner_type", ALL_OWNER_TYPES)
@patch("saleor.plugins.manager.PluginsManager.product_media_deleted")
@patch("saleor.plugins.manager.PluginsManager.media_deleted")
def test_delete_also_fires_the_deprecated_product_media_event(
    mock_media_deleted,
    mock_product_media_deleted,
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
    permission_manage_pages,
):
    """`PRODUCT_MEDIA_DELETED` must keep firing for product-owned media."""
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_pages
    )
    media = media_owner.media.create(alt="alt")
    variables = {"id": media_global_id(owner_type, media)}

    # when
    response = staff_api_client.post_graphql(MEDIA_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["mediaDelete"]["errors"] == []
    mock_media_deleted.assert_called_once_with(media)
    if owner_type == MediaOwnerTypes.PRODUCT:
        mock_product_media_deleted.assert_called_once_with(media)
    else:
        mock_product_media_deleted.assert_not_called()
