from unittest.mock import patch

import graphene
import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....media import MediaOwnerTypes
from .....media.error_codes import MediaDeleteErrorCode
from .....media.models import ProductMedia
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
    assert type(media).objects.filter(pk=media.pk).exists() is False
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


@patch("saleor.plugins.manager.PluginsManager.media_deleted")
def test_delete_with_an_unsupported_media_type_reports_invalid_not_denied(
    mock_media_deleted, api_client, product
):
    """An ID naming no media type skips the permission check by design.

    `check_permissions` cannot resolve a permission to require, so it lets the
    mutation run and answer with a precise `INVALID`. Nothing is reachable
    either way - this pins that down so the bypass cannot quietly widen.
    """
    # given
    media = product.media.create(alt="alt")
    media_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = api_client.post_graphql(MEDIA_DELETE_MUTATION, {"id": media_id})

    # then
    content = get_graphql_content(response)
    errors = content["data"]["mediaDelete"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == MediaDeleteErrorCode.INVALID.name
    assert errors[0]["field"] == "id"
    assert errors[0]["message"] == (
        "Expected a ProductMedia, CategoryMedia, CollectionMedia or PageMedia ID."
    )
    assert ProductMedia.objects.filter(pk=media.pk).exists() is True
    mock_media_deleted.assert_not_called()


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
@patch("saleor.plugins.manager.PluginsManager.media_deleted")
def test_delete_rejects_id_of_a_different_owner_type(
    mock_media_deleted,
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
):
    """`MANAGE_PRODUCTS` must not delete another owner's media via a mistyped ID."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = media_owner.media.create(alt="not a product media")
    media_id = media_global_id(MediaOwnerTypes.PRODUCT, media)

    # when
    response = staff_api_client.post_graphql(MEDIA_DELETE_MUTATION, {"id": media_id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaDelete"]
    assert data["media"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == MediaDeleteErrorCode.NOT_FOUND.name
    assert data["errors"][0]["field"] == "id"
    assert media_owner.media.filter(pk=media.pk).exists() is True
    mock_media_deleted.assert_not_called()


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_delete_removes_the_product_row_when_pks_collide(
    owner_type,
    media_owner,
    product,
    staff_api_client,
    permission_manage_products,
):
    """One pk names a real row in every media table; the type name picks one."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_media, other_media = create_colliding_media(
        owner_type, media_owner, product
    )
    media_id = media_global_id(MediaOwnerTypes.PRODUCT, product_media)

    # when
    response = staff_api_client.post_graphql(MEDIA_DELETE_MUTATION, {"id": media_id})

    # then
    content = get_graphql_content(response)
    data = content["data"]["mediaDelete"]
    assert data["errors"] == []
    assert data["media"]["id"] == media_id
    assert ProductMedia.objects.filter(pk=product_media.pk).exists() is False
    assert media_owner.media.filter(pk=other_media.pk).exists() is True


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
@patch("saleor.plugins.manager.PluginsManager.media_deleted")
def test_delete_denies_a_colliding_pk_without_the_product_permission(
    mock_media_deleted,
    owner_type,
    media_owner,
    product,
    staff_api_client,
    permission_manage_pages,
):
    """`MANAGE_PAGES` must not delete a product media, even at a shared pk."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    product_media, other_media = create_colliding_media(
        owner_type, media_owner, product
    )

    # when
    response = staff_api_client.post_graphql(
        MEDIA_DELETE_MUTATION,
        {"id": media_global_id(MediaOwnerTypes.PRODUCT, product_media)},
    )

    # then
    assert_no_permission(response)
    content = get_graphql_content_from_response(response)
    assert content["data"]["mediaDelete"] is None
    assert ProductMedia.objects.filter(pk=product_media.pk).exists() is True
    assert media_owner.media.filter(pk=other_media.pk).exists() is True
    mock_media_deleted.assert_not_called()


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
        assert type(media).objects.filter(pk=media.pk).exists() is False
        assert mock_media_deleted.call_count == 1
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["mediaDelete"] is None
        assert type(media).objects.filter(pk=media.pk).exists() is True
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
