from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....attribute.error_codes import AttributeErrorCode
from .....attribute.models import Attribute
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....core.enums import MeasurementUnitsEnum
from ....tests.utils import get_graphql_content
from ...enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum

CREATE_ATTRIBUTE_MUTATION = """
    mutation createAttribute(
        $input: AttributeCreateInput!
    ){
        attributeCreate(input: $input) {
            errors {
                field
                message
                code
            }
            attribute {
                name
                slug
                type
                unit
                inputType
                entityType
                filterableInStorefront
                filterableInDashboard
                availableInGrid
                storefrontSearchPosition
                choices(first: 10) {
                    edges {
                        node {
                            name
                            slug
                            value
                            file {
                                url
                                contentType
                            }
                        }
                    }
                }
                productTypes(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
    }
"""


def test_create_attribute_and_attribute_values(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]) == 1
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["choices"]["edges"][0]["node"]["name"] == name
    assert data["attribute"]["choices"]["edges"][0]["node"]["slug"] == slugify(name)


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_attribute_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_ATTRIBUTE_MUTATION,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    attribute = Attribute.objects.last()

    # then
    assert not data["errors"]
    assert data["attribute"]

    mocked_webhook_trigger.assert_called_once_with(
        {
            "id": graphene.Node.to_global_id("Attribute", attribute.id),
            "name": attribute.name,
            "slug": attribute.slug,
            "meta": generate_meta(
                requestor_data=generate_requestor(
                    SimpleLazyObject(lambda: staff_api_client.user)
                )
            ),
        },
        WebhookEventAsyncType.ATTRIBUTE_CREATED,
        [any_webhook],
        attribute,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_create_numeric_attribute_and_attribute_values(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example numeric attribute name"
    name = "12.1"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "unit": MeasurementUnitsEnum.M.name,
            "inputType": AttributeInputTypeEnum.NUMERIC.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["unit"] == MeasurementUnitsEnum.M.name
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.NUMERIC.name
    assert data["attribute"]["filterableInStorefront"] is True
    assert data["attribute"]["filterableInDashboard"] is True
    assert data["attribute"]["availableInGrid"] is True
    assert data["attribute"]["storefrontSearchPosition"] == 0
    assert data["attribute"]["choices"]["edges"] == []


def test_create_numeric_attribute_and_attribute_values_not_numeric_value_provided(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example numeric attribute name"
    name = "Width"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "unit": MeasurementUnitsEnum.M.name,
            "inputType": AttributeInputTypeEnum.NUMERIC.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = content["data"]["attributeCreate"]["errors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "values"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


def test_create_swatch_attribute_and_attribute_values_only_name_provided(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example numeric attribute name"
    name = "Pink"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.SWATCH.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]) == 1
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["unit"] is None
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.SWATCH.name
    assert data["attribute"]["filterableInStorefront"] is True
    assert data["attribute"]["filterableInDashboard"] is True
    assert data["attribute"]["availableInGrid"] is True
    assert data["attribute"]["storefrontSearchPosition"] == 0
    assert data["attribute"]["choices"]["edges"][0]["node"]["name"] == name
    assert data["attribute"]["choices"]["edges"][0]["node"]["slug"] == slugify(name)


def test_create_swatch_attribute_and_attribute_values_with_file(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example numeric attribute name"
    name = "Logo"
    file_url = "http://mirumee.com/test_media/test_logo.png"
    content_type = "image/png"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [
                {"name": name, "fileUrl": file_url, "contentType": content_type}
            ],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.SWATCH.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]["edges"]) == 1
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["unit"] is None
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.SWATCH.name
    assert data["attribute"]["filterableInStorefront"] is True
    assert data["attribute"]["filterableInDashboard"] is True
    assert data["attribute"]["availableInGrid"] is True
    assert data["attribute"]["storefrontSearchPosition"] == 0
    assert data["attribute"]["choices"]["edges"][0]["node"]["name"] == name
    assert data["attribute"]["choices"]["edges"][0]["node"]["slug"] == slugify(name)
    assert data["attribute"]["choices"]["edges"][0]["node"]["file"] == {
        "url": file_url,
        "contentType": content_type,
    }


def test_create_swatch_attribute_and_attribute_values_with_value(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example numeric attribute name"
    name = "Pink"
    value = "#ffc0cb"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name, "value": value}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.SWATCH.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]["edges"]) == 1
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["unit"] is None
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.SWATCH.name
    assert data["attribute"]["filterableInStorefront"] is True
    assert data["attribute"]["filterableInDashboard"] is True
    assert data["attribute"]["availableInGrid"] is True
    assert data["attribute"]["storefrontSearchPosition"] == 0
    assert data["attribute"]["choices"]["edges"][0]["node"]["name"] == name
    assert data["attribute"]["choices"]["edges"][0]["node"]["slug"] == slugify(name)
    assert data["attribute"]["choices"]["edges"][0]["node"]["file"] is None
    assert data["attribute"]["choices"]["edges"][0]["node"]["value"] == value


def test_create_swatch_attribute_and_attribute_values_file_and_value_provided(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example numeric attribute name"
    name = "Pink"
    file_url = "http://mirumee.com/test_media/test_file.jpeg"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name, "value": "#A8A8A8", "fileUrl": file_url}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.SWATCH.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]
    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "values"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


@pytest.mark.parametrize(
    "field, value", [("fileUrl", "test.jpg"), ("value", "blue"), ("contentType", "jpg")]
)
def test_create_not_swatch_attribute_provide_not_valid_data(
    field,
    value,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example numeric attribute name"
    name = "Test"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name, field: value}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]
    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "values"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


def test_create_attribute_with_file_input_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]["edges"]) == 0
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.FILE.name


@pytest.mark.parametrize(
    "entity_type",
    [AttributeEntityTypeEnum.PAGE.name, AttributeEntityTypeEnum.PRODUCT.name],
)
def test_create_attribute_with_reference_input_type(
    entity_type,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": entity_type,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]["edges"]) == 0
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.REFERENCE.name
    assert data["attribute"]["entityType"] == entity_type


def test_create_attribute_with_reference_input_type_entity_type_not_given(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "entityType"
    assert errors[0]["code"] == AttributeErrorCode.REQUIRED.name


def test_create_attribute_with_plain_text_input_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.PLAIN_TEXT.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]["edges"]) == 0
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.PLAIN_TEXT.name


def test_create_page_attribute_and_attribute_values(
    staff_api_client,
    permission_manage_page_types_and_attributes,
    permission_manage_pages,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name}],
            "type": AttributeTypeEnum.PAGE_TYPE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_page_types_and_attributes,
            permission_manage_pages,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"
    assert data["attribute"]["filterableInStorefront"] is False
    assert data["attribute"]["filterableInDashboard"] is False
    assert data["attribute"]["availableInGrid"] is False
    assert data["attribute"]["storefrontSearchPosition"] == 0

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]["edges"]) == 1
    assert data["attribute"]["type"] == AttributeTypeEnum.PAGE_TYPE.name
    assert data["attribute"]["choices"]["edges"][0]["node"]["name"] == name
    assert data["attribute"]["choices"]["edges"][0]["node"]["slug"] == slugify(name)


def test_create_attribute_with_file_input_type_and_values(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "values": [{"name": name}],
            "inputType": AttributeInputTypeEnum.FILE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "values"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


def test_create_attribute_with_file_input_type_correct_attribute_settings(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
            "filterableInStorefront": False,
            "filterableInDashboard": False,
            "availableInGrid": False,
            "storefrontSearchPosition": 0,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["errors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["choices"]["edges"]) == 0
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.FILE.name


def test_create_attribute_with_file_input_type_and_invalid_settings(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
            "storefrontSearchPosition": 1,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]

    assert not data["attribute"]
    assert len(errors) == 4
    assert {error["field"] for error in errors} == {
        "filterableInStorefront",
        "filterableInDashboard",
        "availableInGrid",
        "storefrontSearchPosition",
    }
    assert {error["code"] for error in errors} == {AttributeErrorCode.INVALID.name}


@pytest.mark.parametrize(
    "entity_type",
    [AttributeEntityTypeEnum.PAGE.name, AttributeEntityTypeEnum.PRODUCT.name],
)
def test_create_attribute_with_reference_input_type_invalid_settings(
    entity_type,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": entity_type,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
            "storefrontSearchPosition": 1,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]

    assert not data["attribute"]
    assert len(errors) == 4
    assert {error["field"] for error in errors} == {
        "filterableInStorefront",
        "filterableInDashboard",
        "availableInGrid",
        "storefrontSearchPosition",
    }
    assert {error["code"] for error in errors} == {AttributeErrorCode.INVALID.name}


@pytest.mark.parametrize(
    "field, value",
    [
        ("filterableInStorefront", True),
        ("filterableInDashboard", True),
        ("availableInGrid", True),
        ("storefrontSearchPosition", 4),
    ],
)
def test_create_attribute_with_file_input_type_and_invalid_one_settings_value(
    field,
    value,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
            field: value,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == field
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


@pytest.mark.parametrize(
    "field, value",
    [
        ("filterableInStorefront", True),
        ("filterableInDashboard", True),
        ("availableInGrid", True),
        ("storefrontSearchPosition", 4),
    ],
)
def test_create_attribute_with_reference_input_type_invalid_one_settings_value(
    field,
    value,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": AttributeEntityTypeEnum.PAGE.name,
            field: value,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == field
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


@pytest.mark.parametrize(
    "entity_type",
    [AttributeEntityTypeEnum.PAGE.name, AttributeEntityTypeEnum.PRODUCT.name],
)
def test_create_attribute_with_reference_input_type_values_given(
    entity_type,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": entity_type,
            "values": [{"name": "test-value"}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["errors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "values"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("my-slug", "my-slug"),
        (None, "my-name"),
        ("", "my-name"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ),
)
def test_create_attribute_with_given_slug(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
    input_slug,
    expected_slug,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    query = """
        mutation createAttribute(
            $name: String!, $slug: String, $type: AttributeTypeEnum!) {
        attributeCreate(input: {name: $name, slug: $slug, type: $type}) {
            errors {
                field
                message
                code
            }
            attribute {
                slug
            }
        }
    }
    """

    attribute_name = "My Name"
    variables = {
        "name": attribute_name,
        "slug": input_slug,
        "type": AttributeTypeEnum.PRODUCT_TYPE.name,
    }

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    assert not content["data"]["attributeCreate"]["errors"]
    assert content["data"]["attributeCreate"]["attribute"]["slug"] == expected_slug


def test_create_attribute_value_name_and_slug_with_unicode(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION
    name = "わたし わ にっぽん です"
    slug = "わたし-わ-にっぽん-で"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    assert not data["errors"]
    assert data["attribute"]["name"] == name
    assert data["attribute"]["slug"] == slug


@pytest.mark.parametrize(
    "name_1, name_2, error_msg, error_code",
    (
        (
            "Red color",
            "Red color",
            "Provided values are not unique.",
            AttributeErrorCode.UNIQUE,
        ),
        (
            "Red color",
            "red color",
            "Provided values are not unique.",
            AttributeErrorCode.UNIQUE,
        ),
    ),
)
def test_create_attribute_and_attribute_values_errors(
    staff_api_client,
    name_1,
    name_2,
    error_msg,
    error_code,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
    product_type,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION
    variables = {
        "input": {
            "name": "Example name",
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "values": [{"name": name_1}, {"name": name_2}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["attributeCreate"]["errors"]
    assert errors
    assert errors[0]["field"] == "values"
    assert errors[0]["message"] == error_msg
    assert errors[0]["code"] == error_code.name
