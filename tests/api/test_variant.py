from unittest.mock import ANY
from uuid import uuid4

import graphene
import pytest
from graphene.utils.str_converters import to_camel_case

from saleor.product.error_codes import ProductErrorCode
from saleor.product.models import ProductVariant
from saleor.product.utils.attributes import associate_attribute_values_to_instance
from saleor.warehouse.error_codes import StockErrorCode
from saleor.warehouse.models import Stock, Warehouse
from tests.api.utils import get_graphql_content


def test_fetch_variant(staff_api_client, product, permission_manage_products):
    query = """
    query ProductVariantDetails($id: ID!, $countyCode: CountryCode) {
        productVariant(id: $id) {
            id
            stocks(countryCode: $countyCode) {
                id
            }
            attributes {
                attribute {
                    id
                    name
                    slug
                    values {
                        id
                        name
                        slug
                    }
                }
                values {
                    id
                    name
                    slug
                }
            }
            costPrice {
                currency
                amount
            }
            images {
                id
            }
            name
            priceOverride {
                currency
                amount
            }
            product {
                id
            }
        }
    }
    """

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "countyCode": "EU"}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["name"] == variant.name
    assert len(data["stocks"]) == variant.stocks.count()


def test_create_variant(
    staff_api_client, product, product_type, permission_manage_products, warehouse
):
    query = """
        mutation createVariant (
            $productId: ID!,
            $sku: String!,
            $stocks: [StockInput!],
            $priceOverride: Decimal,
            $costPrice: Decimal,
            $attributes: [AttributeValueInput]!,
            $weight: WeightScalar,
            $trackInventory: Boolean!) {
                productVariantCreate(
                    input: {
                        product: $productId,
                        sku: $sku,
                        stocks: $stocks,
                        priceOverride: $priceOverride,
                        costPrice: $costPrice,
                        attributes: $attributes,
                        trackInventory: $trackInventory,
                        weight: $weight
                    }) {
                    productErrors {
                      field
                      message
                    }
                    productVariant {
                        name
                        sku
                        attributes {
                            attribute {
                                slug
                            }
                            values {
                                slug
                            }
                        }
                        priceOverride {
                            currency
                            amount
                            localized
                        }
                        costPrice {
                            currency
                            amount
                            localized
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
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    price_override = 1.32
    cost_price = 3.22
    weight = 10.22
    variant_slug = product_type.variant_attributes.first().slug
    variant_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"
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
        "costPrice": cost_price,
        "priceOverride": price_override,
        "weight": weight,
        "attributes": [{"id": variant_id, "values": [variant_value]}],
        "trackInventory": True,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)["data"]["productVariantCreate"]
    assert not content["productErrors"]
    data = content["productVariant"]
    assert data["name"] == variant_value
    assert data["costPrice"]["amount"] == cost_price
    assert data["priceOverride"]["amount"] == price_override
    assert data["sku"] == sku
    assert data["attributes"][0]["attribute"]["slug"] == variant_slug
    assert data["attributes"][0]["values"][0]["slug"] == variant_value
    assert data["weight"]["unit"] == "kg"
    assert data["weight"]["value"] == weight
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["quantity"] == stocks[0]["quantity"]
    assert data["stocks"][0]["warehouse"]["slug"] == warehouse.slug


def test_create_product_variant_with_negative_weight(
    staff_api_client, product, product_type, permission_manage_products
):
    query = """
        mutation createVariant (
            $productId: ID!,
            $attributes: [AttributeValueInput]!,
            $weight: WeightScalar) {
                productVariantCreate(
                    input: {
                        product: $productId,
                        attributes: $attributes,
                        weight: $weight
                    }) {
                    productErrors {
                        field
                        code
                        message
                    }
                }
            }
    """
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variant_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"

    variables = {
        "productId": product_id,
        "weight": -1,
        "attributes": [{"id": variant_id, "values": [variant_value]}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantCreate"]
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_create_product_variant_not_all_attributes(
    staff_api_client, product, product_type, color_attribute, permission_manage_products
):
    query = """
            mutation createVariant (
                $productId: ID!,
                $sku: String!,
                $attributes: [AttributeValueInput]!) {
                    productVariantCreate(
                        input: {
                            product: $productId,
                            sku: $sku,
                            attributes: $attributes
                        }) {
                        productErrors {
                            field
                            code
                            message
                        }
                    }
                }

        """
    product_id = graphene.Node.to_global_id("Product", product.pk)
    sku = "1"
    variant_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"
    product_type.variant_attributes.add(color_attribute)

    variables = {
        "productId": product_id,
        "sku": sku,
        "attributes": [{"id": variant_id, "values": [variant_value]}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productVariantCreate"]["productErrors"]
    assert content["data"]["productVariantCreate"]["productErrors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.REQUIRED.name,
        "message": ANY,
    }
    assert not product.variants.filter(sku=sku).exists()


def test_create_product_variant_duplicated_attributes(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    query = """
        mutation createVariant (
            $productId: ID!,
            $sku: String!,
            $attributes: [AttributeValueInput]!
        ) {
            productVariantCreate(
                input: {
                    product: $productId,
                    sku: $sku,
                    attributes: $attributes
                }) {
                productErrors {
                    field
                    code
                    message
                }
            }
        }
    """
    product = product_with_variant_with_two_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    sku = str(uuid4())[:12]
    variables = {
        "productId": product_id,
        "sku": sku,
        "attributes": [
            {"id": color_attribute_id, "values": ["red"]},
            {"id": size_attribute_id, "values": ["small"]},
        ],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productVariantCreate"]["productErrors"]
    assert content["data"]["productVariantCreate"]["productErrors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.DUPLICATED_INPUT_ITEM.name,
        "message": ANY,
    }
    assert not product.variants.filter(sku=sku).exists()


def test_create_product_variant_update_with_new_attributes(
    staff_api_client, permission_manage_products, product, size_attribute
):
    query = """
        mutation VariantUpdate(
          $id: ID!
          $attributes: [AttributeValueInput]
          $costPrice: Decimal
          $priceOverride: Decimal
          $sku: String
          $trackInventory: Boolean!
        ) {
          productVariantUpdate(
            id: $id
            input: {
              attributes: $attributes
              costPrice: $costPrice
              priceOverride: $priceOverride
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
                  values {
                    id
                    name
                    slug
                    __typename
                  }
                  __typename
                }
                __typename
              }
            }
          }
        }
    """

    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    variant_id = graphene.Node.to_global_id(
        "ProductVariant", product.variants.first().pk
    )

    variables = {
        "attributes": [{"id": size_attribute_id, "values": ["XXXL"]}],
        "costPrice": 10,
        "id": variant_id,
        "priceOverride": 0,
        "sku": "21599567",
        "trackInventory": True,
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_products]
        )
    )["data"]["productVariantUpdate"]
    assert not data["errors"]
    assert data["productVariant"]["id"] == variant_id

    attributes = data["productVariant"]["attributes"]
    assert len(attributes) == 1
    assert attributes[0]["attribute"]["id"] == size_attribute_id


def test_update_product_variant(staff_api_client, product, permission_manage_products):
    query = """
        mutation updateVariant (
            $id: ID!,
            $sku: String!,
            $costPrice: Decimal,
            $trackInventory: Boolean!) {
                productVariantUpdate(
                    id: $id,
                    input: {
                        sku: $sku,
                        costPrice: $costPrice,
                        trackInventory: $trackInventory
                    }) {
                    productVariant {
                        name
                        sku
                        costPrice {
                            currency
                            amount
                            localized
                        }
                    }
                }
            }

    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "test sku"
    cost_price = 3.3

    variables = {
        "id": variant_id,
        "sku": sku,
        "costPrice": cost_price,
        "trackInventory": True,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]
    assert data["name"] == variant.name
    assert data["costPrice"]["amount"] == cost_price
    assert data["sku"] == sku


def test_update_product_variant_with_negative_weight(
    staff_api_client, product, permission_manage_products
):
    query = """
        mutation updateVariant (
            $id: ID!,
            $weight: WeightScalar
        ) {
            productVariantUpdate(
                id: $id,
                input: {
                    weight: $weight
                }
            ){
                productVariant {
                    name
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {"id": variant_id, "weight": -1}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


@pytest.mark.parametrize("field", ("cost_price", "price_override"))
def test_update_product_variant_unset_amounts(
    staff_api_client, product, permission_manage_products, field
):
    """Ensure setting nullable amounts to null is properly handled
    (setting the amount to none) and doesn't override the currency.
    """
    query = """
        mutation updateVariant (
            $id: ID!,
            $sku: String!,
            $costPrice: Decimal,
            $priceOverride: Decimal) {
                productVariantUpdate(
                    id: $id,
                    input: {
                        sku: $sku,
                        costPrice: $costPrice,
                        priceOverride: $priceOverride
                    }) {
                    productVariant {
                        name
                        sku
                        costPrice {
                            currency
                            amount
                            localized
                        }
                        priceOverride {
                            currency
                            amount
                            localized
                        }
                    }
                }
            }

    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = variant.sku

    camel_case_field_name = to_camel_case(field)

    variables = {"id": variant_id, "sku": sku, camel_case_field_name: None}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()

    assert variant.currency is not None
    assert getattr(variant, field) is None

    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]["productVariant"]
    assert data[camel_case_field_name] is None


QUERY_UPDATE_VARIANT_ATTRIBUTES = """
    mutation updateVariant (
        $id: ID!,
        $sku: String,
        $attributes: [AttributeValueInput]!) {
            productVariantUpdate(
                id: $id,
                input: {
                    sku: $sku,
                    attributes: $attributes
                }) {
                errors {
                    field
                    message
                }
                productErrors {
                    field
                    code
                }
            }
        }
"""


def test_update_product_variant_not_all_attributes(
    staff_api_client, product, product_type, color_attribute, permission_manage_products
):
    """Ensures updating a variant with missing attributes (all attributes must
    be provided) raises an error. We expect the color attribute
    to be flagged as missing."""

    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    sku = "test sku"
    attr_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().id
    )
    variant_value = "test-value"
    product_type.variant_attributes.add(color_attribute)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [{"id": attr_id, "values": [variant_value]}],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    assert len(content["data"]["productVariantUpdate"]["errors"]) == 1
    assert content["data"]["productVariantUpdate"]["errors"][0] == {
        "field": "attributes",
        "message": "All attributes must take a value",
    }
    assert not product.variants.filter(sku=sku).exists()


def test_update_product_variant_with_current_attribut(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku
    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": color_attribute_id, "values": ["red"]},
            {"id": size_attribute_id, "values": ["small"]},
        ],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant.refresh_from_db()
    assert variant.sku == sku
    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"


def test_update_product_variant_with_new_attribute(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()
    sku = str(uuid4())[:12]
    assert not variant.sku == sku
    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    variables = {
        "id": variant_id,
        "sku": sku,
        "attributes": [
            {"id": color_attribute_id, "values": ["red"]},
            {"id": size_attribute_id, "values": ["big"]},
        ],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert not data["errors"]
    variant.refresh_from_db()
    assert variant.sku == sku
    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "big"


def test_update_product_variant_with_duplicated_attribute(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
    product = product_with_variant_with_two_attributes
    variant = product.variants.first()
    variant2 = product.variants.first()

    variant2.pk = None
    variant2.sku = str(uuid4())[:12]
    variant2.save()
    associate_attribute_values_to_instance(
        variant2, color_attribute, color_attribute.values.last()
    )
    associate_attribute_values_to_instance(
        variant2, size_attribute, size_attribute.values.last()
    )

    assert variant.attributes.first().values.first().slug == "red"
    assert variant.attributes.last().values.first().slug == "small"
    assert variant2.attributes.first().values.first().slug == "blue"
    assert variant2.attributes.last().values.first().slug == "big"

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)

    variables = {
        "id": variant_id,
        "attributes": [
            {"id": color_attribute_id, "values": ["blue"]},
            {"id": size_attribute_id, "values": ["big"]},
        ],
    }

    response = staff_api_client.post_graphql(
        QUERY_UPDATE_VARIANT_ATTRIBUTES,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    data = content["data"]["productVariantUpdate"]
    assert data["productErrors"][0] == {
        "field": "attributes",
        "code": ProductErrorCode.DUPLICATED_INPUT_ITEM.name,
    }


@pytest.mark.parametrize(
    "values, message",
    (
        ([], "size expects a value but none were given"),
        (["one", "two"], "A variant attribute cannot take more than one value"),
        (["   "], "Attribute values cannot be blank"),
    ),
)
def test_update_product_variant_requires_values(
    staff_api_client, variant, product_type, permission_manage_products, values, message
):
    """Ensures updating a variant with invalid values raise an error.

    - No values
    - Blank value
    - More than one value
    """

    sku = "updated"

    query = QUERY_UPDATE_VARIANT_ATTRIBUTES
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    attr_id = graphene.Node.to_global_id(
        "Attribute", product_type.variant_attributes.first().id
    )

    variables = {
        "id": variant_id,
        "attributes": [{"id": attr_id, "values": values}],
        "sku": sku,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    variant.refresh_from_db()
    content = get_graphql_content(response)
    assert (
        len(content["data"]["productVariantUpdate"]["errors"]) == 1
    ), f"expected: {message}"
    assert content["data"]["productVariantUpdate"]["errors"][0] == {
        "field": "attributes",
        "message": message,
    }
    assert not variant.product.variants.filter(sku=sku).exists()


def test_delete_variant(staff_api_client, product, permission_manage_products):
    query = """
        mutation variantDelete($id: ID!) {
            productVariantDelete(id: $id) {
                productVariant {
                    sku
                    id
                }
              }
            }
    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()


def _fetch_all_variants(client, permissions=None):
    query = """
        query fetchAllVariants {
            productVariants(first: 10) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    response = client.post_graphql(
        query, {}, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["productVariants"]


def test_fetch_all_variants_staff_user(
    staff_api_client, unavailable_product_with_variant, permission_manage_products
):
    data = _fetch_all_variants(
        staff_api_client, permissions=[permission_manage_products]
    )
    variant = unavailable_product_with_variant.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert data["totalCount"] == 1
    assert data["edges"][0]["node"]["id"] == variant_id


def test_fetch_all_variants_customer(user_api_client, unavailable_product_with_variant):
    data = _fetch_all_variants(user_api_client)
    assert data["totalCount"] == 0


def test_fetch_all_variants_anonymous_user(
    api_client, unavailable_product_with_variant
):
    data = _fetch_all_variants(api_client)
    assert data["totalCount"] == 0


def _fetch_variant(client, variant, permissions=None):
    query = """
    query ProductVariantDetails($variantId: ID!) {
        productVariant(id: $variantId) {
            id
            product {
                id
            }
        }
    }
    """
    variables = {"variantId": graphene.Node.to_global_id("ProductVariant", variant.id)}
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["productVariant"]


def test_fetch_unpublished_variant_staff_user(
    staff_api_client, unavailable_product_with_variant, permission_manage_products
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(
        staff_api_client, variant, permissions=[permission_manage_products]
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id(
        "Product", unavailable_product_with_variant.pk
    )

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


def test_fetch_unpublished_variant_customer(
    user_api_client, unavailable_product_with_variant
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(user_api_client, variant)
    assert data is None


def test_fetch_unpublished_variant_anonymous_user(
    api_client, unavailable_product_with_variant
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(api_client, variant)
    assert data is None


PRODUCT_VARIANT_BULK_CREATE_MUTATION = """
    mutation ProductVariantBulkCreate(
        $variants: [ProductVariantBulkCreateInput]!, $productId: ID!
    ) {
        productVariantBulkCreate(variants: $variants, product: $productId) {
            bulkProductErrors {
                field
                message
                code
                index
                warehouses
            }
            productVariants{
                id
                sku
                stocks {
                    warehouse {
                        slug
                    }
                    quantity
                }
            }
            count
        }
    }
"""


def test_product_variant_bulk_create_by_attribute_id(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    attribute_value_count = size_attribute.values.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribut_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "costPrice": None,
            "priceOverride": None,
            "weight": 2.5,
            "trackInventory": True,
            "attributes": [{"id": attribut_id, "values": [attribute_value.name]}],
        }
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["bulkProductErrors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()
    assert attribute_value_count == size_attribute.values.count()
    product_variant = ProductVariant.objects.get(sku=sku)
    assert not product_variant.cost_price
    assert not product_variant.price_override


@pytest.mark.parametrize(
    "price_field", ("priceOverride", "costPrice",),
)
def test_product_variant_bulk_create_by_attribute_id_with_invalid_price(
    staff_api_client, product, size_attribute, permission_manage_products, price_field
):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribut_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    sku = str(uuid4())[:12]
    variant = {
        "sku": sku,
        "weight": 2.5,
        "trackInventory": True,
        "attributes": [{"id": attribut_id, "values": [attribute_value.name]}],
    }
    variant[price_field] = "-1"

    variables = {"productId": product_id, "variants": [variant]}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert data["bulkProductErrors"][0]["field"] == price_field
    assert data["bulkProductErrors"][0]["code"] == ProductErrorCode.INVALID.name


def test_product_variant_bulk_create_empty_attribute(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variants = [{"sku": str(uuid4())[:12], "attributes": []}]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["bulkProductErrors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()


def test_product_variant_bulk_create_with_new_attribute_value(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    attribute_value_count = size_attribute.values.count()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value = size_attribute.values.last()
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-attribute"]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["bulkProductErrors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()


def test_product_variant_bulk_create_stocks_input(
    staff_api_client, product, permission_manage_products, warehouses, size_attribute
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_value_count = size_attribute.values.count()
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    variants = [
        {
            "sku": str(uuid4())[:12],
            "stocks": [
                {
                    "quantity": 10,
                    "warehouse": graphene.Node.to_global_id(
                        "Warehouse", warehouses[0].pk
                    ),
                }
            ],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-attribute"]}],
            "stocks": [
                {
                    "quantity": 15,
                    "warehouse": graphene.Node.to_global_id(
                        "Warehouse", warehouses[0].pk
                    ),
                },
                {
                    "quantity": 15,
                    "warehouse": graphene.Node.to_global_id(
                        "Warehouse", warehouses[1].pk
                    ),
                },
            ],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["bulkProductErrors"]
    assert data["count"] == 2
    assert product_variant_count + 2 == ProductVariant.objects.count()
    assert attribute_value_count + 1 == size_attribute.values.count()

    expected_result = [
        {
            "sku": variants[0]["sku"],
            "stocks": [
                {
                    "warehouse": {"slug": warehouses[0].slug},
                    "quantity": variants[0]["stocks"][0]["quantity"],
                }
            ],
        },
        {
            "sku": variants[1]["sku"],
            "stocks": [
                {
                    "warehouse": {"slug": warehouses[0].slug},
                    "quantity": variants[1]["stocks"][0]["quantity"],
                },
                {
                    "warehouse": {"slug": warehouses[1].slug},
                    "quantity": variants[1]["stocks"][1]["quantity"],
                },
            ],
        },
    ]
    for variant_data in data["productVariants"]:
        variant_data.pop("id")
        assert variant_data in expected_result


def test_product_variant_bulk_create_duplicated_warehouses(
    staff_api_client, product, permission_manage_products, warehouses, size_attribute
):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    attribute_value = size_attribute.values.last()
    warehouse1_id = graphene.Node.to_global_id("Warehouse", warehouses[0].pk)
    variants = [
        {
            "sku": str(uuid4())[:12],
            "stocks": [
                {
                    "quantity": 10,
                    "warehouse": graphene.Node.to_global_id(
                        "Warehouse", warehouses[1].pk
                    ),
                }
            ],
            "attributes": [{"id": size_attribute_id, "values": [attribute_value.name]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-attribute"]}],
            "stocks": [
                {"quantity": 15, "warehouse": warehouse1_id},
                {"quantity": 15, "warehouse": warehouse1_id},
            ],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    errors = data["bulkProductErrors"]

    assert not data["productVariants"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "stocks"
    assert error["index"] == 1
    assert error["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["warehouses"] == [warehouse1_id]


def test_product_variant_bulk_create_duplicated_sku(
    staff_api_client,
    product,
    product_with_default_variant,
    size_attribute,
    permission_manage_products,
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    sku = product.variants.first().sku
    sku2 = product_with_default_variant.variants.first().sku
    assert not sku == sku2
    variants = [
        {
            "sku": sku,
            "attributes": [{"id": size_attribute_id, "values": ["Test-value"]}],
        },
        {
            "sku": sku2,
            "attributes": [{"id": size_attribute_id, "values": ["Test-valuee"]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["bulkProductErrors"]) == 2
    errors = data["bulkProductErrors"]
    for index, error in enumerate(errors):
        assert error["field"] == "sku"
        assert error["code"] == ProductErrorCode.UNIQUE.name
        assert error["index"] == index
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_duplicated_sku_in_input(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    sku = str(uuid4())[:12]
    variants = [
        {
            "sku": sku,
            "attributes": [{"id": size_attribute_id, "values": ["Test-value"]}],
        },
        {
            "sku": sku,
            "attributes": [{"id": size_attribute_id, "values": ["Test-value2"]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["bulkProductErrors"]) == 1
    error = data["bulkProductErrors"][0]
    assert error["field"] == "sku"
    assert error["code"] == ProductErrorCode.UNIQUE.name
    assert error["index"] == 1
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_many_errors(
    staff_api_client, product, size_attribute, permission_manage_products
):
    product_variant_count = ProductVariant.objects.count()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.pk)
    non_existent_attribute_pk = 0
    invalid_attribute_id = graphene.Node.to_global_id(
        "Attribute", non_existent_attribute_pk
    )
    sku = product.variants.first().sku
    variants = [
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-value1"]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": size_attribute_id, "values": ["Test-value4"]}],
        },
        {
            "sku": sku,
            "attributes": [{"id": size_attribute_id, "values": ["Test-value2"]}],
        },
        {
            "sku": str(uuid4())[:12],
            "attributes": [{"id": invalid_attribute_id, "values": ["Test-value3"]}],
        },
    ]

    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["bulkProductErrors"]) == 2
    errors = data["bulkProductErrors"]
    expected_errors = [
        {
            "field": "sku",
            "index": 2,
            "code": ProductErrorCode.UNIQUE.name,
            "message": ANY,
            "warehouses": None,
        },
        {
            "field": "attributes",
            "index": 3,
            "code": ProductErrorCode.NOT_FOUND.name,
            "message": ANY,
            "warehouses": None,
        },
    ]
    for expected_error in expected_errors:
        assert expected_error in errors
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_two_variants_duplicated_attribute_value(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
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
                {"id": size_attribute_id, "values": ["small"]},
            ],
        }
    ]
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["bulkProductErrors"]) == 1
    error = data["bulkProductErrors"][0]
    assert error["field"] == "attributes"
    assert error["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["index"] == 0
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_two_variants_duplicated_attribute_value_in_input(
    staff_api_client,
    product_with_variant_with_two_attributes,
    permission_manage_products,
    color_attribute,
    size_attribute,
):
    product = product_with_variant_with_two_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product_variant_count = ProductVariant.objects.count()
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    size_attribute_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    attributes = [
        {"id": color_attribute_id, "values": [color_attribute.values.last().slug]},
        {"id": size_attribute_id, "values": [size_attribute.values.last().slug]},
    ]
    variants = [
        {"sku": str(uuid4())[:12], "attributes": attributes},
        {"sku": str(uuid4())[:12], "attributes": attributes},
    ]
    variables = {"productId": product_id, "variants": variants}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert len(data["bulkProductErrors"]) == 1
    error = data["bulkProductErrors"][0]
    assert error["field"] == "attributes"
    assert error["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert error["index"] == 1
    assert product_variant_count == ProductVariant.objects.count()


def test_product_variant_bulk_create_two_variants_duplicated_one_attribute_value(
    staff_api_client,
    product_with_variant_with_two_attributes,
    color_attribute,
    size_attribute,
    permission_manage_products,
):
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
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_BULK_CREATE_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantBulkCreate"]
    assert not data["bulkProductErrors"]
    assert data["count"] == 1
    assert product_variant_count + 1 == ProductVariant.objects.count()


VARIANT_STOCKS_CREATE_MUTATION = """
    mutation ProductVariantStocksCreate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksCreate(variantId: $variantId, stocks: $stocks){
            productVariant{
                id
                stocks {
                    quantity
                    quantityAllocated
                    id
                    warehouse{
                        slug
                    }
                }
            }
            bulkStockErrors{
                code
                field
                message
                index
            }
        }
    }
"""


def test_variant_stocks_create(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]

    expected_result = [
        {
            "quantity": stocks[0]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": warehouse.slug},
        },
        {
            "quantity": stocks[1]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": second_warehouse.slug},
        },
    ]
    assert not data["bulkStockErrors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)
    result = []
    for stock in data["productVariant"]["stocks"]:
        stock.pop("id")
        result.append(stock)
    for res in result:
        assert res in expected_result


def test_variant_stocks_create_empty_stock_input(
    staff_api_client, variant, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {"variantId": variant_id, "stocks": []}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]

    assert not data["bulkStockErrors"]
    assert len(data["productVariant"]["stocks"]) == variant.stocks.count()
    assert data["productVariant"]["id"] == variant_id


def test_variant_stocks_create_stock_already_exists(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["bulkStockErrors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 0


def test_variant_stocks_create_stock_duplicated_warehouse(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    second_warehouse_id = graphene.Node.to_global_id("Warehouse", second_warehouse.id)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {"warehouse": second_warehouse_id, "quantity": 100},
        {"warehouse": second_warehouse_id, "quantity": 120},
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["bulkStockErrors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 2


def test_variant_stocks_create_stock_duplicated_warehouse_and_warehouse_already_exists(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    second_warehouse_id = graphene.Node.to_global_id("Warehouse", second_warehouse.id)
    Stock.objects.create(
        product_variant=variant, warehouse=second_warehouse, quantity=10
    )

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {"warehouse": second_warehouse_id, "quantity": 100},
        {"warehouse": second_warehouse_id, "quantity": 120},
    ]

    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksCreate"]
    errors = data["bulkStockErrors"]

    assert len(errors) == 3
    assert {error["code"] for error in errors} == {
        StockErrorCode.UNIQUE.name,
    }
    assert {error["field"] for error in errors} == {
        "warehouse",
    }
    assert {error["index"] for error in errors} == {1, 2}


VARIANT_STOCKS_UPDATE_MUTATIONS = """
    mutation ProductVariantStocksUpdate($variantId: ID!, $stocks: [StockInput!]!){
        productVariantStocksUpdate(variantId: $variantId, stocks: $stocks){
            productVariant{
                stocks{
                    quantity
                    quantityAllocated
                    id
                    warehouse{
                        slug
                    }
                }
            }
            bulkStockErrors{
                code
                field
                message
                index
            }
        }
    }
"""


def test_product_variant_stocks_update(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.id),
            "quantity": 100,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]

    expected_result = [
        {
            "quantity": stocks[0]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": warehouse.slug},
        },
        {
            "quantity": stocks[1]["quantity"],
            "quantityAllocated": 0,
            "warehouse": {"slug": second_warehouse.slug},
        },
    ]
    assert not data["bulkStockErrors"]
    assert len(data["productVariant"]["stocks"]) == len(stocks)
    result = []
    for stock in data["productVariant"]["stocks"]:
        stock.pop("id")
        result.append(stock)
    for res in result:
        assert res in expected_result


def test_variant_stocks_update_stock_duplicated_warehouse(
    staff_api_client, variant, warehouse, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", second_warehouse.pk),
            "quantity": 100,
        },
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 150,
        },
    ]
    variables = {"variantId": variant_id, "stocks": stocks}
    response = staff_api_client.post_graphql(
        VARIANT_STOCKS_UPDATE_MUTATIONS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantStocksUpdate"]
    errors = data["bulkStockErrors"]

    assert errors
    assert errors[0]["code"] == StockErrorCode.UNIQUE.name
    assert errors[0]["field"] == "warehouse"
    assert errors[0]["index"] == 2


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
            stockErrors{
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
    assert not data["stockErrors"]
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
    assert not data["stockErrors"]
    assert (
        len(data["productVariant"]["stocks"]) == variant.stocks.count() == stocks_count
    )
    assert data["productVariant"]["stocks"][0]["quantity"] == 10
    assert data["productVariant"]["stocks"][0]["warehouse"]["slug"] == warehouse.slug
