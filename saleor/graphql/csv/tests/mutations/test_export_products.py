from unittest.mock import ANY, patch

import graphene
import pytest

from .....attribute.models import Attribute
from .....channel.models import Channel
from .....csv import ExportEvents
from .....csv.error_codes import ExportErrorCode
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
            errors {
                field
                code
                message
            }
        }
    }
"""

EXPORT_PRODUCTS_BY_APP_MUTATION = """
    mutation ExportProducts($input: ExportProductsInput!){
        exportProducts(input: $input){
            exportFile {
                id
                status
                createdAt
                updatedAt
                url
                app {
                    name
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_all_scope(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    query = EXPORT_PRODUCTS_MUTATION
    user = staff_api_client.user
    variables = {
        "input": {
            "scope": ExportScope.ALL.name,
            "exportInfo": {},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once_with(
        ANY, {"all": ""}, {}, FileTypeEnum.CSV.value
    )

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_filter_scope_with_channel(
    export_products_mock,
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    query = EXPORT_PRODUCTS_MUTATION
    user = staff_api_client.user
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    variables = {
        "input": {
            "scope": ExportScope.FILTER.name,
            "filter": {"isPublished": True},
            "exportInfo": {"channels": [channel_id]},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once_with(
        ANY,
        {"filter": {"is_published": True, "channel": channel_USD.slug}},
        {"channels": [str(channel_USD.pk)]},
        FileTypeEnum.CSV.value,
    )

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_by_app(
    export_products_mock,
    app_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    query = EXPORT_PRODUCTS_BY_APP_MUTATION
    app = app_api_client.app
    variables = {
        "input": {
            "scope": ExportScope.ALL.name,
            "exportInfo": {},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_products,
            permission_manage_apps,
        ],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    export_file_data = data["exportFile"]

    export_products_mock.assert_called_once_with(
        ANY, {"all": ""}, {}, FileTypeEnum.CSV.value
    )

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["app"]["name"] == app.name
    assert ExportEvent.objects.filter(
        user=None, app=app, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_ids_scope(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
):
    # given
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

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
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

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_ids_scope_invalid_object_type(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    query = EXPORT_PRODUCTS_MUTATION

    products = product_list[:2]

    ids = []
    for product in products:
        ids.append(graphene.Node.to_global_id("ProductVariant", product.pk))

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

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert not data["exportFile"]
    assert errors[0]["field"] == "ids"
    assert errors[0]["code"] == ExportErrorCode.GRAPHQL_ERROR.name

    export_products_mock.assert_not_called()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_with_warehouse_and_attribute_ids(
    export_products_mock,
    staff_api_client,
    product_list,
    channel_USD,
    channel_PLN,
    permission_manage_products,
    permission_manage_apps,
):
    # given
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

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
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

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_with_warehouse_ids_invalid_object_type(
    export_products_mock,
    staff_api_client,
    product_list,
    channel_USD,
    channel_PLN,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    query = EXPORT_PRODUCTS_MUTATION

    products = product_list[:2]

    ids = []
    for product in products:
        ids.append(graphene.Node.to_global_id("Product", product.pk))

    warehouse_pks = [str(warehouse.pk) for warehouse in Warehouse.objects.all()]
    channel_pks = [str(channel.pk) for channel in Channel.objects.all()]

    warehouse_ids = [
        graphene.Node.to_global_id("Attribute", pk) for pk in warehouse_pks
    ]
    channel_ids = [graphene.Node.to_global_id("Channel", pk) for pk in channel_pks]

    variables = {
        "input": {
            "scope": ExportScope.IDS.name,
            "ids": ids,
            "exportInfo": {
                "fields": [ProductFieldEnum.NAME.name],
                "warehouses": warehouse_ids,
                "attributes": [],
                "channels": channel_ids,
            },
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert not data["exportFile"]
    assert errors[0]["field"] == "warehouses"
    assert errors[0]["code"] == ExportErrorCode.GRAPHQL_ERROR.name

    export_products_mock.assert_not_called()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_with_attribute_ids_invalid_object_type(
    export_products_mock,
    staff_api_client,
    product_list,
    channel_USD,
    channel_PLN,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    query = EXPORT_PRODUCTS_MUTATION

    products = product_list[:2]

    ids = []
    for product in products:
        ids.append(graphene.Node.to_global_id("Product", product.pk))

    attribute_pks = [str(attr.pk) for attr in Attribute.objects.all()]
    channel_pks = [str(channel.pk) for channel in Channel.objects.all()]

    attribute_ids = [
        graphene.Node.to_global_id("Warehouse", pk) for pk in attribute_pks
    ]
    channel_ids = [graphene.Node.to_global_id("Channel", pk) for pk in channel_pks]

    variables = {
        "input": {
            "scope": ExportScope.IDS.name,
            "ids": ids,
            "exportInfo": {
                "fields": [ProductFieldEnum.NAME.name],
                "warehouses": [],
                "attributes": attribute_ids,
                "channels": channel_ids,
            },
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert not data["exportFile"]
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == ExportErrorCode.GRAPHQL_ERROR.name

    export_products_mock.assert_not_called()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_with_channel_ids_invalid_object_type(
    export_products_mock,
    staff_api_client,
    product_list,
    channel_USD,
    channel_PLN,
    permission_manage_products,
    permission_manage_apps,
):
    # given
    query = EXPORT_PRODUCTS_MUTATION

    products = product_list[:2]

    ids = []
    for product in products:
        ids.append(graphene.Node.to_global_id("Product", product.pk))

    attribute_pks = [str(attr.pk) for attr in Attribute.objects.all()]
    channel_pks = [str(channel.pk) for channel in Channel.objects.all()]

    attribute_ids = [
        graphene.Node.to_global_id("Attribute", pk) for pk in attribute_pks
    ]
    channel_ids = [graphene.Node.to_global_id("Warehouse", pk) for pk in channel_pks]

    variables = {
        "input": {
            "scope": ExportScope.IDS.name,
            "ids": ids,
            "exportInfo": {
                "fields": [ProductFieldEnum.NAME.name],
                "warehouses": [],
                "attributes": attribute_ids,
                "channels": channel_ids,
            },
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert not data["exportFile"]
    assert errors[0]["field"] == "channels"
    assert errors[0]["code"] == ExportErrorCode.GRAPHQL_ERROR.name

    export_products_mock.assert_not_called()


@pytest.mark.parametrize(
    ("input", "error_field"),
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
@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_mutation_failed(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    input,
    error_field,
):
    # given
    query = EXPORT_PRODUCTS_MUTATION
    user = staff_api_client.user
    variables = {"input": input}

    # when
    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    errors = data["errors"]

    export_products_mock.assert_not_called()

    assert data["errors"]
    assert errors[0]["field"] == error_field
    assert not ExportEvent.objects.filter(
        user=user, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.plugins.manager.PluginsManager.product_export_completed")
def test_export_products_webhooks(
    product_export_completed_mock,
    user_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
    media_root,
):
    # given
    query = EXPORT_PRODUCTS_MUTATION
    variables = {
        "input": {
            "scope": ExportScope.ALL.name,
            "exportInfo": {},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = user_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    assert not data["errors"]

    product_export_completed_mock.assert_called_once()


@pytest.mark.parametrize(
    "filter_input",
    [
        {"stockAvailability": "OUT_OF_STOCK"},
        {"isPublished": True},
        {"isAvailable": True},
        {"isVisibleInListing": True},
        {"price": {"gte": 10, "lte": 100}},
        {"minimalPrice": {"gte": 10, "lte": 100}},
    ],
)
@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_with_channel_dependent_filter_requires_channel(
    export_products_mock,
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_products,
    permission_manage_apps,
    filter_input,
):
    """Test that channel-dependent filters require exactly one channel in exportInfo."""
    # given
    query = EXPORT_PRODUCTS_MUTATION
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    variables = {
        "input": {
            "scope": ExportScope.FILTER.name,
            "filter": filter_input,
            "exportInfo": {"channels": [channel_id]},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    assert not data["errors"]
    assert data["exportFile"]["id"]

    # Verify channel slug was injected into the filter
    export_products_mock.assert_called_once()
    call_args = export_products_mock.call_args[0]
    scope = call_args[1]
    assert "filter" in scope
    assert scope["filter"]["channel"] == channel_USD.slug


@pytest.mark.parametrize(
    "filter_input",
    [
        {"stockAvailability": "OUT_OF_STOCK"},
        {"isPublished": True},
        {"isAvailable": True},
        {"isVisibleInListing": True},
        {"price": {"gte": 10, "lte": 100}},
        {"minimalPrice": {"gte": 10, "lte": 100}},
    ],
)
@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_with_channel_dependent_filter_no_channel_returns_error(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
    filter_input,
):
    """Test that channel-dependent filters fail when no channel is provided."""
    # given
    query = EXPORT_PRODUCTS_MUTATION
    variables = {
        "input": {
            "scope": ExportScope.FILTER.name,
            "filter": filter_input,
            "exportInfo": {},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "channels"
    assert errors[0]["code"] == ExportErrorCode.REQUIRED.name
    assert not data["exportFile"]

    export_products_mock.assert_not_called()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_with_channel_dependent_filter_multiple_channels_returns_error(
    export_products_mock,
    staff_api_client,
    product_list,
    channel_USD,
    channel_PLN,
    permission_manage_products,
    permission_manage_apps,
):
    """Test that channel-dependent filters fail when multiple channels are provided."""
    # given
    query = EXPORT_PRODUCTS_MUTATION
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel_USD.pk),
        graphene.Node.to_global_id("Channel", channel_PLN.pk),
    ]
    variables = {
        "input": {
            "scope": ExportScope.FILTER.name,
            "filter": {"stockAvailability": "OUT_OF_STOCK"},
            "exportInfo": {"channels": channel_ids},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "channels"
    assert errors[0]["code"] == ExportErrorCode.REQUIRED.name
    assert not data["exportFile"]

    export_products_mock.assert_not_called()


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_with_non_channel_filter_does_not_require_channel(
    export_products_mock,
    staff_api_client,
    product_list,
    collection,
    permission_manage_products,
    permission_manage_apps,
):
    """Test that non-channel-dependent filters work without providing a channel."""
    # given
    query = EXPORT_PRODUCTS_MUTATION
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "input": {
            "scope": ExportScope.FILTER.name,
            "filter": {"collections": [collection_id]},
            "exportInfo": {},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    assert not data["errors"]
    assert data["exportFile"]["id"]

    export_products_mock.assert_called_once()
    call_args = export_products_mock.call_args[0]
    scope = call_args[1]
    # Channel should not be in the filter since we used a non-channel filter
    assert "channel" not in scope.get("filter", {})


@patch("saleor.graphql.csv.mutations.export_products.export_products_task.delay")
def test_export_products_with_channel_dependent_filter_invalid_channel_returns_error(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    permission_manage_apps,
):
    """Test that channel-dependent filters fail when invalid channel ID is provided."""
    # given
    query = EXPORT_PRODUCTS_MUTATION
    invalid_channel_id = graphene.Node.to_global_id("Channel", 99999)
    variables = {
        "input": {
            "scope": ExportScope.FILTER.name,
            "filter": {"stockAvailability": "IN_STOCK"},
            "exportInfo": {"channels": [invalid_channel_id]},
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_products, permission_manage_apps],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["exportProducts"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "channels"
    assert errors[0]["code"] == ExportErrorCode.NOT_FOUND.name
    assert not data["exportFile"]

    export_products_mock.assert_not_called()
