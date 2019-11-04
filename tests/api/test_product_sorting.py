import graphene

from ..api.utils import get_graphql_content

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
      id
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


def test_sort_products_within_collection_invalid_collection_id(
    staff_api_client, collection, product, permission_manage_products
):
    collection_id = graphene.Node.to_global_id("Collection", -1)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    moves = [{"productId": product_id, "sortOrder": 1}]

    content = get_graphql_content(
        staff_api_client.post_graphql(
            COLLECTION_RESORT_QUERY,
            {"collectionId": collection_id, "moves": moves},
            permissions=[permission_manage_products],
        )
    )["data"]["collectionReorderProducts"]

    assert content["errors"] == [
        {
            "field": "collectionId",
            "message": f"Couldn't resolve to a collection: {collection_id}",
        }
    ]


def test_sort_products_within_collection_invalid_product_id(
    staff_api_client, collection, product, permission_manage_products
):
    # Remove the products from the collection to make the product invalid
    collection.products.clear()
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # The move should be targeting an invalid product
    product_id = graphene.Node.to_global_id("Product", product.pk)
    moves = [{"productId": product_id, "sortOrder": 1}]

    content = get_graphql_content(
        staff_api_client.post_graphql(
            COLLECTION_RESORT_QUERY,
            {"collectionId": collection_id, "moves": moves},
            permissions=[permission_manage_products],
        )
    )["data"]["collectionReorderProducts"]

    assert content["errors"] == [
        {"field": "moves", "message": f"Couldn't resolve to a product: {product_id}"}
    ]


def test_sort_products_within_collection(
    staff_api_client,
    staff_user,
    collection,
    collection_with_products,
    permission_manage_products,
):

    staff_api_client.user.user_permissions.add(permission_manage_products)
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    products = collection_with_products
    assert len(products) == 3

    # Sort the products per sort_order
    products = list(collection.products.collection_sorted(staff_user))
    assert len(products) == 3

    variables = {
        "collectionId": collection_id,
        "moves": [
            {
                "productId": graphene.Node.to_global_id("Product", products[0].pk),
                "sortOrder": +1,
            },
            {
                "productId": graphene.Node.to_global_id("Product", products[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    expected_order = [products[1].pk, products[2].pk, products[0].pk]

    content = get_graphql_content(
        staff_api_client.post_graphql(COLLECTION_RESORT_QUERY, variables)
    )["data"]["collectionReorderProducts"]
    assert not content["errors"]

    assert content["collection"]["id"] == collection_id

    gql_products = content["collection"]["products"]["edges"]
    assert len(gql_products) == len(expected_order)

    for attr, expected_pk in zip(gql_products, expected_order):
        gql_type, gql_attr_id = graphene.Node.from_global_id(attr["node"]["id"])
        assert gql_type == "Product"
        assert int(gql_attr_id) == expected_pk
