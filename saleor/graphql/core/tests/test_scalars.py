from ...tests.utils import get_graphql_content

QUERY_CHECKOUT = """
query getCheckout($token: UUID!, $channel: String!) {
    checkout(token: $token, channel: $channel) {
        token
    }
}
"""


def test_uuid_scalar_value_passed_as_variable(api_client, checkout):
    variables = {"token": str(checkout.token), "channel": checkout.channel.slug}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_uuid_scalar_wrong_value_passed_as_variable(api_client, checkout):
    variables = {"token": "wrong-token", "channel": checkout.channel.slug}
    response = api_client.post_graphql(QUERY_CHECKOUT, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_uuid_scalar_value_passed_in_input(api_client, checkout):
    token = checkout.token
    channel_slug = checkout.channel.slug

    query = f"""
        query{{
            checkout(token: "{token}", channel: "{channel_slug}") {{
                token
            }}
        }}
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["token"] == str(checkout.token)


def test_uuid_scalar_wrong_value_passed_in_input(api_client, checkout):
    token = "wrong-token"
    channel_slug = checkout.channel.slug

    query = f"""
        query{{
            checkout(token: "{token}", channel: "{channel_slug}") {{
                token
            }}
        }}
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1
