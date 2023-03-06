import json
from unittest.mock import ANY, patch

import graphene
import pytest
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.text import slugify
from freezegun import freeze_time

from .....attribute import AttributeInputType
from .....attribute.models import Attribute, AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....core.taxes import TaxType
from .....graphql.core.enums import AttributeErrorCode
from .....graphql.tests.utils import get_graphql_content
from .....plugins.manager import PluginsManager
from .....product.error_codes import ProductErrorCode
from .....product.models import Product
from ....attribute.utils import AttributeInputErrors

MUTATION_UPDATE_PRODUCT = """
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
                            id
                            name
                        }
                        values {
                            id
                            name
                            slug
                            boolean
                            reference
                            plainText
                            file {
                                url
                                contentType
                            }
                        }
                    }
                    externalReference
                }
                errors {
                    message
                    field
                    code
                }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_created")
def test_update_product(
    created_webhook_mock,
    updated_webhook_mock,
    staff_api_client,
    category,
    non_default_category,
    product,
    other_description_json,
    permission_manage_products,
    monkeypatch,
    color_attribute,
):
    # given

    expected_other_description_json = other_description_json
    text = expected_other_description_json["blocks"][0]["data"]["text"]
    expected_other_description_json["blocks"][0]["data"]["text"] = strip_tags(text)
    other_description_json = json.dumps(other_description_json)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_name = "updated name"
    product_slug = "updated-product"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"

    old_meta = {"old": "meta"}
    product.store_value_in_metadata(items=old_meta)
    product.store_value_in_private_metadata(items=old_meta)
    product.save(update_fields=["metadata", "private_metadata"])

    metadata_key = "md key"
    metadata_value = "md value"
    external_reference = "test-ext-ref"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    attr_value = "Rainbow"

    variables = {
        "productId": product_id,
        "input": {
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": other_description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [{"id": attribute_id, "values": [attr_value]}],
            "metadata": [{"key": metadata_key, "value": metadata_value}],
            "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
            "externalReference": external_reference,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PRODUCT, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    product.refresh_from_db()

    # then
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["description"] == json.dumps(expected_other_description_json)
    assert data["product"]["chargeTaxes"] == product_charge_taxes
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert not data["product"]["category"]["name"] == category.name
    assert product.metadata == {metadata_key: metadata_value, **old_meta}
    assert product.private_metadata == {metadata_key: metadata_value, **old_meta}
    assert (
        data["product"]["externalReference"]
        == external_reference
        == product.external_reference
    )

    attributes = data["product"]["attributes"]

    assert len(attributes) == 1
    assert len(attributes[0]["values"]) == 1

    assert attributes[0]["attribute"]["id"] == attribute_id
    assert attributes[0]["values"][0]["name"] == "Rainbow"
    assert attributes[0]["values"][0]["slug"] == "rainbow"

    updated_webhook_mock.assert_called_once_with(product)
    created_webhook_mock.assert_not_called()


def test_update_and_search_product_by_description(
    staff_api_client,
    category,
    non_default_category,
    product,
    other_description_json,
    permission_manage_products,
    color_attribute,
):
    query = MUTATION_UPDATE_PRODUCT
    other_description_json = json.dumps(other_description_json)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_name = "updated name"
    product_slug = "updated-product"

    variables = {
        "productId": product_id,
        "input": {
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": other_description_json,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert not data["errors"]
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["description"] == other_description_json


def test_update_product_without_description_clear_description_plaintext(
    staff_api_client,
    category,
    non_default_category,
    product,
    other_description_json,
    permission_manage_products,
    color_attribute,
):
    query = MUTATION_UPDATE_PRODUCT
    description_plaintext = "some desc"
    product.description_plaintext = description_plaintext
    product.save()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_name = "updated name"
    product_slug = "updated-product"

    variables = {
        "productId": product_id,
        "input": {
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert not data["errors"]
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["description"] is None

    product.refresh_from_db()
    assert product.description_plaintext == ""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_boolean_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    boolean_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.pk)
    product_type.product_attributes.add(boolean_attribute)

    new_value = False

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "boolean": new_value}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": boolean_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": "Boolean: No",
                "boolean": new_value,
                "slug": f"{boolean_attribute.id}_false",
                "reference": None,
                "file": None,
                "plainText": None,
            }
        ],
    }
    assert expected_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_file_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    file_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)
    product_type.product_attributes.add(file_attribute)

    file_name = "new_test.jpg"
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}{file_name}"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "file": file_url}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {"id": attribute_id, "name": file_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": file_name,
                "slug": slugify(file_name),
                "reference": None,
                "file": {
                    "url": file_url,
                    "contentType": None,
                },
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_file_attribute_value_new_value_is_not_created(
    updated_webhook_mock,
    staff_api_client,
    file_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)
    product_type.product_attributes.add(file_attribute)
    existing_value = file_attribute.values.first()
    associate_attribute_values_to_instance(product, file_attribute, existing_value)

    values_count = file_attribute.values.count()
    domain = site_settings.site.domain
    file_url = f"http://{domain}{settings.MEDIA_URL}{existing_value.file_url}"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "file": file_url}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {"id": attribute_id, "name": file_attribute.name},
        "values": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", existing_value.pk),
                "name": existing_value.name,
                "slug": existing_value.slug,
                "reference": None,
                "file": {
                    "url": file_url,
                    "contentType": existing_value.content_type,
                },
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_numeric_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    numeric_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    product_type.product_attributes.add(numeric_attribute)

    new_value = "45.2"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": [new_value]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": numeric_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": new_value,
                "slug": slugify(
                    f"{product.id}_{numeric_attribute.id}", allow_unicode=True
                ),
                "reference": None,
                "file": None,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_numeric_attribute_value_new_value_is_not_created(
    updated_webhook_mock,
    staff_api_client,
    numeric_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    product_type.product_attributes.add(numeric_attribute)
    slug_value = slugify(f"{product.id}_{numeric_attribute.id}", allow_unicode=True)
    value = AttributeValue.objects.create(
        attribute=numeric_attribute, slug=slug_value, name="20.0"
    )
    associate_attribute_values_to_instance(product, numeric_attribute, value)

    value_count = AttributeValue.objects.count()

    new_value = "45.2"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": [new_value]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": numeric_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": new_value,
                "slug": slug_value,
                "reference": None,
                "file": None,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_att_data in attributes

    assert AttributeValue.objects.count() == value_count
    value.refresh_from_db()
    assert value.name == new_value


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_clear_attribute_values(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    product_attr = product.attributes.first()
    attribute = product_attr.assignment.attribute
    attribute.value_required = False
    attribute.save(update_fields=["value_required"])

    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": []}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 1
    assert not attributes[0]["values"]
    with pytest.raises(product_attr._meta.model.DoesNotExist):
        product_attr.refresh_from_db()

    updated_webhook_mock.assert_called_once_with(product)


def test_update_product_clean_boolean_attribute_value(
    staff_api_client,
    product,
    product_type,
    boolean_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.pk)

    product_type.product_attributes.add(boolean_attribute)
    associate_attribute_values_to_instance(
        product, boolean_attribute, boolean_attribute.values.first()
    )

    product_attr = product.attributes.get(assignment__attribute_id=boolean_attribute.id)
    assert product_attr.values.count() == 1

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": []}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": boolean_attribute.name},
        "values": [],
    }
    assert expected_att_data in attributes
    assert product_attr.values.count() == 0


def test_update_product_clean_file_attribute_value(
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)

    product_type.product_attributes.add(file_attribute)
    associate_attribute_values_to_instance(
        product, file_attribute, file_attribute.values.first()
    )

    product_attr = product.attributes.get(assignment__attribute_id=file_attribute.id)
    assert product_attr.values.count() == 1

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": []}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": file_attribute.name},
        "values": [],
    }
    assert expected_att_data in attributes
    assert product_attr.values.count() == 0


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_none_as_attribute_values(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    product_attr = product.attributes.first()
    attribute = product_attr.assignment.attribute
    attribute.value_required = False
    attribute.save(update_fields=["value_required"])

    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": None}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 1
    assert not attributes[0]["values"]
    with pytest.raises(product_attr._meta.model.DoesNotExist):
        product_attr.refresh_from_db()

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_plain_text_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    plain_text_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", plain_text_attribute.pk)
    product_type.product_attributes.add(plain_text_attribute)

    plain_text_attribute_value = plain_text_attribute.values.first()
    text = plain_text_attribute_value.plain_text

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "plainText": text}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": plain_text_attribute.name},
        "values": [
            {
                "id": ANY,
                "slug": f"{product.id}_{plain_text_attribute.id}",
                "name": text,
                "reference": None,
                "file": None,
                "boolean": None,
                "plainText": text,
            }
        ],
    }
    assert expected_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_plain_text_attribute_value_required(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    plain_text_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", plain_text_attribute.pk)
    product_type.product_attributes.add(plain_text_attribute)

    plain_text_attribute.value_required = True
    plain_text_attribute.save(update_fields=["value_required"])

    plain_text_attribute_value = plain_text_attribute.values.first()
    text = plain_text_attribute_value.plain_text

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "plainText": text}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": plain_text_attribute.name},
        "values": [
            {
                "id": ANY,
                "slug": f"{product.id}_{plain_text_attribute.id}",
                "name": text,
                "reference": None,
                "file": None,
                "boolean": None,
                "plainText": text,
            }
        ],
    }
    assert expected_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


@pytest.mark.parametrize("value", ["", "  ", None])
@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_plain_text_attribute_value_required_no_value_given(
    updated_webhook_mock,
    value,
    staff_api_client,
    product,
    product_type,
    plain_text_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", plain_text_attribute.pk)
    product_type.product_attributes.add(plain_text_attribute)

    plain_text_attribute.value_required = True
    plain_text_attribute.save(update_fields=["value_required"])

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "plainText": value}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"


@freeze_time("2020-03-18 12:00:00")
def test_update_product_rating(
    staff_api_client,
    product,
    permission_manage_products,
):
    query = MUTATION_UPDATE_PRODUCT

    product.rating = 5.5
    product.save(update_fields=["rating"])
    product_id = graphene.Node.to_global_id("Product", product.pk)
    expected_rating = 9.57
    variables = {"productId": product_id, "input": {"rating": expected_rating}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []
    assert data["product"]["rating"] == expected_rating
    product.refresh_from_db()
    assert product.rating == expected_rating


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_page_reference_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_page_reference_attribute,
    product,
    product_type,
    page,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_page_reference_attribute)

    values_count = product_type_page_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("Page", page.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_page_reference_attribute.name,
        },
        "values": [
            {
                "id": ANY,
                "name": page.title,
                "slug": f"{product.id}_{page.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count + 1


def test_update_product_without_supplying_required_product_attribute(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = product.product_type
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    # Create and assign a new attribute requiring a value to be always supplied
    required_attribute = Attribute.objects.create(
        name="Required One", slug="required-one", value_required=True
    )
    product_type.product_attributes.add(required_attribute)
    required_attribute_id = graphene.Node.to_global_id(
        "Attribute", required_attribute.id
    )

    value = "Blue"
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {"attributes": [{"id": color_attribute_id, "values": [value]}]},
    }

    # when
    data = get_graphql_content(
        staff_api_client.post_graphql(MUTATION_UPDATE_PRODUCT, variables)
    )["data"]["productUpdate"]

    # then
    assert not data["errors"]
    attributes_data = data["product"]["attributes"]
    assert len(attributes_data) == 2
    assert {
        "attribute": {"id": required_attribute_id, "name": required_attribute.name},
        "values": [],
    } in attributes_data
    assert {
        "attribute": {"id": color_attribute_id, "name": color_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": value,
                "slug": value.lower(),
                "file": None,
                "reference": None,
                "boolean": None,
                "plainText": None,
            }
        ],
    } in attributes_data


def test_update_product_with_empty_input_collections(
    product, permission_manage_products, staff_api_client
):
    # given
    query = """
    mutation updateProduct($productId: ID!, $input: ProductInput!) {
      productUpdate(id: $productId, input: $input) {
        productErrors {
          field
          message
          code
        }
        product {
          id
        }
      }
    }

    """
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "productId": product_id,
        "input": {"collections": [""]},
    }
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert len(data["productErrors"]) == 1
    product_errors = data["productErrors"][0]
    assert product_errors["code"] == ProductErrorCode.GRAPHQL_ERROR.name


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_page_reference_attribute_existing_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_page_reference_attribute,
    product,
    product_type,
    page,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_page_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page.title,
        slug=f"{product.pk}_{page.pk}",
        reference_page=page,
    )
    associate_attribute_values_to_instance(
        product, product_type_page_reference_attribute, attr_value
    )

    values_count = product_type_page_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("Page", page.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_page_reference_attribute.name,
        },
        "values": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_value.pk),
                "name": page.title,
                "slug": f"{product.id}_{page.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_page_reference_attribute_value_not_given(
    updated_webhook_mock,
    staff_api_client,
    product_type_page_reference_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_type_page_reference_attribute.value_required = True
    product_type_page_reference_attribute.save(update_fields=["value_required"])

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_page_reference_attribute)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": ["test"]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == AttributeErrorCode.REQUIRED.name

    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_product_reference_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_product_reference_attribute,
    product_list,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_list[0]
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product_ref = product_list[1]

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_product_reference_attribute)

    values_count = product_type_product_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("Product", product_ref.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_product_reference_attribute.name,
        },
        "values": [
            {
                "id": ANY,
                "name": product_ref.name,
                "slug": f"{product.id}_{product_ref.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count + 1


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_variant_reference_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_variant_reference_attribute,
    product_list,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_list[0]
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variant_ref = product_list[1].variants.first()

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_variant_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_variant_reference_attribute)

    values_count = product_type_variant_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("ProductVariant", variant_ref.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_variant_reference_attribute.name,
        },
        "values": [
            {
                "id": ANY,
                "name": f"{variant_ref.product.name}: {variant_ref.name}",
                "slug": f"{product.id}_{variant_ref.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_variant_reference_attribute.refresh_from_db()
    assert product_type_variant_reference_attribute.values.count() == values_count + 1


def test_update_product_with_no_id(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure only supplying values triggers a validation error."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"values": ["Oopsie!"]}],
    }

    # when
    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]

    # then
    assert data["errors"] == [
        {
            "field": "attributes",
            "code": ProductErrorCode.REQUIRED.name,
            "message": ANY,
            "attributes": None,
        }
    ]


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_product_reference_attribute_existing_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_product_reference_attribute,
    product_list,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_list[0]
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product_ref = product_list[1]

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_product_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_ref.name,
        slug=f"{product.pk}_{product_ref.pk}",
        reference_product=product_ref,
    )
    associate_attribute_values_to_instance(
        product, product_type_product_reference_attribute, attr_value
    )

    values_count = product_type_product_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("Product", product_ref.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_product_reference_attribute.name,
        },
        "values": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_value.pk),
                "name": product_ref.name,
                "slug": f"{product.id}_{product_ref.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_product_reference_attribute_value_not_given(
    updated_webhook_mock,
    staff_api_client,
    product_type_product_reference_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_type_product_reference_attribute.value_required = True
    product_type_product_reference_attribute.save(update_fields=["value_required"])

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_product_reference_attribute)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": ["test"]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == AttributeErrorCode.REQUIRED.name

    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_change_values_ordering(
    updated_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
    page_list,
    product_type_page_reference_attribute,
):
    # given
    query = MUTATION_UPDATE_PRODUCT
    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )

    product_type = product.product_type
    product_type.product_attributes.set([product_type_page_reference_attribute])

    attr_value_1 = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page_list[0].title,
        slug=f"{product.pk}_{page_list[0].pk}",
        reference_page=page_list[0],
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page_list[1].title,
        slug=f"{product.pk}_{page_list[1].pk}",
        reference_page=page_list[1],
    )

    associate_attribute_values_to_instance(
        product, product_type_page_reference_attribute, attr_value_2, attr_value_1
    )

    assert list(
        product.attributes.first().productvalueassignment.values_list(
            "value_id", flat=True
        )
    ) == [attr_value_2.pk, attr_value_1.pk]

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "references": [
                        graphene.Node.to_global_id("Page", page_list[0].pk),
                        graphene.Node.to_global_id("Page", page_list[1].pk),
                    ],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 1
    values = attributes[0]["values"]
    assert len(values) == 2
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk)
        for val in [attr_value_1, attr_value_2]
    ]
    product.refresh_from_db()
    assert list(
        product.attributes.first().productvalueassignment.values_list(
            "value_id", flat=True
        )
    ) == [attr_value_1.pk, attr_value_2.pk]

    updated_webhook_mock.assert_called_once_with(product)


UPDATE_PRODUCT_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        productUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            product{
                name
                slug
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_product_slug(
    staff_api_client,
    product,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_PRODUCT_SLUG_MUTATION
    old_slug = product.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["product"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_slug_exists(
    staff_api_client, product, permission_manage_products
):
    query = UPDATE_PRODUCT_SLUG_MUTATION
    input_slug = "test-slug"

    second_product = Product.objects.get(pk=product.pk)
    second_product.pk = None
    second_product.slug = input_slug
    second_product.save()

    assert input_slug != product.slug

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_product_slug_and_name(
    staff_api_client,
    product,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            productUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                product{
                    name
                    slug
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = product.name
    old_slug = product.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    product.refresh_from_db()
    data = content["data"]["productUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["product"]["name"] == input_name == product.name
        assert data["product"]["slug"] == input_slug == product.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


SET_ATTRIBUTES_TO_PRODUCT_QUERY = """
    mutation updateProduct($productId: ID!, $attributes: [AttributeValueInput!]) {
      productUpdate(id: $productId, input: { attributes: $attributes }) {
        errors {
          message
          field
          code
          attributes
        }
      }
    }
"""


def test_update_product_can_only_assign_multiple_values_to_valid_input_types(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensures you cannot assign multiple values to input types
    that are not multi-select. This also ensures multi-select types
    can be assigned multiple values as intended."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    multi_values_attr = Attribute.objects.create(
        name="multi", slug="multi-vals", input_type=AttributeInputType.MULTISELECT
    )
    multi_values_attr.product_types.add(product.product_type)
    multi_values_attr_id = graphene.Node.to_global_id("Attribute", multi_values_attr.id)

    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": color_attribute_id, "values": ["red", "blue"]}],
    }
    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["errors"] == [
        {
            "field": "attributes",
            "code": ProductErrorCode.INVALID.name,
            "message": ANY,
            "attributes": [color_attribute_id],
        }
    ]

    # Try to assign multiple values from a valid attribute
    variables["attributes"] = [{"id": multi_values_attr_id, "values": ["a", "b"]}]
    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert not data["errors"]


def test_update_product_with_existing_attribute_value(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    expected_attribute_values_count = color_attribute.values.count()
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    color = color_attribute.values.only("name").first()

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": color_attribute_id, "values": [color.name]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert not data["errors"]

    assert (
        color_attribute.values.count() == expected_attribute_values_count
    ), "A new attribute value shouldn't have been created"


def test_update_product_with_non_existing_attribute(
    staff_api_client, product, permission_manage_products, color_attribute
):
    non_existent_attribute_pk = 0
    invalid_attribute_id = graphene.Node.to_global_id(
        "Attribute", non_existent_attribute_pk
    )

    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": invalid_attribute_id, "values": ["hello"]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["errors"] == [
        {
            "field": "attributes",
            "code": ProductErrorCode.NOT_FOUND.name,
            "message": ANY,
            "attributes": None,
        }
    ]


def test_update_product_with_negative_weight(
    staff_api_client, product_with_default_variant, permission_manage_products, product
):
    query = """
        mutation updateProduct(
            $productId: ID!,
            $weight: WeightScalar)
        {
            productUpdate(
                id: $productId,
                input: {
                    weight: $weight
                })
            {
                product {
                    id
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    product = product_with_default_variant
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {"productId": product_id, "weight": -1}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


UPDATE_PRODUCT = """
    mutation updateProduct(
        $productId: ID!,
        $input: ProductInput!)
    {
        productUpdate(
            id: $productId,
            input: $input)
        {
            product {
                id
                name
                slug
            }
            errors {
                message
                field
            }
        }
    }"""


def test_update_product_name(staff_api_client, permission_manage_products, product):
    query = UPDATE_PRODUCT

    product_slug = product.slug
    new_name = "example-product"
    assert new_name != product.name

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"productId": product_id, "input": {"name": new_name}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    data = get_graphql_content(response)["data"]["productUpdate"]
    assert data["product"]["name"] == new_name
    assert data["product"]["slug"] == product_slug


def test_update_product_slug_with_existing_value(
    staff_api_client, permission_manage_products, product
):
    query = UPDATE_PRODUCT
    second_product = Product.objects.get(pk=product.pk)
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()

    assert product.slug != second_product.slug

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"productId": product_id, "input": {"slug": second_product.slug}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    data = get_graphql_content(response)["data"]["productUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["message"] == "Product with this Slug already exists."


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_numeric_attribute_value_by_numeric_field(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    numeric_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    product_type.product_attributes.add(numeric_attribute)

    new_value = "45.2"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "numeric": new_value}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": numeric_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": new_value,
                "slug": slugify(
                    f"{product.id}_{numeric_attribute.id}", allow_unicode=True
                ),
                "reference": None,
                "file": None,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


def test_update_product_with_numeric_attribute_by_numeric_field_null_value(
    staff_api_client,
    numeric_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    product_type.product_attributes.add(numeric_attribute)
    slug_value = slugify(f"{product.id}_{numeric_attribute.id}", allow_unicode=True)
    value = AttributeValue.objects.create(
        attribute=numeric_attribute, slug=slug_value, name="20.0"
    )
    associate_attribute_values_to_instance(product, numeric_attribute, value)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "numeric": None}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []
    assert not data["product"]["attributes"][1]["values"]


def test_update_product_with_numeric_attribute_by_numeric_field_new_value_not_created(
    staff_api_client,
    numeric_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    product_type.product_attributes.add(numeric_attribute)
    slug_value = slugify(f"{product.id}_{numeric_attribute.id}", allow_unicode=True)
    value = AttributeValue.objects.create(
        attribute=numeric_attribute, slug=slug_value, name="20.0"
    )
    associate_attribute_values_to_instance(product, numeric_attribute, value)

    value_count = AttributeValue.objects.count()

    new_value = "45.2"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "numeric": new_value}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": numeric_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": new_value,
                "slug": slug_value,
                "reference": None,
                "file": None,
                "boolean": None,
                "plainText": None,
            }
        ],
    }
    assert expected_att_data in attributes

    assert AttributeValue.objects.count() == value_count
    value.refresh_from_db()
    assert value.name == new_value


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_dropdown_attribute_non_existing_value(
    updated_webhook_mock,
    staff_api_client,
    color_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    product_type.product_attributes.add(color_attribute)

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "dropdown": {
                        "value": "new color",
                    },
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not errors
    assert data["product"]["attributes"][0]["values"][0]["name"] == "new color"
    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_dropdown_attribute_existing_value(
    updated_webhook_mock,
    staff_api_client,
    color_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    attribute_value = color_attribute.values.model.objects.first()
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.pk
    )
    attribute_value_name = color_attribute.values.model.objects.first().name
    product_type.product_attributes.add(color_attribute)

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "dropdown": {
                        "id": attribute_value_id,
                    },
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not errors
    assert data["product"]["attributes"][0]["values"][0]["name"] == attribute_value_name
    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_dropdown_attribute_existing_value_passed_as_new_value(
    updated_webhook_mock,
    staff_api_client,
    color_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    attribute_value = color_attribute.values.model.objects.first()
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.pk
    )
    attribute_value_name = color_attribute.values.model.objects.first().name
    product_type.product_attributes.add(color_attribute)

    value_count = AttributeValue.objects.count()

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "dropdown": {
                        "value": attribute_value_name,
                    },
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not errors
    assert data["product"]["attributes"][0]["values"][0]["id"] == attribute_value_id
    assert AttributeValue.objects.count() == value_count
    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_dropdown_attribute_null_value(
    updated_webhook_mock,
    staff_api_client,
    color_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    product_type.product_attributes.add(color_attribute)

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "dropdown": {
                        "value": None,
                    },
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not errors
    assert not data["product"]["attributes"][0]["values"]
    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_multiselect_attribute_non_existing_values(
    updated_webhook_mock,
    staff_api_client,
    product_with_multiple_values_attributes,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_with_multiple_values_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute = product.attributes.first().attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    value_count = AttributeValue.objects.count()

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "multiselect": [{"value": "new mode 1"}, {"value": "new mode 2"}],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not errors
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 2
    assert values[0]["name"] == "new mode 1"
    assert values[1]["name"] == "new mode 2"
    updated_webhook_mock.assert_called_once_with(product)

    assert AttributeValue.objects.count() == value_count + 2


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_multiselect_attribute_existing_values(
    updated_webhook_mock,
    staff_api_client,
    product_with_multiple_values_attributes,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_with_multiple_values_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute = product.attributes.first().attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)
    attr_value_1 = product.attributes.first().values.all()[0]
    attr_value_id_1 = graphene.Node.to_global_id("AttributeValue", attr_value_1.pk)
    attr_value_name_1 = product.attributes.first().values.all()[0].name
    attr_value_2 = product.attributes.first().values.all()[1]
    attr_value_id_2 = graphene.Node.to_global_id("AttributeValue", attr_value_2.pk)
    attr_value_name_2 = product.attributes.first().values.all()[1].name

    associate_attribute_values_to_instance(product, attribute, attr_value_1)
    assert len(product.attributes.first().values.all()) == 1

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "multiselect": [{"id": attr_value_id_1}, {"id": attr_value_id_2}],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not errors
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 2
    assert values[0]["name"] == attr_value_name_1
    assert values[1]["name"] == attr_value_name_2
    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_multiselect_attribute_new_values_not_created(
    updated_webhook_mock,
    staff_api_client,
    product_with_multiple_values_attributes,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_with_multiple_values_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute = product.attributes.first().attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)
    attr_value_1 = product.attributes.first().values.all()[0]
    attr_value_id_1 = graphene.Node.to_global_id("AttributeValue", attr_value_1.pk)
    attr_value_name_1 = product.attributes.first().values.all()[0].name
    attr_value_2 = product.attributes.first().values.all()[1]
    attr_value_id_2 = graphene.Node.to_global_id("AttributeValue", attr_value_2.pk)
    attr_value_name_2 = product.attributes.first().values.all()[1].name

    value_count = AttributeValue.objects.count()

    assert len(product.attributes.first().values.all()) == 2

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "multiselect": [
                        {"value": attr_value_name_1},
                        {"value": attr_value_name_2},
                    ],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not errors
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 2
    assert values[0]["id"] == attr_value_id_1
    assert values[1]["id"] == attr_value_id_2
    assert AttributeValue.objects.count() == value_count
    updated_webhook_mock.assert_called_once_with(product)


def test_update_product_with_selectable_attribute_by_both_id_and_value(
    staff_api_client,
    color_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    attribute_value_id = color_attribute.values.model.objects.first().id
    product_type.product_attributes.add(color_attribute)

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "dropdown": {"id": attribute_value_id, "value": "new color"},
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["message"] == AttributeInputErrors.ERROR_ID_AND_VALUE[0]


@pytest.mark.parametrize(
    "value,expected_result",
    [
        ("", AttributeInputErrors.ERROR_NO_VALUE_GIVEN),
        ("  ", AttributeInputErrors.ERROR_BLANK_VALUE),
        (None, AttributeInputErrors.ERROR_NO_VALUE_GIVEN),
    ],
)
def test_update_product_with_selectable_attribute_value_required(
    value,
    expected_result,
    staff_api_client,
    color_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    product_type.product_attributes.add(color_attribute)

    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "dropdown": {
                        "value": value,
                    },
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["message"] == expected_result[0]


def test_update_product_with_selectable_attribute_exceed_max_length(
    staff_api_client,
    color_attribute,
    product,
    product_type,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    product_type.product_attributes.add(color_attribute)
    max_length = color_attribute.values.model.name.field.max_length

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "dropdown": {"value": "a" * max_length + "a"},
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["message"] == AttributeInputErrors.ERROR_MAX_LENGTH[0]


def test_update_product_with_multiselect_attribute_by_both_id_and_value(
    staff_api_client,
    product_with_multiple_values_attributes,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_with_multiple_values_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute = product.attributes.first().attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)
    attr_value = product.attributes.first().values.all()[0]
    attr_value_id = graphene.Node.to_global_id("AttributeValue", attr_value.pk)

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "multiselect": [{"id": attr_value_id}, {"value": "new mode"}],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["message"] == AttributeInputErrors.ERROR_ID_AND_VALUE[0]


def test_update_product_with_multiselect_attribute_by_id_duplicated(
    staff_api_client,
    product_with_multiple_values_attributes,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_with_multiple_values_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute = product.attributes.first().attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)
    attr_value = product.attributes.first().values.all()[0]
    attr_value_id = graphene.Node.to_global_id("AttributeValue", attr_value.pk)

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "multiselect": [{"id": attr_value_id}, {"id": attr_value_id}],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["message"] == AttributeInputErrors.ERROR_DUPLICATED_VALUES[0]


def test_update_product_with_multiselect_attribute_by_name_duplicated(
    staff_api_client,
    product_with_multiple_values_attributes,
    permission_manage_products,
    site_settings,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_with_multiple_values_attributes
    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute = product.attributes.first().attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)
    attr_value_name = product.attributes.first().values.all()[0].name

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "multiselect": [
                        {"value": attr_value_name},
                        {"value": attr_value_name},
                    ],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["message"] == AttributeInputErrors.ERROR_DUPLICATED_VALUES[0]


MUTATION_UPDATE_PRODUCT_BY_EXTERNAL_REFERENCE = """
    mutation updateProduct($id: ID, $externalReference: String, $input: ProductInput!) {
        productUpdate(id: $id, externalReference: $externalReference, input: $input) {
                product {
                    name
                    id
                    externalReference
                }
                errors {
                    message
                    field
                    code
                }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_created")
def test_update_product_by_external_reference(
    created_webhook_mock,
    updated_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    new_name = "updated name"
    product.external_reference = "test-ext-id"
    product.save(update_fields=["external_reference"])

    variables = {
        "externalReference": product.external_reference,
        "input": {"name": new_name},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PRODUCT_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    product.refresh_from_db()

    # then
    assert data["errors"] == []
    assert data["product"]["name"] == new_name
    assert data["product"]["externalReference"] == product.external_reference
    assert data["product"]["id"] == graphene.Node.to_global_id(
        product._meta.model.__name__, product.id
    )

    updated_webhook_mock.assert_called_once_with(product)
    created_webhook_mock.assert_not_called()


def test_update_product_by_both_id_and_external_reference(
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    new_name = "updated name"
    product.external_reference = "test-ext-id"
    product.save(update_fields=["external_reference"])

    variables = {
        "externalReference": product.external_reference,
        "id": product.id,
        "input": {"name": new_name},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PRODUCT_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]

    # then
    assert data["errors"]
    assert (
        data["errors"][0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_update_product_external_reference_not_existing(
    staff_api_client,
    permission_manage_products,
):
    # given
    ext_ref = "non-existing-ext-ref"
    variables = {
        "externalReference": ext_ref,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PRODUCT_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]

    # then
    assert data["errors"]
    assert data["errors"][0]["message"] == f"Couldn't resolve to a node: {ext_ref}"


def test_update_product_with_non_unique_external_reference(
    staff_api_client,
    product_list,
    permission_manage_products,
):
    # given
    product_1 = product_list[0]
    product_2 = product_list[1]
    ext_ref = "test-ext-ref"
    product_1.external_reference = ext_ref
    product_1.save(update_fields=["external_reference"])
    product_2_id = graphene.Node.to_global_id("Product", product_2.id)

    variables = {
        "id": product_2_id,
        "input": {"externalReference": ext_ref},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PRODUCT_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["productUpdate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == ProductErrorCode.UNIQUE.name
    assert error["message"] == "Product with this External reference already exists."
