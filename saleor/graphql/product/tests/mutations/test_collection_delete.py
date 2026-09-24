from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.core.files import File

from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....discount.utils.promotion import get_active_catalogue_promotion_rules
from .....product.error_codes import CollectionErrorCode
from .....product.models import Collection
from .....thumbnail.models import Thumbnail
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

DELETE_COLLECTION_MUTATION = """
    mutation deleteCollection($id: ID!) {
        collectionDelete(id: $id) {
            collection {
                name
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


DELETE_COLLECTION_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation deleteCollection($id: ID, $externalReference: String) {
        collectionDelete(id: $id, externalReference: $externalReference) {
            collection {
                name
                externalReference
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_delete_collection_by_external_reference(
    staff_api_client, collection, permission_manage_products
):
    # given
    external_reference = "test-ext-ref"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    variables = {"externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        DELETE_COLLECTION_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["collectionDelete"]
    assert data["errors"] == []
    assert data["collection"]["name"] == collection.name
    assert data["collection"]["externalReference"] == external_reference
    assert Collection.objects.filter(pk=collection.pk).exists() is False


@patch("saleor.plugins.manager.PluginsManager.collection_deleted")
def test_delete_collection(
    deleted_webhook_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION
    collection.products.set(product_list)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"id": collection_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()

    deleted_webhook_mock.assert_called_once()
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_delete_collection_with_background_image(
    delete_from_storage_task_mock,
    staff_api_client,
    collection_with_image,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION
    collection = collection_with_image

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(collection=collection, size=128, image=thumbnail_mock)
    Thumbnail.objects.create(collection=collection, size=200, image=thumbnail_mock)

    collection_id = collection.id
    variables = {"id": graphene.Node.to_global_id("Collection", collection.id)}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()
    # ensure all related thumbnails has been deleted
    assert not Thumbnail.objects.filter(collection_id=collection_id)
    assert delete_from_storage_task_mock.call_count == 3


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_delete_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = DELETE_COLLECTION_MUTATION
    collection.products.add(*product_list)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"id": collection_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]["collection"]
    assert data["name"] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()
    assert len(product_list) == product_updated_mock.call_count


def test_collection_delete_removes_reference_to_product(
    staff_api_client,
    collection,
    product_type_product_reference_attribute,
    product_type,
    product,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION

    product_type.product_attributes.add(product_type_product_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=collection.name,
        slug=f"{product.pk}_{collection.pk}",
        reference_collection=collection,
    )
    associate_attribute_values_to_instance(
        product, {product_type_product_reference_attribute.pk: [attr_value]}
    )
    reference_id = graphene.Node.to_global_id("Collection", collection.pk)

    variables = {"id": reference_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()

    assert not data["errors"]


def test_collection_delete_removes_reference_to_product_variant(
    staff_api_client,
    collection,
    product_type_product_reference_attribute,
    product_type,
    product_list,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION

    variant = product_list[0].variants.first()
    product_type.variant_attributes.set([product_type_product_reference_attribute])
    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=collection.name,
        slug=f"{variant.pk}_{collection.pk}",
        reference_collection=collection,
    )
    associate_attribute_values_to_instance(
        variant, {product_type_product_reference_attribute.pk: [attr_value]}
    )
    reference_id = graphene.Node.to_global_id("Collection", collection.pk)

    variables = {"id": reference_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()

    assert not data["errors"]


def test_collection_delete_removes_reference_to_page(
    staff_api_client,
    collection,
    page,
    page_type_product_reference_attribute,
    permission_manage_products,
):
    # given
    query = DELETE_COLLECTION_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_product_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{collection.pk}",
        reference_collection=collection,
    )
    associate_attribute_values_to_instance(
        page, {page_type_product_reference_attribute.pk: [attr_value]}
    )
    reference_id = graphene.Node.to_global_id("Collection", collection.pk)

    variables = {"id": reference_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()

    assert not data["errors"]


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            CollectionErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            CollectionErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            CollectionErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            CollectionErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'external_reference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            CollectionErrorCode.NOT_FOUND,
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
    collection,
    permission_manage_products,
    mocker,
):
    # given
    collection.external_reference = "existing-reference"
    collection.save(update_fields=("external_reference",))
    original_name = collection.name
    original_reference = collection.external_reference
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.collection_deleted")
    task = mocker.patch("saleor.product.tasks.collection_product_updated_task.delay")
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Collection", collection.pk)

    # when
    response = staff_api_client.post_graphql(
        DELETE_COLLECTION_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["collectionDelete"]
    assert data["collection"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    collection.refresh_from_db(fields=("name", "external_reference"))
    assert collection.name == original_name
    assert collection.external_reference == original_reference
    webhook.assert_not_called()
    task.assert_not_called()


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
def test_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    collection,
    permission_manage_products,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    collection.external_reference = "existing-reference"
    collection.save(update_fields=("external_reference",))
    original_name = collection.name
    original_reference = collection.external_reference
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.collection_deleted")
    task = mocker.patch("saleor.product.tasks.collection_product_updated_task.delay")
    variables = {"externalReference": original_reference}

    # when
    response = client.post_graphql(
        DELETE_COLLECTION_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["collectionDelete"]
        assert data["errors"] == []
        assert Collection.objects.filter(pk=collection.pk).exists() is False
        assert data["collection"] == {
            "name": original_name,
            "externalReference": original_reference,
        }
        webhook.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"collectionDelete": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["collectionDelete"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: MANAGE_PRODUCTS"
        )
        collection.refresh_from_db(fields=("name", "external_reference"))
        assert collection.name == original_name
        assert collection.external_reference == original_reference
        webhook.assert_not_called()
        task.assert_not_called()
