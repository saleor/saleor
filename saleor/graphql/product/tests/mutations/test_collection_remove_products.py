from unittest.mock import patch

import graphene
import pytest

from .....discount.utils.promotion import get_active_catalogue_promotion_rules
from .....product.error_codes import CollectionErrorCode
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

COLLECTION_REMOVE_PRODUCTS_MUTATION = """
    mutation collectionRemoveProducts(
        $id: ID!, $products: [ID!]!) {
        collectionRemoveProducts(collectionId: $id, products: $products) {
            collection {
                products {
                    totalCount
                }
            }
        }
    }
"""


def test_remove_products_from_collection(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    query = COLLECTION_REMOVE_PRODUCTS_MUTATION
    collection.products.add(*product_list)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionRemoveProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before - len(product_ids)
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_remove_products_from_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = COLLECTION_REMOVE_PRODUCTS_MUTATION
    collection.products.add(*product_list)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionRemoveProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before - len(product_ids)
    assert len(product_list) == product_updated_mock.call_count


COLLECTION_REMOVE_PRODUCTS_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation collectionRemoveProducts(
        $collectionId: ID,
        $collectionExternalReference: String,
        $products: [ID!]!
    ) {
        collectionRemoveProducts(
            collectionId: $collectionId,
            collectionExternalReference: $collectionExternalReference,
            products: $products
        ) {
            collection {
                id
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_by_collection_external_reference(
    staff_api_client, collection, product_list, permission_manage_products, mocker
):
    # given
    external_reference = "test-ext-ref"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    collection.products.add(*product_list)
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.product_updated")
    variables = {
        "collectionExternalReference": external_reference,
        "products": [
            graphene.Node.to_global_id("Product", product.pk)
            for product in product_list
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_REMOVE_PRODUCTS_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["collectionRemoveProducts"]
    assert data["errors"] == []
    assert data["collection"] == {
        "id": graphene.Node.to_global_id("Collection", collection.pk)
    }
    assert collection.products.exists() is False
    assert webhook.call_count == len(product_list)


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            CollectionErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: "
            "'collectionId', 'collectionExternalReference'.",
        ),
        (
            "null",
            {"collectionId": None, "collectionExternalReference": None},
            None,
            CollectionErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: "
            "'collectionId', 'collectionExternalReference'.",
        ),
        (
            "empty",
            {"collectionExternalReference": ""},
            None,
            CollectionErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: "
            "'collectionId', 'collectionExternalReference'.",
        ),
        (
            "both",
            {"collectionExternalReference": "existing-reference"},
            None,
            CollectionErrorCode.GRAPHQL_ERROR,
            "Argument 'collectionId' cannot be combined with "
            "'collectionExternalReference'",
        ),
        (
            "not_found",
            {"collectionExternalReference": "missing-reference"},
            "collectionExternalReference",
            CollectionErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_collection_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
    mocker,
):
    # given
    collection.external_reference = "existing-reference"
    collection.save(update_fields=["external_reference"])
    collection.products.add(*product_list)
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.product_updated")
    variables = dict(identifiers)
    if _case == "both":
        variables["collectionId"] = graphene.Node.to_global_id(
            "Collection", collection.pk
        )
    variables["products"] = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_REMOVE_PRODUCTS_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )

    # then
    data = get_graphql_content(response)["data"]["collectionRemoveProducts"]
    assert data["collection"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert set(collection.products.all()) == set(product_list)
    webhook.assert_not_called()


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
def test_collection_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    collection,
    product_list,
    permission_manage_products,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    external_reference = "existing-reference"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    collection.products.add(*product_list)
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.product_updated")
    variables = {
        "collectionExternalReference": external_reference,
        "products": [
            graphene.Node.to_global_id("Product", product.pk)
            for product in product_list
        ],
    }

    # when
    response = client.post_graphql(
        COLLECTION_REMOVE_PRODUCTS_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["collectionRemoveProducts"]
        assert data["errors"] == []
        assert data["collection"] == {
            "id": graphene.Node.to_global_id("Collection", collection.pk)
        }
        assert collection.products.exists() is False
        assert webhook.call_count == len(product_list)
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"collectionRemoveProducts": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["collectionRemoveProducts"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_PRODUCTS"
        )
        assert set(collection.products.all()) == set(product_list)
        webhook.assert_not_called()
