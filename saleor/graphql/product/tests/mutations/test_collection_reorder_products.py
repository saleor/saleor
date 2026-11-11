import graphene
import pytest

from .....product.error_codes import CollectionErrorCode
from .....product.models import CollectionProduct
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

COLLECTION_REORDER_PRODUCTS_MUTATION = """
    mutation collectionReorderProducts(
        $collectionId: ID,
        $collectionExternalReference: String,
        $moves: [MoveProductInput!]!
    ) {
        collectionReorderProducts(
            collectionId: $collectionId,
            collectionExternalReference: $collectionExternalReference,
            moves: $moves
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


def _set_initial_sort_order(collection):
    """Order collection products by product id and return product ids in that order."""
    collection_products = list(collection.collectionproduct.order_by("product_id"))
    for sort_order, collection_product in enumerate(collection_products):
        collection_product.sort_order = sort_order
    CollectionProduct.objects.bulk_update(collection_products, ["sort_order"])
    return [collection_product.product_id for collection_product in collection_products]


def _get_sorted_product_ids(collection):
    return list(
        collection.collectionproduct.order_by("sort_order").values_list(
            "product_id", flat=True
        )
    )


def test_by_collection_external_reference(
    staff_api_client,
    published_collection,
    collection_with_products,
    permission_manage_products,
):
    # given
    collection = published_collection
    external_reference = "test-ext-ref"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    first_id, second_id, third_id = _set_initial_sort_order(collection)
    variables = {
        "collectionExternalReference": external_reference,
        "moves": [
            {
                "productId": graphene.Node.to_global_id("Product", third_id),
                "sortOrder": -1,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_REORDER_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["collectionReorderProducts"]
    assert data["errors"] == []
    assert data["collection"] == {
        "id": graphene.Node.to_global_id("Collection", collection.pk)
    }
    assert _get_sorted_product_ids(collection) == [first_id, third_id, second_id]


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
    published_collection,
    collection_with_products,
    permission_manage_products,
):
    # given
    collection = published_collection
    collection.external_reference = "existing-reference"
    collection.save(update_fields=["external_reference"])
    initial_order = _set_initial_sort_order(collection)
    variables = dict(identifiers)
    if _case == "both":
        variables["collectionId"] = graphene.Node.to_global_id(
            "Collection", collection.pk
        )
    variables["moves"] = [
        {
            "productId": graphene.Node.to_global_id("Product", initial_order[-1]),
            "sortOrder": -1,
        }
    ]

    # when
    response = staff_api_client.post_graphql(
        COLLECTION_REORDER_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )

    # then
    data = get_graphql_content(response)["data"]["collectionReorderProducts"]
    assert data["collection"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert _get_sorted_product_ids(collection) == initial_order


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
    published_collection,
    collection_with_products,
    permission_manage_products,
):
    # given
    client = request.getfixturevalue(client_fixture)
    collection = published_collection
    external_reference = "existing-reference"
    collection.external_reference = external_reference
    collection.save(update_fields=["external_reference"])
    first_id, second_id, third_id = _set_initial_sort_order(collection)
    variables = {
        "collectionExternalReference": external_reference,
        "moves": [
            {
                "productId": graphene.Node.to_global_id("Product", third_id),
                "sortOrder": -1,
            }
        ],
    }

    # when
    response = client.post_graphql(
        COLLECTION_REORDER_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["collectionReorderProducts"]
        assert data["errors"] == []
        assert data["collection"] == {
            "id": graphene.Node.to_global_id("Collection", collection.pk)
        }
        assert _get_sorted_product_ids(collection) == [first_id, third_id, second_id]
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"collectionReorderProducts": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["collectionReorderProducts"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_PRODUCTS"
        )
        assert _get_sorted_product_ids(collection) == [first_id, second_id, third_id]
