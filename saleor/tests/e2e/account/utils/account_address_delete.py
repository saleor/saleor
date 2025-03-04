from ...utils import get_graphql_content

ACCOUNT_ADDRESS_DELETE_MUTATION = """
    mutation deleteUserAddress($id: ID!) {
        accountAddressDelete(id: $id) {
            address {
                city
            }
            user {
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


def account_address_delete(api_client, id):
    variables = {"id": id}

    response = api_client.post_graphql(
        ACCOUNT_ADDRESS_DELETE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["accountAddressDelete"]

    user_id = data["user"]["id"]
    errors = data["errors"]

    assert errors == []
    assert user_id is not None

    return data
