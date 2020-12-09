from uuid import uuid4

import graphene
import pytest

from .....product.models import ProductVariant
from .....warehouse.models import Stock
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_variant_list(
    product_variant_list,
    api_client,
    count_queries,
    warehouse,
    warehouse_no_shipping_zone,
    shipping_zone_without_countries,
    channel_USD,
):
    query = """
        fragment BasicProductFields on Product {
          id
          name
          thumbnail {
            url
            alt
          }
          thumbnail2x: thumbnail(size: 510) {
            url
          }
        }

        fragment ProductVariantFields on ProductVariant {
          id
          sku
          name
          pricing {
            discountLocalCurrency {
              currency
              gross {
                amount
                localized
              }
            }
            price {
              currency
              gross {
                amount
                localized
              }
            }
            priceUndiscounted {
              currency
              gross {
                amount
                localized
              }
            }
            priceLocalCurrency {
              currency
              gross {
                amount
                localized
              }
            }
          }
          attributes {
            attribute {
              id
              name
            }
            values {
              id
              name
              value: name
            }
          }
        }

        query VariantList($ids: [ID!], $channel: String) {
          productVariants(ids: $ids, first: 100, channel: $channel) {
            edges {
              node {
                ...ProductVariantFields
                quantityAvailable
                quantityAvailablePl: quantityAvailable(countryCode: PL)
                quantityAvailableUS: quantityAvailable(countryCode: US)
                product {
                  ...BasicProductFields
                }
              }
            }
          }
        }
    """
    warehouse_2 = warehouse_no_shipping_zone
    warehouse_2.shipping_zones.add(shipping_zone_without_countries)
    stocks = [
        Stock(product_variant=variant, warehouse=warehouse, quantity=1)
        for variant in product_variant_list
    ]
    stocks.extend(
        [
            Stock(product_variant=variant, warehouse=warehouse_2, quantity=2)
            for variant in product_variant_list
        ]
    )
    Stock.objects.bulk_create(stocks)

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.pk)
            for variant in product_variant_list
        ],
        "channel": channel_USD.slug,
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_variant_bulk_create(
    staff_api_client,
    product_with_variant_with_two_attributes,
    permission_manage_products,
    color_attribute,
    size_attribute,
    count_queries,
):
    query = """
    mutation ProductVariantBulkCreate(
        $variants: [ProductVariantBulkCreateInput]!, $productId: ID!
    ) {
        productVariantBulkCreate(variants: $variants, product: $productId) {
            bulkProductErrors {
                field
                message
                code
                index
            }
            productVariants{
                id
                sku
            }
            count
        }
    }
    """
    product = product_with_variant_with_two_attributes
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [
                {"id": color_attribute_id, "values": ["red"]},
                {"id": size_attribute_id, "values": ["big"]},
            ],
        }
    ]
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["bulkProductErrors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()
