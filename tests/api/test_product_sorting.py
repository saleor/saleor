from typing import Dict, List

import graphene
import pytest

from saleor.product.models import Product
from tests.api.utils import get_graphql_content

GET_SORTED_PRODUCTS_COLLECTION_QUERY = """
query CollectionProducts($id: ID!) {
  collection(id: $id) {
    products(first: 10) {
      edges {
        node {
          id
        }
      }
    }
  }
}
"""

COLLECTION_RESORT_QUERY = """
mutation ReorderCollectionProducts($collectionId: ID!, $moves: [MoveProductInput]!) {
  collectionReorderProducts(collectionId: $collectionId, moves: $moves) {
        collection {
      products(first: 10) {
        edges {
          node {
            name
            id
          }
        }
      }
    }
    errors {
      field
      message
    }
  }
}
"""


def _assert_product_are_correctly_ordered(expected: List[Product], nodes: List[Dict]):
    assert len(nodes) == len(expected), "Size differs"
    expected_ids = [p.pk for p in expected]
    nodes_ids = [int(graphene.Node.from_global_id(p["node"]["id"])[1]) for p in nodes]
    assert nodes_ids == expected_ids


@pytest.mark.parametrize("wanted_pos, expected_pos", ((-100, 0), (+100, 100)))
def test_sort_products_within_collection_with_out_of_bound_value(
    staff_api_client,
    collection,
    product,
    permission_manage_products,
    wanted_pos,
    expected_pos,
):
    product.collections.add(collection)
    moves = [
        {
            "productId": graphene.Node.to_global_id("Product", product.pk),
            "sortOrder": wanted_pos,
        }
    ]
    get_graphql_content(
        staff_api_client.post_graphql(
            COLLECTION_RESORT_QUERY,
            {
                "collectionId": graphene.Node.to_global_id("Collection", collection.pk),
                "moves": moves,
            },
            permissions=[permission_manage_products],
        )
    )

    # Look if the order is as expected
    assert product.collectionproduct.first().sort_order == expected_pos


def test_sort_products_within_collection_invalid_id(
    staff_api_client, collection, product, permission_manage_products
):
    product_id = graphene.Node.to_global_id("Collection", product.pk)
    moves = [{"productId": product_id, "sortOrder": 1}]
    content = get_graphql_content(
        staff_api_client.post_graphql(
            COLLECTION_RESORT_QUERY,
            {
                "collectionId": graphene.Node.to_global_id("Collection", collection.pk),
                "moves": moves,
            },
            permissions=[permission_manage_products],
        )
    )["data"]["collectionReorderProducts"]

    assert content["errors"] == [
        {"field": "moves", "message": f"Couldn't resolve to a node: {product_id}"}
    ]


def test_sort_products_within_collection(
    staff_api_client,
    staff_user,
    collection,
    collection_with_products,
    permission_manage_products,
):
    expected_product_order = list(Product.objects.collection_sorted(user=staff_user))
    assert Product.objects.count() == len(expected_product_order)

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    products = get_graphql_content(
        staff_api_client.post_graphql(
            GET_SORTED_PRODUCTS_COLLECTION_QUERY, {"id": collection_id}
        )
    )["data"]["collection"]["products"]["edges"]

    # Ensure the default the order is in place and well returned by default
    _assert_product_are_correctly_ordered(expected_product_order, products)

    # Reorder the items
    product_move_1 = expected_product_order.pop(2)
    product_move_2 = expected_product_order.pop(0)

    expected_product_order.insert(2, product_move_2)
    expected_product_order.insert(1, product_move_1)

    moves = [
        {
            "productId": graphene.Node.to_global_id("Product", product_move_1.pk),
            "sortOrder": -2,
        },
        {
            "productId": graphene.Node.to_global_id("Product", product_move_2.pk),
            "sortOrder": +2,
        },
    ]
    products = get_graphql_content(
        staff_api_client.post_graphql(
            COLLECTION_RESORT_QUERY,
            {"collectionId": collection_id, "moves": moves},
            permissions=[permission_manage_products],
        )
    )["data"]["collectionReorderProducts"]["collection"]["products"]["edges"]

    # Look if the order is right
    _assert_product_are_correctly_ordered(expected_product_order, products)
