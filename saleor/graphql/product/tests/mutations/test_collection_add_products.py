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

COLLECTION_ADD_PRODUCTS_MUTATION = """
    mutation collectionAddProducts(
        $id: ID!, $products: [ID!]!) {
        collectionAddProducts(collectionId: $id, products: $products) {
            collection {
                products {
                    totalCount
                }
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_add_products_to_collection(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    query = COLLECTION_ADD_PRODUCTS_MUTATION

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
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_add_products_to_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = COLLECTION_ADD_PRODUCTS_MUTATION
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
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)
    assert len(product_list) == product_updated_mock.call_count


def test_add_products_to_collection_on_sale_trigger_discounted_price_recalculation(
    staff_api_client, collection, product_list, permission_manage_products
):
    query = COLLECTION_ADD_PRODUCTS_MUTATION
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
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)


def test_add_products_to_collection_with_product_without_variants(
    staff_api_client, collection, product_list, permission_manage_products
):
    # given
    query = COLLECTION_ADD_PRODUCTS_MUTATION
    product_list[0].variants.all().delete()
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    variables = {"id": collection_id, "products": product_ids}
    products_before = collection.products.count()

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)


COLLECTION_ADD_PRODUCTS_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation collectionAddProducts(
        $collectionId: ID,
        $collectionExternalReference: String,
        $products: [ID!]!
    ) {
        collectionAddProducts(
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
        COLLECTION_ADD_PRODUCTS_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["collectionAddProducts"]
    assert data["errors"] == []
    assert data["collection"] == {
        "id": graphene.Node.to_global_id("Collection", collection.pk)
    }
    assert set(collection.products.all()) == set(product_list)
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
        COLLECTION_ADD_PRODUCTS_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )

    # then
    data = get_graphql_content(response)["data"]["collectionAddProducts"]
    assert data["collection"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert collection.products.exists() is False
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
        COLLECTION_ADD_PRODUCTS_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["collectionAddProducts"]
        assert data["errors"] == []
        assert data["collection"] == {
            "id": graphene.Node.to_global_id("Collection", collection.pk)
        }
        assert set(collection.products.all()) == set(product_list)
        assert webhook.call_count == len(product_list)
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"collectionAddProducts": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["collectionAddProducts"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_PRODUCTS"
        )
        assert collection.products.exists() is False
        webhook.assert_not_called()
