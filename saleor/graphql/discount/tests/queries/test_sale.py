import graphene

from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_SALE_BY_ID = """
    query Sale($id: ID!) {
        sale(id: $id) {
            id
            name
            type
            discountValue
        }
    }
"""


def test_staff_query_sale(staff_api_client, sale, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}
    response = staff_api_client.post_graphql(
        QUERY_SALE_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["sale"]["name"] == sale.name
    assert content["data"]["sale"]["type"] == sale.type.upper()


def test_query_sale_by_app(app_api_client, sale, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}
    response = app_api_client.post_graphql(
        QUERY_SALE_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["sale"]["name"] == sale.name
    assert content["data"]["sale"]["type"] == sale.type.upper()


def test_query_sale_by_customer(api_client, sale, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}
    response = api_client.post_graphql(QUERY_SALE_BY_ID, variables)
    assert_no_permission(response)


def test_staff_query_sale_by_invalid_id(
    staff_api_client, sale, permission_manage_discounts
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_SALE_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["sale"] is None


def test_staff_query_sale_with_invalid_object_type(
    staff_api_client, sale, permission_manage_discounts
):
    variables = {"id": graphene.Node.to_global_id("Order", sale.pk)}
    response = staff_api_client.post_graphql(
        QUERY_SALE_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["sale"] is None
