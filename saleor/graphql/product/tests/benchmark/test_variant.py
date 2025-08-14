from uuid import uuid4

import graphene
import pytest

from .....product.models import ProductMedia, ProductVariant, VariantMedia
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
              }
            }
            price {
              currency
              gross {
                amount
              }
            }
            priceUndiscounted {
              currency
              gross {
                amount
              }
            }
            priceLocalCurrency {
              currency
              gross {
                amount
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
        $variants: [ProductVariantBulkCreateInput!]!, $productId: ID!
    ) {
        productVariantBulkCreate(variants: $variants, product: $productId) {
            errors {
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
    assert not data["errors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_variant_create(
    staff_api_client,
    permission_manage_products,
    product_type,
    product_available_in_many_channels,
    warehouse,
    settings,
    count_queries,
):
    query = """
        mutation createVariant (
            $productId: ID!,
            $sku: String,
            $stocks: [StockInput!],
            $attributes: [AttributeValueInput!]!,
            $weight: WeightScalar,
            $trackInventory: Boolean
        ) {
            productVariantCreate(
                input: {
                    product: $productId,
                    sku: $sku,
                    stocks: $stocks,
                    attributes: $attributes,
                    trackInventory: $trackInventory,
                    weight: $weight
                }
            ) {
                errors {
                    field
                    message
                    attributes
                    code
                }
                productVariant {
                    id
                    name
                    sku
                    attributes {
                        attribute {
                            slug
                        }
                        values {
                            name
                            slug
                            reference
                            file {
                                url
                                contentType
                            }
                        }
                    }
                    weight {
                        value
                        unit
                    }
                    stocks {
                        quantity
                    warehouse {
                        slug
                    }
                }
            }
        }
    }
    """
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    product = product_available_in_many_channels
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    weight = 10.22
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]

    variables = {
        "productId": product_id,
        "sku": sku,
        "stocks": stocks,
        "weight": weight,
        "attributes": [
            {"id": attribute_id, "values": ["red"]},
        ],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    assert not content["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_update_product_variant(
    staff_api_client,
    permission_manage_products,
    product_available_in_many_channels,
    product_type,
    media_root,
    settings,
    image,
    count_queries,
):
    query = """
        mutation VariantUpdate(
            $id: ID!
            $attributes: [AttributeValueInput!]
            $sku: String
            $trackInventory: Boolean!
        ) {
            productVariantUpdate(
                id: $id
                input: {
                    attributes: $attributes
                    sku: $sku
                    trackInventory: $trackInventory
                }
            ) {
            errors {
                field
                message
            }
            productVariant {
                id
                attributes {
                    attribute {
                        id
                        name
                        slug
                        choices(first: 10) {
                            edges {
                                node {
                                    id
                                    name
                                    slug
                                    __typename
                                }
                            }
                        }
                    __typename
                    }
                __typename
                }
            }
        }
    }
    """
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    product = product_available_in_many_channels
    variant = product.variants.first()
    product_image = ProductMedia.objects.create(product=product, image=image)
    VariantMedia.objects.create(variant=variant, media=product_image)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variables = {
        "attributes": [
            {"id": attribute_id, "values": ["yellow"]},
        ],
        "id": variant_id,
        "sku": "21599567",
        "trackInventory": True,
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_products]
        )
    )["data"]["productVariantUpdate"]
    assert not data["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_products_variants_for_federation_query_count(
    api_client,
    product_variant_list,
    channel_USD,
    django_assert_num_queries,
    count_queries,
):
    query = """
      query GetProductVariantInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on ProductVariant {
            id
            name
          }
        }
      }
    """

    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": graphene.Node.to_global_id(
                    "ProductVariant", product_variant_list[0].pk
                ),
                "channel": channel_USD.slug,
            },
        ],
    }

    with django_assert_num_queries(3):
        response = api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 1

    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
                "channel": channel_USD.slug,
            }
            for variant in product_variant_list
        ],
    }

    with django_assert_num_queries(3):
        response = api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 4
