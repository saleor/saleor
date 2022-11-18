import graphene

from .....product.error_codes import ProductErrorCode
from .....warehouse.models import Stock, Warehouse
from ....tests.utils import get_graphql_content

VARIANT_STOCKS_DELETE_MUTATION = """
    mutation ProductVariantStocksDelete($variantId: ID!, $warehouseIds: [ID!]!){
        productVariantStocksDelete(
            variantId: $variantId, warehouseIds: $warehouseIds
        ){
            productVariant{
                stocks{
                    id
                    quantity
                    warehouse{
                        slug
                    }
                }
            }
            errors{
                field
                code
                message
            }
        }
    }
"""


def test_product_variant_stocks_delete_mutation(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=10),
            Stock(product_variant=variant, warehouse=second_warehouse, quantity=140),
        ]
    )
    stocks_count = variant.stocks.count()

    warehouse_ids = [graphene.Node.to_global_id("Warehouse", second_warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    variant.refresh_from_db()
    assert not data["errors"]
    assert (
        len(data["productVariant"]["stocks"])
        == variant.stocks.count()
        == stocks_count - 1
    )
    assert data["productVariant"]["stocks"][0]["quantity"] == 10
    assert data["productVariant"]["stocks"][0]["warehouse"]["slug"] == warehouse.slug


def test_product_variant_stocks_delete_mutation_invalid_warehouse_id(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.bulk_create(
        [Stock(product_variant=variant, warehouse=warehouse, quantity=10)]
    )
    stocks_count = variant.stocks.count()

    warehouse_ids = [graphene.Node.to_global_id("Warehouse", second_warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    variant.refresh_from_db()
    assert not data["errors"]
    assert (
        len(data["productVariant"]["stocks"]) == variant.stocks.count() == stocks_count
    )
    assert data["productVariant"]["stocks"][0]["quantity"] == 10
    assert data["productVariant"]["stocks"][0]["warehouse"]["slug"] == warehouse.slug


def test_product_variant_stocks_delete_mutation_invalid_object_type_of_warehouse_id(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    Stock.objects.bulk_create(
        [Stock(product_variant=variant, warehouse=warehouse, quantity=10)]
    )

    warehouse_ids = [graphene.Node.to_global_id("Product", warehouse.id)]

    variables = {"variantId": variant_id, "warehouseIds": warehouse_ids}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksDelete"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["field"] == "warehouseIds"


VARIANT_UPDATE_AND_STOCKS_REMOVE_MUTATION = """
  fragment ProductVariant on ProductVariant {
    stocks {
      id
    }
  }

  mutation VariantUpdate($removeStocks: [ID!]!, $id: ID!) {
    productVariantUpdate(id: $id, input: {}) {
      productVariant {
        ...ProductVariant
      }
    }
    productVariantStocksDelete(variantId: $id, warehouseIds: $removeStocks) {
      productVariant {
        ...ProductVariant
      }
    }
  }
"""


def test_invalidate_stocks_dataloader_on_removing_stocks(
    staff_api_client, variant_with_many_stocks, permission_manage_products
):
    # given
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", stock.warehouse.id)
        for stock in variant_with_many_stocks.stocks.all()
    ]
    variables = {
        "id": variant_id,
        "removeStocks": warehouse_ids,
    }

    # when
    response = staff_api_client.post_graphql(
        VARIANT_UPDATE_AND_STOCKS_REMOVE_MUTATION,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    variant_data = content["data"]["productVariantUpdate"]["productVariant"]
    remove_stocks_data = content["data"]["productVariantStocksDelete"]["productVariant"]

    # no stocks were removed in the first mutation
    assert len(variant_data["stocks"]) == len(warehouse_ids)

    # stocks are empty in the second mutation
    assert remove_stocks_data["stocks"] == []
