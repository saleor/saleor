from unittest.mock import patch

import graphene
import pytest
from django.conf import settings

from .....media import MediaOwnerTypes
from .....media.models import ProductMedia
from .....product.error_codes import ProductErrorCode
from ....media.tests.utils import (
    NON_PRODUCT_OWNER_TYPES,
    create_colliding_media,
    media_count,
    media_global_id,
)
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

PRODUCT_MEDIA_BULK_DELETE_MUTATION = """
    mutation productMediaBulkDelete($ids: [ID!]!) {
        productMediaBulkDelete(ids: $ids) {
            count
            errors {
                field
                code
                message
            }
        }
    }
"""

OWNER_TYPE_TO_FIXTURE = {
    MediaOwnerTypes.CATEGORY: "category",
    MediaOwnerTypes.COLLECTION: "published_collection",
    MediaOwnerTypes.PAGE: "page",
}


@pytest.fixture
def media_owner(request, owner_type):
    """Return the non-product owner matching the test's `owner_type` parameter."""
    return request.getfixturevalue(OWNER_TYPE_TO_FIXTURE[owner_type])


def product_media_global_id(media) -> str:
    return graphene.Node.to_global_id("ProductMedia", media.pk)


def test_delete_product_media(
    staff_api_client, product_with_images, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = list(product_with_images.media.all())
    assert len(media) == 2
    variables = {"ids": [product_media_global_id(media_obj) for media_obj in media]}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaBulkDelete"]
    assert data["errors"] == []
    assert data["count"] == len(media)
    assert (
        ProductMedia.objects.filter(
            pk__in=[media_obj.pk for media_obj in media]
        ).exists()
        is False
    )


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_rejects_non_product_media_addressed_as_product_media(
    mock_delete_from_storage,
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
):
    """`MANAGE_PRODUCTS` must not delete another owner's media via a mistyped ID.

    The type name in a global ID is client-supplied, so it must not be what
    decides which table the batch reads.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = media_owner.media.create(alt="not a product media")
    variables = {"ids": [product_media_global_id(media)]}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaBulkDelete"]
    assert data["count"] == 0
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["field"] == "id"
    assert media_owner.media.filter(pk=media.pk).exists() is True
    mock_delete_from_storage.assert_not_called()


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_deletes_only_the_product_row_when_pks_collide(
    owner_type,
    media_owner,
    product,
    staff_api_client,
    permission_manage_products,
):
    """Each media model has its own pk sequence, so one pk names two real rows."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_media, other_media = create_colliding_media(
        owner_type, media_owner, product
    )
    assert product_media.pk == other_media.pk
    variables = {"ids": [product_media_global_id(product_media)]}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaBulkDelete"]
    assert data["errors"] == []
    assert data["count"] == 1
    assert ProductMedia.objects.filter(pk=product_media.pk).exists() is False
    assert media_owner.media.filter(pk=other_media.pk).exists() is True


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_rejects_an_honestly_typed_non_product_media_id(
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = media_owner.media.create(alt="not a product media")
    media_id = media_global_id(owner_type, media)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, {"ids": [media_id]}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaBulkDelete"]
    assert data["count"] == 0
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["message"] == f"Must receive ProductMedia id: {media_id}."
    assert media_owner.media.filter(pk=media.pk).exists() is True


@pytest.mark.parametrize("owner_type", [MediaOwnerTypes.PAGE])
def test_a_mixed_batch_deletes_nothing(
    owner_type,
    media_owner,
    product,
    staff_api_client,
    permission_manage_products,
):
    """A rejected batch must not take the valid half of it with it.

    The partially-resolvable case trips a bare `assert` inside the shared
    `get_nodes` helper, so it surfaces as an untyped protocol error rather than
    the mutation's own error type. That is ugly but safe; what matters here is
    that neither row is deleted.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product_media = product.media.create(alt="a real product media")
    other_media = media_owner.media.create(alt="not a product media")
    variables = {
        "ids": [
            product_media_global_id(product_media),
            product_media_global_id(other_media),
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, variables
    )

    # then
    content = get_graphql_content_from_response(response)
    assert content["data"]["productMediaBulkDelete"] is None
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"There is no node of type ProductMedia with pk {other_media.pk}"
    )
    assert ProductMedia.objects.filter(pk=product_media.pk).exists() is True
    assert media_owner.media.filter(pk=other_media.pk).exists() is True


def test_rejects_an_unknown_pk(staff_api_client, permission_manage_products):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media_id = graphene.Node.to_global_id("ProductMedia", -1)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, {"ids": [media_id]}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaBulkDelete"]
    assert data["count"] == 0
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["field"] == "id"
    assert (
        data["errors"][0]["message"]
        == f"Could not resolve to a node with the global id list of '['{media_id}']'."
    )


def test_deletes_an_owner_less_legacy_row(staff_api_client, permission_manage_products):
    """Owner-less rows stay bulk-deletable, as they were before the media split.

    `ProductMedia.product` is nullable for historical reasons and such rows are
    unreachable through every resolver, so this mutation is the only way left to
    clear them.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = ProductMedia.objects.create(alt="owner-less legacy row")
    assert media.product_id is None

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, {"ids": [product_media_global_id(media)]}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaBulkDelete"]
    assert data["errors"] == []
    assert data["count"] == 1
    assert ProductMedia.objects.filter(pk=media.pk).exists() is False


def test_rejects_more_ids_than_the_limit(
    staff_api_client, product, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = product.media.create(alt="alt")
    ids = [product_media_global_id(media)] * (settings.BULK_DELETE_LIMIT + 1)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, {"ids": ids}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaBulkDelete"]
    assert data["count"] == 0
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "ids"
    assert (
        data["errors"][0]["message"]
        == f"The maximum number of items in ids is {settings.BULK_DELETE_LIMIT}."
    )
    assert ProductMedia.objects.filter(pk=media.pk).exists() is True


def test_accepts_an_empty_list(staff_api_client, product, permission_manage_products):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    media = product.media.create(alt="alt")

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION, {"ids": []}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productMediaBulkDelete"]
    assert data["errors"] == []
    assert data["count"] == 0
    assert ProductMedia.objects.filter(pk=media.pk).exists() is True


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", None, False),
        ("Unprivileged user should be rejected", "user_api_client", None, False),
        (
            "Staff user without any permission should be rejected",
            "staff_api_client",
            None,
            False,
        ),
        (
            "Staff user holding only the page permission should be rejected",
            "staff_api_client",
            "permission_manage_pages",
            False,
        ),
        (
            "Staff user with the product permission should be allowed",
            "staff_api_client",
            "permission_manage_products",
            True,
        ),
        (
            "App with the product permission should be allowed",
            "app_api_client",
            "permission_manage_products",
            True,
        ),
    ],
)
@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_authorization(
    mock_delete_from_storage,
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    request,
    product,
    permission_manage_products,
):
    # given
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        permission = request.getfixturevalue(permission_fixture)
        if client.app:
            client.app.permissions.add(permission)
        elif client.user:
            client.user.user_permissions.add(permission)
        else:
            raise AssertionError("Couldn't add the permission")
    media = product.media.create(alt="alt")

    # when
    response = client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION,
        {"ids": [product_media_global_id(media)]},
    )

    # then
    if is_allowed:
        content = get_graphql_content(response)
        data = content["data"]["productMediaBulkDelete"]
        assert data["errors"] == []
        assert data["count"] == 1
        assert ProductMedia.objects.filter(pk=media.pk).exists() is False
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["productMediaBulkDelete"] is None
        assert ProductMedia.objects.filter(pk=media.pk).exists() is True
        mock_delete_from_storage.assert_not_called()


@pytest.mark.parametrize("owner_type", NON_PRODUCT_OWNER_TYPES)
def test_the_owner_permission_does_not_unlock_another_owners_media(
    owner_type,
    media_owner,
    staff_api_client,
    permission_manage_pages,
):
    """The mutation is product-only, not "whatever the caller has rights to".

    Holding the permission that governs the media's real owner must still be
    rejected: the route to that row is `mediaDelete`, not this mutation.
    """
    # given
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    media = media_owner.media.create(alt="not a product media")

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION,
        {"ids": [product_media_global_id(media)]},
    )

    # then
    assert_no_permission(response)
    content = get_graphql_content_from_response(response)
    assert content["data"]["productMediaBulkDelete"] is None
    assert media_owner.media.filter(pk=media.pk).exists() is True


def test_does_not_touch_media_outside_the_batch(
    staff_api_client, product, page, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    deleted = product.media.create(alt="delete me")
    kept = product.media.create(alt="keep me")
    page_media = page.media.create(alt="page media")
    media_before = media_count()

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_MEDIA_BULK_DELETE_MUTATION,
        {"ids": [product_media_global_id(deleted)]},
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productMediaBulkDelete"]["count"] == 1
    assert media_count() == media_before - 1
    assert ProductMedia.objects.filter(pk=kept.pk).exists() is True
    assert page.media.filter(pk=page_media.pk).exists() is True
