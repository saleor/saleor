import graphene

from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_VOUCHER_BY_ID = """
    query Voucher($id: ID!) {
        voucher(id: $id) {
            id
            codes(first: 10){
                edges {
                    node {
                        code
                    }
                }
                pageInfo{
                    startCursor
                    endCursor
                    hasNextPage
                    hasPreviousPage
                }
            }
            name
            discountValue
        }
    }
"""


def test_staff_query_voucher(staff_api_client, voucher, permission_manage_discounts):
    # given
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucher"]

    # then
    assert data["name"] == voucher.name
    assert data["codes"]["edges"][0]["node"]["code"] == voucher.codes.first().code


def test_query_voucher_by_app(app_api_client, voucher, permission_manage_discounts):
    # given
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucher"]

    # then
    assert data["name"] == voucher.name
    assert data["codes"]["edges"][0]["node"]["code"] == voucher.codes.first().code


def test_query_voucher_by_customer(api_client, voucher, permission_manage_discounts):
    # given
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = api_client.post_graphql(QUERY_VOUCHER_BY_ID, variables)

    # then
    assert_no_permission(response)


def test_staff_query_voucher_by_invalid_id(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    id = "bh/"
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content_from_response(response)

    # then
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Voucher."
    assert content["data"]["voucher"] is None


def test_staff_query_voucher_with_invalid_object_type(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", voucher.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["voucher"] is None
