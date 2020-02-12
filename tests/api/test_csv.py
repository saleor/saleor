from unittest.mock import ANY, patch

import graphene
import pytest

from saleor.graphql.csv.enums import ExportScope
from tests.api.utils import get_graphql_content

EXPORT_PRODUCTS_MUTATION = """
    mutation ExportProducts($input: ExportProductsInput!){
        exportProducts(input: $input){
            job {
                id
                status
                createdAt
                endedAt
                url
                user {
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
        ({"scope": ExportScope.ALL.name}, {"all": ""}),
        (
            {"scope": ExportScope.FILTER.name, "filter": {"isPublished": True}},
            {"filter": {"is_published": True}},
        ),
    ],
)
@patch("saleor.graphql.csv.mutations.export_products.delay")
def test_export_products_mutation(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    input,
    called_data,
):
    query = EXPORT_PRODUCTS_MUTATION
    variables = {"input": input}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]

    export_products_mock.assert_called_once_with(called_data, ANY)

    assert not data["csvErrors"]
    assert data["job"]["id"]


@patch("saleor.graphql.csv.mutations.export_products.delay")
def test_export_products_mutation_ids_scope(
    export_products_mock, staff_api_client, product_list, permission_manage_products
):
    query = EXPORT_PRODUCTS_MUTATION

    products = product_list[:2]

    ids = []
    pks = set()
    for product in products:
        pks.add(str(product.pk))
        ids.append(graphene.Node.to_global_id("Product", product.pk))

    variables = {"input": {"scope": ExportScope.IDS.name, "ids": ids}}

    response = staff_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["exportProducts"]

    export_products_mock.assert_called_once()
    (call_args, call_kwargs,) = export_products_mock.call_args

    assert set(call_args[0]["ids"]) == pks

    assert not data["csvErrors"]
    assert data["job"]["id"]


@pytest.mark.parametrize(
    "input, error_field",
    [
        ({"scope": ExportScope.FILTER.name}, "filter"),
        ({"scope": ExportScope.IDS.name}, "ids"),
    ],
)
@patch("saleor.graphql.csv.mutations.export_products.delay")
def test_export_products_mutation_failed(
    export_products_mock,
    staff_api_client,
    product_list,
    permission_manage_products,
    input,
    error_field,
):
    query = EXPORT_PRODUCTS_MUTATION
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
