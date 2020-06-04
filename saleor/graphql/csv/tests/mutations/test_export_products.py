from unittest.mock import ANY, patch

import graphene
import pytest

from saleor.csv import ExportEvents
from saleor.csv.models import ExportEvent
from saleor.graphql.csv.enums import ExportScope, FileTypeEnum, ProductFieldEnum
from saleor.graphql.tests.utils import get_graphql_content
from saleor.product.models import Attribute
from saleor.warehouse.models import Warehouse

EXPORT_PRODUCTS_MUTATION = """
    mutation ExportProducts($input: ExportProductsInput!){
        exportProducts(input: $input){
            exportFile {
                id
                status
                createdAt
                updatedAt
                url
                createdBy {
                    email
                }
            }
            csvErrors {
                field
                code
                message
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input, called_data",
    [
        (
            {
                "scope": ExportScope.ALL.name,
                "exportInfo": {},
                "fileType": FileTypeEnum.CSV.name,
            },
            {"all": ""},
        ),
        (
            {
                "scope": ExportScope.FILTER.name,
                "filter": {"isPublished": True},
                "exportInfo": {},
                "fileType": FileTypeEnum.CSV.name,
            },
            {"filter": {"is_published": True}},
        ),
    ],
)
@patch("saleor.graphql.csv.mutations.export_products_task.delay")
def test_export_products_mutation(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    input,
    called_data,
):
    query = EXPORT_PRODUCTS_MUTATION
    user = staff_api_client.user
    variables = {"input": input}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once_with(
        ANY, called_data, {}, FileTypeEnum.CSV.value
    )

    assert not data["csvErrors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["createdBy"]["email"] == staff_api_client.user.email
    assert ExportEvent.objects.filter(
        user=user, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products_task.delay")
def test_export_products_mutation_ids_scope(
    export_products_mock, staff_api_client, product_list, permission_manage_products
):
    query = EXPORT_PRODUCTS_MUTATION
    user = staff_api_client.user

    products = product_list[:2]

    ids = []
    pks = set()
    for product in products:
        pks.add(str(product.pk))
        ids.append(graphene.Node.to_global_id("Product", product.pk))

    variables = {
        "input": {
            "scope": ExportScope.IDS.name,
            "ids": ids,
            "exportInfo": {
                "fields": [ProductFieldEnum.PRICE_OVERRIDE.name],
                "warehouses": [],
                "attributes": [],
            },
            "fileType": FileTypeEnum.XLSX.name,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once()
    (call_args, call_kwargs,) = export_products_mock.call_args

    assert set(call_args[1]["ids"]) == pks
    assert call_args[2] == {"fields": [ProductFieldEnum.PRICE_OVERRIDE.value]}
    assert call_args[3] == FileTypeEnum.XLSX.value

    assert not data["csvErrors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["createdBy"]["email"] == staff_api_client.user.email
    assert ExportEvent.objects.filter(
        user=user, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products_task.delay")
def test_export_products_mutation_with_warehouse_and_attribute_ids(
    export_products_mock, staff_api_client, product_list, permission_manage_products
):
    query = EXPORT_PRODUCTS_MUTATION
    user = staff_api_client.user

    products = product_list[:2]

    ids = []
    pks = set()
    for product in products:
        pks.add(str(product.pk))
        ids.append(graphene.Node.to_global_id("Product", product.pk))

    attribute_pks = [str(attr.pk) for attr in Attribute.objects.all()]
    warehouse_pks = [str(warehouse.pk) for warehouse in Warehouse.objects.all()]

    attribute_ids = [
        graphene.Node.to_global_id("Attribute", pk) for pk in attribute_pks
    ]
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", pk) for pk in warehouse_pks
    ]

    variables = {
        "input": {
            "scope": ExportScope.IDS.name,
            "ids": ids,
            "exportInfo": {
                "fields": [ProductFieldEnum.PRICE_OVERRIDE.name],
                "warehouses": warehouse_ids,
                "attributes": attribute_ids,
            },
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once()
    (call_args, call_kwargs,) = export_products_mock.call_args

    assert set(call_args[1]["ids"]) == pks
    assert call_args[2] == {
        "fields": [ProductFieldEnum.PRICE_OVERRIDE.value],
        "warehouses": warehouse_pks,
        "attributes": attribute_pks,
    }
    assert call_args[3] == FileTypeEnum.CSV.value

    assert not data["csvErrors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["createdBy"]["email"] == staff_api_client.user.email
    assert ExportEvent.objects.filter(
        user=user, type=ExportEvents.EXPORT_PENDING
    ).exists()


@pytest.mark.parametrize(
    "input, error_field",
    [
        (
            {
                "scope": ExportScope.FILTER.name,
                "exportInfo": {},
                "fileType": FileTypeEnum.CSV.name,
            },
            "filter",
        ),
        (
            {
                "scope": ExportScope.IDS.name,
                "exportInfo": {},
                "fileType": FileTypeEnum.CSV.name,
            },
            "ids",
        ),
    ],
)
@patch("saleor.graphql.csv.mutations.export_products_task.delay")
def test_export_products_mutation_failed(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    input,
    error_field,
):
    query = EXPORT_PRODUCTS_MUTATION
    user = staff_api_client.user
    variables = {"input": input}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    errors = data["csvErrors"]

    export_products_mock.assert_not_called()

    assert data["csvErrors"]
    assert errors[0]["field"] == error_field
    assert not ExportEvent.objects.filter(
        user=user, type=ExportEvents.EXPORT_PENDING
    ).exists()
