from unittest.mock import ANY, patch

import graphene
import pytest

from .....attribute.models import Attribute
from .....channel.models import Channel
from .....csv import ExportEvents
from .....csv.models import ExportEvent
from .....warehouse.models import Warehouse
from ....tests.utils import get_graphql_content
from ...enums import ExportScope, FileTypeEnum, ProductFieldEnum

EXPORT_PRODUCTS_MUTATION = """
    mutation ExportProducts($input: ExportProductsInput!){
        exportProducts(input: $input){
            exportFile {
                id
                status
                createdAt
                updatedAt
                url
                user {
                    email
                }
                app {
                    name
                }
            }
            exportErrors {
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
    permission_manage_apps,
    input,
    called_data,
):
    query = EXPORT_PRODUCTS_MUTATION
    user = staff_api_client.user
    variables = {"input": input}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once_with(
        ANY, called_data, {}, FileTypeEnum.CSV.value
    )

    assert not data["exportErrors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products_task.delay")
def test_export_products_mutation_by_app(
    export_products_mock,
    app_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
    permission_manage_staff,
):
    query = EXPORT_PRODUCTS_MUTATION
    app = app_api_client.app
    variables = {
        "input": {
            "scope": ExportScope.ALL.name,
            "exportInfo": {},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_products,
            permission_manage_apps,
            permission_manage_staff,
        ],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once_with(
        ANY, {"all": ""}, {}, FileTypeEnum.CSV.value
    )

    assert not data["exportErrors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"] is None
    assert export_file_data["app"]["name"] == app.name
    assert ExportEvent.objects.filter(
        user=None, app=app, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products_task.delay")
def test_export_products_mutation_ids_scope(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
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
                "fields": [ProductFieldEnum.NAME.name],
                "warehouses": [],
                "attributes": [],
            },
            "fileType": FileTypeEnum.XLSX.name,
        }
    }

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once()
    (
        call_args,
        call_kwargs,
    ) = export_products_mock.call_args

    assert set(call_args[1]["ids"]) == pks
    assert call_args[2] == {"fields": [ProductFieldEnum.NAME.value]}
    assert call_args[3] == FileTypeEnum.XLSX.value

    assert not data["exportErrors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products_task.delay")
def test_export_products_mutation_with_warehouse_and_attribute_ids(
    export_products_mock,
    staff_api_client,
    product_list,
    channel_USD,
    channel_PLN,
    permission_manage_products,
    permission_manage_apps,
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
    channel_pks = [str(channel.pk) for channel in Channel.objects.all()]

    attribute_ids = [
        graphene.Node.to_global_id("Attribute", pk) for pk in attribute_pks
    ]
    warehouse_ids = [
        graphene.Node.to_global_id("Warehouse", pk) for pk in warehouse_pks
    ]
    channel_ids = [graphene.Node.to_global_id("Channel", pk) for pk in channel_pks]

    variables = {
        "input": {
            "scope": ExportScope.IDS.name,
            "ids": ids,
            "exportInfo": {
                "fields": [ProductFieldEnum.NAME.name],
                "warehouses": warehouse_ids,
                "attributes": attribute_ids,
                "channels": channel_ids,
            },
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once()
    (
        call_args,
        call_kwargs,
    ) = export_products_mock.call_args

    assert set(call_args[1]["ids"]) == pks
    assert call_args[2] == {
        "fields": [ProductFieldEnum.NAME.value],
        "warehouses": warehouse_pks,
        "attributes": attribute_pks,
        "channels": channel_pks,
    }
    assert call_args[3] == FileTypeEnum.CSV.value

    assert not data["exportErrors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
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
    errors = data["exportErrors"]

    export_products_mock.assert_not_called()

    assert data["exportErrors"]
    assert errors[0]["field"] == error_field
    assert not ExportEvent.objects.filter(
        user=user, type=ExportEvents.EXPORT_PENDING
    ).exists()
