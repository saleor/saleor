from ...tests.utils import get_graphql_content

QUERY_CHECKOUT = """
query getCheckout($token: UUID!) {
    checkout(token: $token) {
        token
    }
}
"""


def test_uuid_scalar_value_passed_as_variable(api_client, checkout):
    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_uuid_scalar_wrong_value_passed_as_variable(api_client, checkout):
    variables = {"token": "wrong-token"}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_uuid_scalar_value_passed_in_input(api_client, checkout):
    token = checkout.token

    query = f"""
        query{{
            checkout(token: "{token}") {{
                token
            }}
        }}
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_uuid_scalar_wrong_value_passed_in_input(api_client, checkout):
    token = "wrong-token"

    query = f"""
        query{{
            checkout(token: "{token}") {{
                token
            }}
        }}
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1
