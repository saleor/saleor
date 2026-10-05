from unittest.mock import patch

import graphene
import pytest

from .....graphql.tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....product.error_codes import ProductErrorCode
from .....product.models import ProductMedia


@patch("saleor.plugins.manager.PluginsManager.product_media_deleted")
@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.product.signals.delete_from_storage_task.delay")
def test_product_media_delete(
    delete_from_storage_task_mock,
    product_updated_mock,
    product_media_deleted_mock,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    # given
    product = product_with_image
    query = """
            mutation deleteProductMedia($id: ID!) {
                productMediaDelete(id: $id) {
                    media {
                        id
                        url(size: 0)
                    }
                }
            }
        """
    media_obj = product.media.first()
    media_img_path = media_obj.image.name
    node_id = graphene.Node.to_global_id("ProductMedia", media_obj.id)
    variables = {"id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productMediaDelete"]
    assert media_obj.image.url in data["media"]["url"]
    product_media_deleted_mock.assert_called_once_with(media_obj)

    with pytest.raises(media_obj._meta.model.DoesNotExist):
        media_obj.refresh_from_db()
    assert node_id == data["media"]["id"]
    product_updated_mock.assert_called_once_with(product)
    delete_from_storage_task_mock.assert_called_once_with(media_img_path)


DELETE_PRODUCT_MEDIA_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation deleteProductMedia($id: ID, $externalReference: String) {
        productMediaDelete(id: $id, externalReference: $externalReference) {
            media {
                id
                externalReference
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


@patch("saleor.product.signals.delete_from_storage_task.delay")
def test_delete_by_external_reference(
    _delete_from_storage_task_mock,
    staff_api_client,
    product_with_image,
    permission_manage_products,
    mocker,
):
    # given
    media = product_with_image.media.get()
    external_reference = "test-ext-ref"
    media.external_reference = external_reference
    media.save(update_fields=["external_reference"])
    product_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_updated"
    )
    media_deleted_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_media_deleted"
    )
    variables = {"externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        DELETE_PRODUCT_MEDIA_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productMediaDelete"]
    assert data["errors"] == []
    assert data["media"] == {
        "id": graphene.Node.to_global_id("ProductMedia", media.pk),
        "externalReference": external_reference,
    }
    assert ProductMedia.objects.filter(pk=media.pk).exists() is False
    product_updated_mock.assert_called_once_with(product_with_image)
    media_deleted_mock.assert_called_once_with(media)


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            ProductErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'external_reference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            ProductErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    product_with_image,
    permission_manage_products,
    mocker,
):
    # given
    media = product_with_image.media.get()
    media.external_reference = "existing-reference"
    media.save(update_fields=("external_reference",))
    original_reference = media.external_reference
    product_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_updated"
    )
    media_deleted_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_media_deleted"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("ProductMedia", media.pk)

    # when
    response = staff_api_client.post_graphql(
        DELETE_PRODUCT_MEDIA_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["productMediaDelete"]
    assert data["media"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    media.refresh_from_db(fields=("external_reference",))
    assert media.external_reference == original_reference
    product_updated_mock.assert_not_called()
    media_deleted_mock.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", False),
        ("customer", "user_api_client", False),
        ("staff_without_permission", "staff_api_client", False),
        ("staff_with_permission", "staff_api_client", True),
        ("app_without_permission", "app_api_client", False),
        ("app_with_permission", "app_api_client", True),
    ],
)
@patch("saleor.product.signals.delete_from_storage_task.delay")
def test_external_reference_authorization(
    delete_from_storage_task_mock,
    _case,
    client_fixture,
    is_allowed,
    request,
    product_with_image,
    permission_manage_products,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    media = product_with_image.media.get()
    media.external_reference = "existing-reference"
    media.save(update_fields=("external_reference",))
    original_reference = media.external_reference
    media_img_path = media.image.name
    product_updated_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_updated"
    )
    media_deleted_mock = mocker.patch(
        "saleor.plugins.manager.PluginsManager.product_media_deleted"
    )
    variables = {"externalReference": original_reference}

    # when
    response = client.post_graphql(
        DELETE_PRODUCT_MEDIA_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["productMediaDelete"]
        assert data["errors"] == []
        assert ProductMedia.objects.filter(pk=media.pk).exists() is False
        assert data["media"] == {
            "id": graphene.Node.to_global_id("ProductMedia", media.pk),
            "externalReference": original_reference,
        }
        product_updated_mock.assert_called_once_with(product_with_image)
        media_deleted_mock.assert_called_once_with(media)
        delete_from_storage_task_mock.assert_called_once_with(media_img_path)
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"productMediaDelete": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["productMediaDelete"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_PRODUCTS"
        )
        media.refresh_from_db(fields=("external_reference",))
        assert media.external_reference == original_reference
        product_updated_mock.assert_not_called()
        media_deleted_mock.assert_not_called()
        delete_from_storage_task_mock.assert_not_called()
