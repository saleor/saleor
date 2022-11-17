from unittest.mock import ANY

import graphene
import pytest

from .....attribute import AttributeType
from .....product.error_codes import ProductErrorCode
from .....product.models import ProductType
from ....tests.utils import get_graphql_content
from ...enums import ProductTypeKindEnum

PRODUCT_TYPE_CREATE_MUTATION = """
    mutation createProductType(
        $name: String,
        $slug: String,
        $kind: ProductTypeKindEnum,
        $taxClass: ID,
        $taxCode: String,
        $hasVariants: Boolean,
        $isShippingRequired: Boolean,
        $productAttributes: [ID!],
        $variantAttributes: [ID!],
        $weight: WeightScalar) {
        productTypeCreate(
            input: {
                name: $name,
                slug: $slug,
                kind: $kind,
                taxClass: $taxClass,
                taxCode: $taxCode,
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                productAttributes: $productAttributes,
                variantAttributes: $variantAttributes,
                weight: $weight}) {
            productType {
                name
                slug
                kind
                isShippingRequired
                hasVariants
                variantAttributes {
                    name
                    choices(first: 10) {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                }
                productAttributes {
                    name
                    choices(first: 10) {
                        edges {
                            node {
                                name
                                richText
                                plainText
                                boolean
                                date
                                dateTime
                            }
                        }

                    }
                }
                taxClass {
                    id
                }
            }
            errors {
                field
                message
                code
                attributes
            }
        }

    }
"""


def test_product_type_create_mutation(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    monkeypatch,
    tax_classes,
):

    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    kind = ProductTypeKindEnum.NORMAL.name
    has_variants = True
    require_shipping = True
    product_attributes = product_type.product_attributes.all()
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]
    tax_class_id = graphene.Node.to_global_id("TaxClass", tax_classes[0].pk)

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": kind,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
        "variantAttributes": variant_attributes_ids,
        "taxClass": tax_class_id,
    }
    initial_count = ProductType.objects.count()
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    assert ProductType.objects.count() == initial_count + 1
    data = content["data"]["productTypeCreate"]["productType"]
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["kind"] == kind
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping

    pa = product_attributes[0]
    assert data["productAttributes"][0]["name"] == pa.name
    pa_values = data["productAttributes"][0]["choices"]["edges"]
    assert sorted([value["node"]["name"] for value in pa_values]) == sorted(
        [value.name for value in pa.values.all()]
    )

    va = variant_attributes[0]
    assert data["variantAttributes"][0]["name"] == va.name
    va_values = data["variantAttributes"][0]["choices"]["edges"]
    assert sorted([value["node"]["name"] for value in va_values]) == sorted(
        [value.name for value in va.values.all()]
    )


def test_product_type_create_mutation_optional_kind(
    staff_api_client, permission_manage_product_types_and_attributes
):
    variables = {"name": "Default Kind Test"}
    response = staff_api_client.post_graphql(
        PRODUCT_TYPE_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    assert (
        content["data"]["productTypeCreate"]["productType"]["kind"]
        == ProductTypeKindEnum.NORMAL.name
    )


def test_create_gift_card_product_type(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    monkeypatch,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    kind = ProductTypeKindEnum.GIFT_CARD.name
    has_variants = True
    require_shipping = True
    product_attributes = product_type.product_attributes.all()
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": kind,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
        "variantAttributes": variant_attributes_ids,
    }
    initial_count = ProductType.objects.count()
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    assert ProductType.objects.count() == initial_count + 1
    data = content["data"]["productTypeCreate"]["productType"]
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["kind"] == kind
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping

    pa = product_attributes[0]
    assert data["productAttributes"][0]["name"] == pa.name
    pa_values = data["productAttributes"][0]["choices"]["edges"]
    assert sorted([value["node"]["name"] for value in pa_values]) == sorted(
        [value.name for value in pa.values.all()]
    )

    va = variant_attributes[0]
    assert data["variantAttributes"][0]["name"] == va.name
    va_values = data["variantAttributes"][0]["choices"]["edges"]
    assert sorted([value["node"]["name"] for value in va_values]) == sorted(
        [value.name for value in va.values.all()]
    )


def test_create_product_type_with_rich_text_attribute(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    rich_text_attribute,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"

    product_type.product_attributes.add(rich_text_attribute)
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", attr.id)
        for attr in product_type.product_attributes.all()
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": ProductTypeKindEnum.NORMAL.name,
        "productAttributes": product_attributes_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]["productType"]
    errors = content["data"]["productTypeCreate"]["errors"]

    assert not errors
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    expected_attributes = [
        {
            "name": "Color",
            "choices": {
                "edges": [
                    {
                        "node": {
                            "name": "Red",
                            "richText": None,
                            "plainText": None,
                            "boolean": None,
                            "date": None,
                            "dateTime": None,
                        }
                    },
                    {
                        "node": {
                            "name": "Blue",
                            "richText": None,
                            "plainText": None,
                            "boolean": None,
                            "date": None,
                            "dateTime": None,
                        }
                    },
                ]
            },
        },
        {
            "name": "Text",
            "choices": {"edges": []},
        },
    ]
    for attribute in data["productAttributes"]:
        assert attribute in expected_attributes


def test_create_product_type_with_plain_text_attribute(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    plain_text_attribute,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"

    product_type.product_attributes.add(plain_text_attribute)
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", attr.id)
        for attr in product_type.product_attributes.all()
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": ProductTypeKindEnum.NORMAL.name,
        "productAttributes": product_attributes_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]["productType"]
    errors = content["data"]["productTypeCreate"]["errors"]

    assert not errors
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    expected_plain_text_attribute = {
        "name": plain_text_attribute.name,
        "choices": {"edges": []},
    }
    assert expected_plain_text_attribute in data["productAttributes"]


def test_create_product_type_with_date_attribute(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    date_attribute,
    date_time_attribute,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    kind = ProductTypeKindEnum.NORMAL.name

    product_type.product_attributes.add(date_attribute)
    product_type.product_attributes.add(date_time_attribute)

    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", attr.id)
        for attr in product_type.product_attributes.all()
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": kind,
        "productAttributes": product_attributes_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]["productType"]
    errors = content["data"]["productTypeCreate"]["errors"]
    expected_attribute = [
        {"choices": {"edges": []}, "name": "Release date"},
        {"choices": {"edges": []}, "name": "Release date time"},
    ]

    assert not errors
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["kind"] == kind

    for attribute in expected_attribute:
        assert attribute in data["productAttributes"]


def test_create_product_type_with_boolean_attribute(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    boolean_attribute,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    kind = ProductTypeKindEnum.NORMAL.name

    product_type.product_attributes.add(boolean_attribute)
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", attr.id)
        for attr in product_type.product_attributes.all()
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": kind,
        "productAttributes": product_attributes_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]["productType"]
    errors = content["data"]["productTypeCreate"]["errors"]

    assert not errors
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["kind"] == kind
    assert {"choices": {"edges": []}, "name": "Boolean"} in data["productAttributes"]


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("test-slug", "test-slug"),
        (None, "test-product-type"),
        ("", "test-product-type"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ),
)
def test_create_product_type_with_given_slug(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    name = "Test product type"
    variables = {
        "name": name,
        "slug": input_slug,
        "kind": ProductTypeKindEnum.NORMAL.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    assert not data["errors"]
    assert data["productType"]["slug"] == expected_slug


def test_create_product_type_with_unicode_in_name(
    staff_api_client, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    name = "わたし わ にっぽん です"
    kind = ProductTypeKindEnum.NORMAL.name
    variables = {
        "name": name,
        "kind": kind,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    assert not data["errors"]
    assert data["productType"]["name"] == name
    assert data["productType"]["slug"] == "watasi-wa-nitupon-desu"
    assert data["productType"]["kind"] == kind


def test_create_product_type_create_with_negative_weight(
    staff_api_client, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    name = "Test product type"
    variables = {
        "name": name,
        "weight": -1.1,
        "type": ProductTypeKindEnum.NORMAL.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_product_type_create_mutation_not_valid_attributes(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    monkeypatch,
):
    # given
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    has_variants = True
    require_shipping = True

    product_attributes = product_type.product_attributes.all()
    product_page_attribute = product_attributes.last()
    product_page_attribute.type = AttributeType.PAGE_TYPE
    product_page_attribute.save(update_fields=["type"])

    variant_attributes = product_type.variant_attributes.all()
    variant_page_attribute = variant_attributes.last()
    variant_page_attribute.type = AttributeType.PAGE_TYPE
    variant_page_attribute.save(update_fields=["type"])

    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": ProductTypeKindEnum.NORMAL.name,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
        "variantAttributes": variant_attributes_ids,
    }
    initial_count = ProductType.objects.count()

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    errors = data["errors"]

    assert len(errors) == 2
    expected_errors = [
        {
            "code": ProductErrorCode.INVALID.name,
            "field": "productAttributes",
            "message": ANY,
            "attributes": [
                graphene.Node.to_global_id("Attribute", product_page_attribute.pk)
            ],
        },
        {
            "code": ProductErrorCode.INVALID.name,
            "field": "variantAttributes",
            "message": ANY,
            "attributes": [
                graphene.Node.to_global_id("Attribute", variant_page_attribute.pk)
            ],
        },
    ]
    for error in errors:
        assert error in expected_errors

    assert initial_count == ProductType.objects.count()
