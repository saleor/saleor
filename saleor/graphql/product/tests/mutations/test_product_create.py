import json
from datetime import datetime
from unittest.mock import ANY, patch

import graphene
import pytest
import pytz
from django.conf import settings
from django.utils.text import slugify
from freezegun import freeze_time

from .....core.taxes import TaxType
from .....graphql.core.enums import AttributeErrorCode
from .....graphql.tests.utils import (
    get_graphql_content,
    get_graphql_content_from_response,
)
from .....plugins.manager import PluginsManager
from .....product.error_codes import ProductErrorCode
from .....product.models import Product
from .....tests.utils import dummy_editorjs

CREATE_PRODUCT_MUTATION = """
       mutation createProduct(
           $input: ProductCreateInput!
       ) {
                productCreate(
                    input: $input) {
                        product {
                            id
                            category {
                                name
                            }
                            description
                            chargeTaxes
                            taxClass {
                                id
                            }
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
                            metadata {
                                key
                                value
                            }
                            privateMetadata {
                                key
                                value
                            }
                            attributes {
                                attribute {
                                    slug
                                }
                                values {
                                    slug
                                    name
                                    reference
                                    richText
                                    plainText
                                    boolean
                                    dateTime
                                    date
                                    file {
                                        url
                                        contentType
                                    }
                                }
                            }
                            externalReference
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


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_created")
def test_create_product(
    created_webhook_mock,
    updated_webhook_mock,
    staff_api_client,
    product_type,
    category,
    size_attribute,
    description_json,
    permission_manage_products,
    monkeypatch,
    tax_classes,
):
    # given

    description_json = json.dumps(description_json)
    metadata_key = "md key"
    metadata_value = "md value"
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"
    tax_class_id = graphene.Node.to_global_id("TaxClass", tax_classes[0].pk)
    external_reference = "test-ext-ref"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name="Color")
    color_value_slug = color_attr.values.first().slug
    color_value_name = color_attr.values.first().name
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
            "taxClass": tax_class_id,
            "taxCode": product_tax_rate,
            "attributes": [
                {"id": color_attr_id, "values": [color_value_name]},
                {"id": size_attr_id, "values": [non_existent_attr_value]},
            ],
            "metadata": [{"key": metadata_key, "value": metadata_value}],
            "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
            "externalReference": external_reference,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PRODUCT_MUTATION, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]

    # then
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["description"] == description_json
    assert data["product"]["chargeTaxes"] == product_charge_taxes
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert data["product"]["taxClass"]["id"] == tax_class_id
    assert data["product"]["externalReference"] == external_reference
    values = (
        data["product"]["attributes"][0]["values"][0]["slug"],
        data["product"]["attributes"][1]["values"][0]["slug"],
    )
    assert slugify(non_existent_attr_value) in values
    assert color_value_slug in values

    product = Product.objects.first()
    assert product.metadata == {metadata_key: metadata_value}
    assert product.private_metadata == {metadata_key: metadata_value}

    created_webhook_mock.assert_called_once_with(product)
    updated_webhook_mock.assert_not_called()


def test_create_product_use_tax_class_from_product_type(
    staff_api_client,
    product_type,
    permission_manage_products,
    default_tax_class,
    tax_classes,
):
    # given
    default_tax_class_id = graphene.Node.to_global_id("TaxClass", default_tax_class.pk)
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    variables = {
        "input": {
            "productType": product_type_id,
            "name": "Test Empty Tax Class",
            "slug": "test-empty-tax-class",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PRODUCT_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["taxClass"]["id"] == default_tax_class_id


def test_create_product_description_plaintext(
    staff_api_client,
    product_type,
    category,
    size_attribute,
    permission_manage_products,
    monkeypatch,
):
    query = CREATE_PRODUCT_MUTATION
    description = "some test description"
    description_json = dummy_editorjs(description, json_format=True)

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

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert not data["errors"]

    product = Product.objects.all().first()
    assert product.description_plaintext == description


def test_create_product_with_rich_text_attribute(
    staff_api_client,
    product_type,
    category,
    rich_text_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(rich_text_attribute)
    rich_text_attribute_id = graphene.Node.to_global_id(
        "Attribute", rich_text_attribute.id
    )
    rich_text_value = dummy_editorjs("test product" * 5)
    rich_text = json.dumps(rich_text_value)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [
                {
                    "id": rich_text_attribute_id,
                    "richText": rich_text,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])

    expected_attributes_data = [
        {"attribute": {"slug": "color"}, "values": []},
        {
            "attribute": {"slug": "text"},
            "values": [
                {
                    "slug": f"{product_id}_{rich_text_attribute.id}",
                    "name": (
                        "test producttest producttest producttest producttest product"
                    ),
                    "reference": None,
                    "richText": rich_text,
                    "plainText": None,
                    "file": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
    ]

    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data


def test_create_product_no_value_for_rich_text_attribute(
    staff_api_client,
    product_type,
    rich_text_attribute,
    permission_manage_products,
):
    """Ensure mutation not fail when as attributes input only rich text attribute id
    is provided."""
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(rich_text_attribute)
    rich_text_attribute_id = graphene.Node.to_global_id(
        "Attribute", rich_text_attribute.id
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": rich_text_attribute_id,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    expected_attributes_data = {
        "attribute": {"slug": rich_text_attribute.slug},
        "values": [],
    }
    assert expected_attributes_data in data["product"]["attributes"]


def test_create_product_with_plain_text_attribute(
    staff_api_client,
    product_type,
    category,
    plain_text_attribute,
    color_attribute,
    permission_manage_products,
):
    # given
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(plain_text_attribute)
    plain_text_attribute_id = graphene.Node.to_global_id(
        "Attribute", plain_text_attribute.id
    )
    text_value = "test product" * 5

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [
                {
                    "id": plain_text_attribute_id,
                    "plainText": text_value,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])

    expected_attributes_data = [
        {"attribute": {"slug": "color"}, "values": []},
        {
            "attribute": {"slug": plain_text_attribute.slug},
            "values": [
                {
                    "slug": f"{product_id}_{plain_text_attribute.id}",
                    "name": text_value,
                    "reference": None,
                    "richText": None,
                    "plainText": text_value,
                    "file": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
    ]

    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data


def test_create_product_no_value_for_plain_text_attribute(
    staff_api_client,
    product_type,
    plain_text_attribute,
    permission_manage_products,
):
    # given
    """Ensure mutation not fail when as attributes input only plain text attribute id
    is provided."""
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(plain_text_attribute)
    plain_text_attribute_id = graphene.Node.to_global_id(
        "Attribute", plain_text_attribute.id
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": plain_text_attribute_id,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    expected_attributes_data = {
        "attribute": {"slug": plain_text_attribute.slug},
        "values": [],
    }
    assert expected_attributes_data in data["product"]["attributes"]


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_create_product_with_date_time_attribute(
    staff_api_client,
    product_type,
    date_time_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(date_time_attribute)
    date_time_attribute_id = graphene.Node.to_global_id(
        "Attribute", date_time_attribute.id
    )
    value = datetime.now(tz=pytz.utc)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": date_time_attribute_id,
                    "dateTime": value,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])

    expected_attributes_data = {
        "attribute": {"slug": "release-date-time"},
        "values": [
            {
                "slug": f"{product_id}_{date_time_attribute.id}",
                "name": str(value),
                "reference": None,
                "richText": None,
                "plainText": None,
                "boolean": None,
                "file": None,
                "date": None,
                "dateTime": str(value.isoformat()),
            }
        ],
    }

    assert expected_attributes_data in data["product"]["attributes"]


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_create_product_with_date_attribute(
    staff_api_client,
    product_type,
    date_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(date_attribute)
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)
    value = datetime.now(tz=pytz.utc).date()

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": date_attribute_id,
                    "date": value,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])

    expected_attributes_data = {
        "attribute": {"slug": "release-date"},
        "values": [
            {
                "slug": f"{product_id}_{date_attribute.id}",
                "name": str(value),
                "reference": None,
                "richText": None,
                "plainText": None,
                "boolean": None,
                "file": None,
                "date": str(value),
                "dateTime": None,
            }
        ],
    }

    assert expected_attributes_data in data["product"]["attributes"]


def test_create_product_no_value_for_date_attribute(
    staff_api_client,
    product_type,
    date_attribute,
    permission_manage_products,
):
    """Ensure mutation not fail when as attributes input only date attribute id
    is provided."""
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(date_attribute)
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": date_attribute_id,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    expected_attributes_data = {
        "attribute": {"slug": date_attribute.slug},
        "values": [],
    }
    assert expected_attributes_data in data["product"]["attributes"]


def test_create_product_with_boolean_attribute(
    staff_api_client,
    product_type,
    category,
    boolean_attribute,
    permission_manage_products,
    product,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(boolean_attribute)
    boolean_attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "attributes": [
                {
                    "id": boolean_attribute_id,
                    "boolean": False,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name

    expected_attributes_data = {
        "attribute": {"slug": "boolean"},
        "values": [
            {
                "slug": f"{boolean_attribute.id}_false",
                "name": "Boolean: No",
                "reference": None,
                "richText": None,
                "plainText": None,
                "boolean": False,
                "date": None,
                "dateTime": None,
                "file": None,
            }
        ],
    }
    assert expected_attributes_data in data["product"]["attributes"]


def test_create_product_no_value_for_boolean_attribute(
    staff_api_client,
    product_type,
    boolean_attribute,
    permission_manage_products,
):
    """Ensure mutation not fail when as attributes input only boolean attribute id
    is provided."""
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(boolean_attribute)
    boolean_attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": boolean_attribute_id,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    expected_attributes_data = {
        "attribute": {"slug": boolean_attribute.slug},
        "values": [],
    }
    assert expected_attributes_data in data["product"]["attributes"]


@pytest.mark.parametrize("input_slug", ["", None])
def test_create_product_no_slug_in_input(
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
    input_slug,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": input_slug,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == "test-name"
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name


def test_create_product_no_category_id(
    staff_api_client,
    product_type,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"
    input_slug = "test-slug"

    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "slug": input_slug,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == input_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"] is None


def test_create_product_with_negative_weight(
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "weight": -1,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_create_product_with_unicode_in_slug_and_name(
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "わたし-わ にっぽん です"
    slug = "わたし-わ-にっぽん-です-2"

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": slug,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    error = data["errors"]
    assert not error
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == slug


def test_create_product_invalid_product_attributes(
    staff_api_client,
    product_type,
    category,
    size_attribute,
    weight_attribute,
    description_json,
    permission_manage_products,
    monkeypatch,
):
    query = CREATE_PRODUCT_MUTATION

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

    # Add third attribute
    product_type.product_attributes.add(weight_attribute)
    weight_attr_id = graphene.Node.to_global_id("Attribute", weight_attribute.id)

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
                {"id": color_attr_id, "values": [" "]},
                {"id": weight_attr_id, "values": ["  "]},
                {
                    "id": size_attr_id,
                    "values": [non_existent_attr_value, color_value_slug],
                },
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 2

    expected_errors = [
        {
            "attributes": [color_attr_id, weight_attr_id],
            "code": ProductErrorCode.REQUIRED.name,
            "field": "attributes",
            "message": ANY,
        },
        {
            "attributes": [size_attr_id],
            "code": ProductErrorCode.INVALID.name,
            "field": "attributes",
            "message": ANY,
        },
    ]
    for error in expected_errors:
        assert error in errors


QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS = """
    mutation createProduct(
        $productTypeId: ID!,
        $categoryId: ID!
        $name: String!)
    {
        productCreate(
            input: {
                category: $categoryId,
                productType: $productTypeId,
                name: $name,
            })
        {
            product {
                id
                name
                slug
                rating
                category {
                    name
                }
                productType {
                    name
                }
            }
            errors {
                message
                field
            }
        }
    }
    """


def test_create_product_without_variants(
    staff_api_client, product_type_without_variant, category, permission_manage_products
):
    query = QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS

    product_type = product_type_without_variant
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "test-name"

    variables = {
        "productTypeId": product_type_id,
        "categoryId": category_id,
        "name": product_name,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name


def test_product_create_without_product_type(
    staff_api_client, category, permission_manage_products
):
    query = """
    mutation createProduct($categoryId: ID!) {
        productCreate(input: {
                name: "Product",
                productType: "",
                category: $categoryId}) {
            product {
                id
            }
            errors {
                message
                field
            }
        }
    }
    """

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = staff_api_client.post_graphql(
        query, {"categoryId": category_id}, permissions=[permission_manage_products]
    )
    errors = get_graphql_content(response)["data"]["productCreate"]["errors"]

    assert errors[0]["field"] == "productType"
    assert errors[0]["message"] == "This field cannot be null."


def test_product_create_with_collections_webhook(
    staff_api_client,
    permission_manage_products,
    published_collection,
    product_type,
    category,
    monkeypatch,
):
    query = """
    mutation createProduct($productTypeId: ID!, $collectionId: ID!, $categoryId: ID!) {
        productCreate(input: {
                name: "Product",
                productType: $productTypeId,
                collections: [$collectionId],
                category: $categoryId
            }) {
            product {
                id,
                collections {
                    slug
                },
                category {
                    slug
                }
            }
            errors {
                message
                field
            }
        }
    }

    """

    def assert_product_has_collections(product):
        assert product.collections.count() > 0
        assert product.collections.first() == published_collection

    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.product_created",
        lambda _, product: assert_product_has_collections(product),
    )

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)

    response = staff_api_client.post_graphql(
        query,
        {
            "productTypeId": product_type_id,
            "categoryId": category_id,
            "collectionId": collection_id,
        },
        permissions=[permission_manage_products],
    )

    get_graphql_content(response)


def test_product_create_with_invalid_json_description(staff_api_client):
    query = """
        mutation ProductCreate {
            productCreate(
                input: {
                    description: "I'm not a valid JSON"
                    category: "Q2F0ZWdvcnk6MjQ="
                    name: "Breaky McErrorface"
                    productType: "UHJvZHVjdFR5cGU6NTE="
                }
            ) {
            errors {
                field
                message
            }
        }
    }
    """

    response = staff_api_client.post_graphql(query)
    content = get_graphql_content_from_response(response)

    assert content["errors"]
    assert len(content["errors"]) == 1
    assert content["errors"][0]["extensions"]["exception"]["code"] == "GraphQLError"
    assert "is not a valid JSONString" in content["errors"][0]["message"]


@freeze_time("2020-03-18 12:00:00")
def test_create_product_with_rating(
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
    settings,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"
    expected_rating = 4.57

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "rating": expected_rating,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["rating"] == expected_rating
    assert Product.objects.get().rating == expected_rating


def test_create_product_with_file_attribute(
    staff_api_client,
    product_type,
    category,
    file_attribute,
    color_attribute,
    permission_manage_products,
    site_settings,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = file_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    existing_value = file_attribute.values.first()
    domain = site_settings.site.domain
    file_url = f"http://{domain}{settings.MEDIA_URL}{existing_value.file_url}"

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": file_attr_id, "file": file_url}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 2

    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": file_attribute.slug},
            "values": [
                {
                    "name": existing_value.name,
                    "slug": f"{existing_value.slug}-2",
                    "file": {
                        "url": file_url,
                        "contentType": None,
                    },
                    "reference": None,
                    "richText": None,
                    "plainText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count + 1


def test_create_product_with_page_reference_attribute(
    staff_api_client,
    product_type,
    category,
    color_attribute,
    product_type_page_reference_attribute,
    permission_manage_products,
    page,
):
    query = CREATE_PRODUCT_MUTATION

    values_count = product_type_page_reference_attribute.values.count()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_page_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    reference = graphene.Node.to_global_id("Page", page.pk)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": [reference]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": product_type_page_reference_attribute.slug},
            "values": [
                {
                    "slug": f"{product_id}_{page.id}",
                    "name": page.title,
                    "file": None,
                    "richText": None,
                    "plainText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                    "reference": reference,
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count + 1


def test_create_product_with_product_reference_attribute(
    staff_api_client,
    product_type,
    category,
    color_attribute,
    product_type_product_reference_attribute,
    permission_manage_products,
    product,
):
    query = CREATE_PRODUCT_MUTATION

    values_count = product_type_product_reference_attribute.values.count()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_product_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )
    reference = graphene.Node.to_global_id("Product", product.pk)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": [reference]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": product_type_product_reference_attribute.slug},
            "values": [
                {
                    "slug": f"{product_id}_{product.id}",
                    "name": product.name,
                    "file": None,
                    "richText": None,
                    "plainText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                    "reference": reference,
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count + 1


def test_create_product_with_variant_reference_attribute(
    staff_api_client,
    product_type,
    category,
    color_attribute,
    product_type_variant_reference_attribute,
    permission_manage_products,
    variant,
):
    # given
    query = CREATE_PRODUCT_MUTATION

    values_count = product_type_variant_reference_attribute.values.count()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_variant_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_variant_reference_attribute.id
    )
    reference = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": [reference]}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": product_type_variant_reference_attribute.slug},
            "values": [
                {
                    "slug": f"{product_id}_{variant.id}",
                    "name": f"{variant.product.name}: {variant.name}",
                    "file": None,
                    "richText": None,
                    "plainText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                    "reference": reference,
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    product_type_variant_reference_attribute.refresh_from_db()
    assert product_type_variant_reference_attribute.values.count() == values_count + 1


def test_create_product_with_product_reference_attribute_values_saved_in_order(
    staff_api_client,
    product_type,
    category,
    color_attribute,
    product_type_product_reference_attribute,
    permission_manage_products,
    product_list,
):
    query = CREATE_PRODUCT_MUTATION

    values_count = product_type_product_reference_attribute.values.count()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.set([product_type_product_reference_attribute])
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )
    reference_1 = graphene.Node.to_global_id("Product", product_list[0].pk)
    reference_2 = graphene.Node.to_global_id("Product", product_list[1].pk)
    reference_3 = graphene.Node.to_global_id("Product", product_list[2].pk)

    # test creating root product
    reference_ids = [reference_3, reference_1, reference_2]
    reference_instances = [product_list[2], product_list[0], product_list[1]]
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": reference_ids}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])
    expected_values = [
        {
            "slug": f"{product_id}_{product.id}",
            "name": product.name,
            "file": None,
            "richText": None,
            "plainText": None,
            "boolean": None,
            "date": None,
            "dateTime": None,
            "reference": reference,
        }
        for product, reference in zip(reference_instances, reference_ids)
    ]

    assert len(data["product"]["attributes"]) == 1
    attribute_data = data["product"]["attributes"][0]
    assert (
        attribute_data["attribute"]["slug"]
        == product_type_product_reference_attribute.slug
    )
    assert len(attribute_data["values"]) == 3
    assert attribute_data["values"] == expected_values

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count + 3


def test_create_product_with_page_reference_attribute_and_invalid_product_one(
    staff_api_client,
    product_type,
    product,
    category,
    color_attribute,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    permission_manage_products,
    page,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_page_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )

    reference = graphene.Node.to_global_id("Page", page.pk)
    invalid_reference = graphene.Node.to_global_id("Product", product.pk)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [
                {"id": reference_attr_id, "references": [reference]},
                {"id": reference_attr_id, "references": [invalid_reference]},
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"][0]["message"] == "Invalid reference type."
    assert data["errors"][0]["field"] == "attributes"
    assert data["errors"][0]["code"] == ProductErrorCode.INVALID.name


def test_create_product_with_file_attribute_new_attribute_value(
    staff_api_client,
    product_type,
    category,
    file_attribute,
    color_attribute,
    permission_manage_products,
    site_settings,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = file_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    file_name = "new_test.jpg"
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}{file_name}"

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": file_attr_id, "file": file_url}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 2
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": file_attribute.slug},
            "values": [
                {
                    "name": file_name,
                    "slug": slugify(file_name, allow_unicode=True),
                    "reference": None,
                    "richText": None,
                    "plainText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                    "file": {
                        "url": file_url,
                        "contentType": None,
                    },
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count + 1


def test_create_product_with_file_attribute_not_required_no_file_url_given(
    staff_api_client,
    product_type,
    category,
    file_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    file_attribute.value_required = False
    file_attribute.save(update_fields=["value_required"])

    # Add second attribute
    product_type.product_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": file_attr_id, "values": ["test.txt"]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 2
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {"attribute": {"slug": file_attribute.slug}, "values": []},
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    file_attribute.refresh_from_db()


def test_create_product_with_file_attribute_required_no_file_url_given(
    staff_api_client,
    product_type,
    category,
    file_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])

    # Add second attribute
    product_type.product_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": file_attr_id, "values": ["test.txt"]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    errors = data["errors"]
    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", file_attribute.pk)
    ]


def test_create_product_with_page_reference_attribute_required_no_references(
    staff_api_client,
    product_type,
    category,
    product_type_page_reference_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_page_reference_attribute.value_required = True
    product_type_page_reference_attribute.save(update_fields=["value_required"])

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_page_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": []}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    errors = data["errors"]
    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id(
            "Attribute", product_type_page_reference_attribute.pk
        )
    ]


def test_create_product_with_product_reference_attribute_required_no_references(
    staff_api_client,
    product_type,
    category,
    product_type_product_reference_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_product_reference_attribute.value_required = True
    product_type_product_reference_attribute.save(update_fields=["value_required"])

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_product_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": []}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    errors = data["errors"]
    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id(
            "Attribute", product_type_product_reference_attribute.pk
        )
    ]


def test_create_product_no_values_given(
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
    site_settings,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name="Color")
    color_attr_id = graphene.Node.to_global_id("Attribute", color_attr.id)

    file_name = "test.jpg"
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}{file_name}"

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": color_attr_id, "file": file_url}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert data["product"]["attributes"][0]["values"] == []


@pytest.mark.parametrize(
    "value, expected_name, expected_slug",
    [(20.1, "20.1", "20_1"), (20, "20", "20"), ("1", "1", "1")],
)
def test_create_product_with_numeric_attribute_new_attribute_value(
    value,
    expected_name,
    expected_slug,
    staff_api_client,
    product_type,
    category,
    numeric_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = numeric_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.set([numeric_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": [value]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    product_pk = graphene.Node.from_global_id(data["product"]["id"])[1]
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert (
        data["product"]["attributes"][0]["attribute"]["slug"] == numeric_attribute.slug
    )
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 1
    assert values[0]["name"] == expected_name
    assert values[0]["slug"] == f"{product_pk}_{numeric_attribute.id}"

    numeric_attribute.refresh_from_db()
    assert numeric_attribute.values.count() == values_count + 1


def test_create_product_with_numeric_attribute_existing_value(
    staff_api_client,
    product_type,
    category,
    numeric_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = numeric_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.set([numeric_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)
    existing_value = numeric_attribute.values.first()

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": [existing_value.name]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    product_pk = graphene.Node.from_global_id(data["product"]["id"])[1]
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert (
        data["product"]["attributes"][0]["attribute"]["slug"] == numeric_attribute.slug
    )
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 1
    assert values[0]["name"] == existing_value.name
    assert values[0]["slug"] == f"{product_pk}_{numeric_attribute.id}"

    numeric_attribute.refresh_from_db()
    assert numeric_attribute.values.count() == values_count + 1


def test_create_product_with_swatch_attribute_new_attribute_value(
    staff_api_client,
    product_type,
    category,
    swatch_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = swatch_attribute.values.count()
    new_value = "Yellow"

    # Add second attribute
    product_type.product_attributes.set([swatch_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", swatch_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": [new_value]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert (
        data["product"]["attributes"][0]["attribute"]["slug"] == swatch_attribute.slug
    )
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 1
    assert values[0]["name"] == new_value
    assert values[0]["slug"] == slugify(new_value)

    swatch_attribute.refresh_from_db()
    assert swatch_attribute.values.count() == values_count + 1


def test_create_product_with_swatch_attribute_existing_value(
    staff_api_client,
    product_type,
    category,
    swatch_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = swatch_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.set([swatch_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", swatch_attribute.id)
    existing_value = swatch_attribute.values.first()

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": [existing_value.name]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert (
        data["product"]["attributes"][0]["attribute"]["slug"] == swatch_attribute.slug
    )
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 1
    assert values[0]["name"] == existing_value.name
    assert values[0]["slug"] == existing_value.slug

    swatch_attribute.refresh_from_db()
    assert swatch_attribute.values.count() == values_count


def test_create_product_with_numeric_attribute_not_numeric_value_given(
    staff_api_client,
    product_type,
    category,
    numeric_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = numeric_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.set([numeric_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": ["abd"]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert not data["product"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "attributes"
    assert data["errors"][0]["code"] == AttributeErrorCode.INVALID.name

    numeric_attribute.refresh_from_db()
    assert numeric_attribute.values.count() == values_count


# Because we use Scalars for Weight this test query tests only a scenario when weight
# value is passed by a variable
MUTATION_CREATE_PRODUCT_WITH_WEIGHT_GQL_VARIABLE = """
mutation createProduct(
        $productType: ID!,
        $category: ID!
        $name: String!,
        $weight: WeightScalar)
    {
        productCreate(
            input: {
                category: $category,
                productType: $productType,
                name: $name,
                weight: $weight
            })
        {
            product {
                id
                weight{
                    value
                    unit
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


@pytest.mark.parametrize(
    "weight, expected_weight_value",
    (
        ("0", 0),
        (0, 0),
        (11.11, 11.11),
        (11, 11.0),
        ("11.11", 11.11),
        ({"value": 11.11, "unit": "kg"}, 11.11),
        ({"value": 11, "unit": "g"}, 0.011),
        ({"value": "1", "unit": "ounce"}, 0.028),
    ),
)
def test_create_product_with_weight_variable(
    weight,
    expected_weight_value,
    staff_api_client,
    category,
    permission_manage_products,
    product_type_without_variant,
    site_settings,
):
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_type_id = graphene.Node.to_global_id(
        "ProductType", product_type_without_variant.pk
    )
    variables = {
        "category": category_id,
        "productType": product_type_id,
        "name": "Test",
        "weight": weight,
    }
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PRODUCT_WITH_WEIGHT_GQL_VARIABLE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    result_weight = content["data"]["productCreate"]["product"]["weight"]
    assert result_weight["value"] == expected_weight_value
    assert result_weight["unit"] == site_settings.default_weight_unit.upper()


@pytest.mark.parametrize(
    "weight, expected_weight_value",
    (
        ("0", 0),
        (0, 0),
        ("11.11", 11.11),
        ("11", 11.0),
        ('"11.11"', 11.11),
        ('{value: 11.11, unit: "kg"}', 11.11),
        ('{value: 11, unit: "g"}', 0.011),
        ('{value: "1", unit: "ounce"}', 0.028),
    ),
)
def test_create_product_with_weight_input(
    weight,
    expected_weight_value,
    staff_api_client,
    category,
    permission_manage_products,
    product_type_without_variant,
    site_settings,
):
    # Because we use Scalars for Weight this test query tests only a scenario when
    # weight value is passed by directly in input
    query = f"""
    mutation createProduct(
            $productType: ID!,
            $category: ID!,
            $name: String!)
        {{
            productCreate(
                input: {{
                    category: $category,
                    productType: $productType,
                    name: $name,
                    weight: {weight}
                }})
            {{
                product {{
                    id
                    weight{{
                        value
                        unit
                    }}
                }}
                errors {{
                    message
                    field
                    code
                }}
            }}
        }}
    """
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_type_id = graphene.Node.to_global_id(
        "ProductType", product_type_without_variant.pk
    )
    variables = {
        "category": category_id,
        "productType": product_type_id,
        "name": "Test",
    }
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    result_weight = content["data"]["productCreate"]["product"]["weight"]
    assert result_weight["value"] == expected_weight_value
    assert result_weight["unit"] == site_settings.default_weight_unit.upper()


def test_create_product_with_non_unique_external_reference(
    staff_api_client,
    product_type,
    category,
    product,
    permission_manage_products,
):
    # given
    query = CREATE_PRODUCT_MUTATION
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    ext_ref = "test-ext-ref"
    product.external_reference = ext_ref
    product.save(update_fields=["external_reference"])

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "externalReference": ext_ref,
            "name": "test prod",
            "slug": "test-prod",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["productCreate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == ProductErrorCode.UNIQUE.name
    assert error["message"] == "Product with this External reference already exists."
