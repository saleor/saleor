from ...utils import get_graphql_content

PRODUCT_VARIANT_STOCK_UPDATE_MUTATION = """
mutation productVariantStocksUpdate ($stocks: [StockInput!]!, $id: ID!) {
  productVariantStocksUpdate(stocks: $stocks, variantId: $id) {
    errors {
      message
      field
    }
    productVariant {
      id
      stocks {
        quantity
        warehouse {
          id
        }
      }
    }
  }
}
"""


def product_variant_stock_update(
    staff_api_client, warehouse_id, quantity, product_variant_id
):
    variables = {
        "stocks": [
            {
                "quantity": quantity,
                "warehouse": warehouse_id,
            }
        ],
        "id": product_variant_id,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_STOCK_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    assert content["data"]["productVariantStocksUpdate"]["errors"] == []

    data = content["data"]["productVariantStocksUpdate"]["productVariant"]

    return data
