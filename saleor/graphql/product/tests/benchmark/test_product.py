import json

import graphene
import pytest
from graphene import Node

from .....attribute.utils import associate_attribute_values_to_instance
from .....core.taxes import TaxType
from .....plugins.manager import PluginsManager
from .....product.models import ProductTranslation
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_details(product_with_image, api_client, count_queries, channel_USD):
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
          media {
            id
            url
            type
            alt
          }
          images {
            id
            url
            alt
          }
        }

        query ProductDetails($id: ID!, $channel: String) {
          product(id: $id, channel: $channel) {
            ...BasicProductFields
            description
            category {
              id
              name
              products(first: 4, channel: $channel) {
                edges {
                  node {
                    ...BasicProductFields
                    category {
                      id
                      name
                    }
                    pricing {
                      priceRange {
                        start{
                          currency
                          gross {
                            amount
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                          }
                        }
                      }
                      priceRangeUndiscounted {
                        start{
                          currency
                          gross {
                            amount
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                          }
                        }
                      }
                      priceRangeLocalCurrency {
                        start{
                          currency
                          gross {
                            amount
                          }
                        }
                        stop{
                          currency
                          gross {
                            amount
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            media {
              id
            }
            images {
              id
            }
            variants {
              ...ProductVariantFields
            }
            seoDescription
            seoTitle
            isAvailable
          }
        }
    """
    product = product_with_image
    variant = product_with_image.variants.first()
    media = product_with_image.get_first_image()
    media.variant_media.create(variant=variant)

    variables = {
        "id": Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_attributes(
    product_list, api_client, count_queries, channel_USD
):
    query = """
        query($sortBy: ProductOrder, $channel: String) {
          products(first: 10, sortBy: $sortBy, channel: $channel) {
            edges {
              node {
                id
                attributes {
                  attribute {
                    id
                  }
                }
              }
            }
          }
        }
    """

    variables = {"channel": channel_USD.slug}
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_images(product_list, api_client, count_queries, channel_USD):
    query = """
        query($sortBy: ProductOrder, $channel: String) {
          products(first: 10, sortBy: $sortBy, channel: $channel) {
            edges {
              node {
                id
                images {
                  id
                }
              }
            }
          }
        }
    """

    variables = {"channel": channel_USD.slug}
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_media(product_list, api_client, count_queries, channel_USD):
    query = """
        query($sortBy: ProductOrder, $channel: String) {
          products(first: 10, sortBy: $sortBy, channel: $channel) {
            edges {
              node {
                id
                media {
                  id
                }
              }
            }
          }
        }
    """

    variables = {"channel": channel_USD.slug}
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_channel_listings(
    product_list_with_many_channels,
    staff_api_client,
    count_queries,
    permission_manage_products,
    channel_USD,
):
    query = """
        query($channel: String) {
          products(first: 10, channel: $channel) {
            edges {
              node {
                id
                channelListings {
                  publicationDate
                  isPublished
                  channel{
                    slug
                    currencyCode
                    name
                    isActive
                  }
                  visibleInListings
                  discountedPrice{
                    amount
                    currency
                  }
                  purchaseCost{
                    start{
                      amount
                    }
                    stop{
                      amount
                    }
                  }
                  margin{
                    start
                    stop
                  }
                  isAvailableForPurchase
                  availableForPurchase
                  pricing {
                    priceRangeUndiscounted {
                      start {
                        gross {
                          amount
                          currency
                        }
                      }
                      stop {
                        gross {
                          amount
                          currency
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
    """

    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            query,
            variables,
            permissions=(permission_manage_products,),
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrive_products_with_product_types_and_attributes(
    product_list,
    api_client,
    count_queries,
    channel_USD,
):
    query = """
        query($channel: String) {
          products(first: 10, channel: $channel) {
            edges {
              node {
                id
                  productType {
                    name
                  productAttributes {
                    name
                  }
                  variantAttributes {
                    name
                  }
                }
              }
            }
          }
        }
    """
    variables = {"channel": channel_USD.slug}
    get_graphql_content(api_client.post_graphql(query, variables))


def test_product_create(
    settings,
    staff_api_client,
    product_type,
    category,
    size_attribute,
    description_json,
    permission_manage_products,
    monkeypatch,
    count_queries,
):
    query = """
        mutation createProduct($input: ProductCreateInput!) {
            productCreate(input: $input) {
                product {
                    id
                    category {
                        name
                    }
                    description
                    chargeTaxes
                    taxType {
                        taxCode
                        description
                    }
                    name
                    slug
                    rating
                    productType {
                        name
                    }
                    attributes {
                        attribute {
                            slug
                        }
                    values {
                        slug
                        name
                        reference
                        file {
                            url
                            contentType
                        }
                    }
                }
            }
            errors {
                field
                code
                message
                attributes
            }
        }
    }
"""
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name="Color")
    color_value_slug = color_attr.values.first().slug
    color_attr_id = graphene.Node.to_global_id("Attribute", color_attr.id)

    # Add second attribute
    product_type.product_attributes.add(size_attribute)
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    non_existent_attr_value = "The cake is a lie"

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [
                {"id": color_attr_id, "values": [color_value_slug]},
                {"id": size_attr_id, "values": [non_existent_attr_value]},
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert not content["data"]["productCreate"]["errors"]


def test_update_product(
    settings,
    staff_api_client,
    category,
    non_default_category,
    collection_list,
    product_with_variant_with_two_attributes,
    other_description_json,
    permission_manage_products,
    monkeypatch,
    count_queries,
):
    query = """
    mutation updateProduct($productId: ID!, $input: ProductInput!) {
        productUpdate(id: $productId, input: $input) {
                product {
                    category {
                        name
                    }
                    rating
                    description
                    chargeTaxes
                    variants {
                        name
                    }
                    taxType {
                        taxCode
                        description
                    }
                    name
                    slug
                    productType {
                        name
                    }
                    attributes {
                        attribute {
                            id
                            name
                        }
                        values {
                            id
                            name
                            slug
                            reference
                            file {
                                url
                                contentType
                            }
                        }
                    }
                }
                errors {
                    message
                    field
                    code
                }
            }
        }
    """
    product = product_with_variant_with_two_attributes
    for collection in collection_list:
        collection.products.add(product)
    other_description_json = json.dumps(other_description_json)
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    product_id = graphene.Node.to_global_id("Product", product.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_name = "updated name"
    product_slug = "updated-product"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    variables = {
        "productId": product_id,
        "input": {
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": other_description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert not data["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_filter_products_by_attributes(
    api_client, product_list, channel_USD, count_queries
):
    query = """
      query ($channel: String, $filter: ProductFilterInput){
          products(
              channel: $channel,
              filter: $filter,
              first: 20,
          ) {
              edges {
                  node {
                      name
                  }
              }
          }
      }
    """

    product = product_list[0]
    attr_assignment = product.attributes.first()
    attr = attr_assignment.attribute
    variables = {
        "channel": channel_USD.slug,
        "filter": {
            "attributes": [
                {"slug": attr.slug, "values": [attr_assignment.values.first().slug]}
            ]
        },
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_filter_products_by_numeric_attributes(
    api_client, product_list, numeric_attribute, channel_USD, count_queries
):
    query = """
      query ($channel: String,  $filter: ProductFilterInput){
          products(
              channel: $channel,
              filter: $filter,
              first: 20,
          ) {
              edges {
                  node {
                      name
                  }
              }
          }
      }
    """

    product = product_list[0]
    product.product_type.product_attributes.add(numeric_attribute)
    associate_attribute_values_to_instance(
        product, numeric_attribute, *numeric_attribute.values.all()
    )
    variables = {
        "channel": channel_USD.slug,
        "filter": {
            "attributes": [
                {
                    "slug": numeric_attribute.slug,
                    "valuesRange": {
                        "gte": 10,
                        "lte": 20,
                    },
                }
            ]
        },
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_filter_products_by_boolean_attributes(
    api_client, product_list, boolean_attribute, channel_USD, count_queries
):
    query = """
      query ($channel: String,  $filter: ProductFilterInput){
          products(
              channel: $channel,
              filter: $filter,
              first: 20,
          ) {
              edges {
                  node {
                      name
                  }
              }
          }
      }
    """

    product = product_list[0]
    product.product_type.product_attributes.add(boolean_attribute)
    associate_attribute_values_to_instance(
        product, boolean_attribute, *boolean_attribute.values.all()
    )
    variables = {
        "channel": channel_USD.slug,
        "filter": {
            "attributes": [
                {
                    "slug": boolean_attribute.slug,
                    "boolean": True,
                }
            ]
        },
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_translations(api_client, product_list, channel_USD, count_queries):
    query = """
      query($channel: String) {
        products(channel: $channel, first: 20) {
          edges {
            node {
              name
              translation(languageCode: EN) {
                name
              }
            }
          }
        }
      }
    """
    translations = []
    for product in product_list:
        translations.append(ProductTranslation(product=product, language_code="en"))
    ProductTranslation.objects.bulk_create(translations)

    variables = {"channel": channel_USD.slug}
    get_graphql_content(api_client.post_graphql(query, variables))
