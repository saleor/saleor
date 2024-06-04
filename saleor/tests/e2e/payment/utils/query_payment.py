from ...utils import get_graphql_content

PAYMENT_QUERY = """
    query payment($id: ID!) {
        payment(id: $id) {
            id
            isActive
            checkout {
                token
            }
        }
    }
"""


def get_payment(
    api_client,
    payment_id,
):
    variables = {"id": payment_id}

    response = api_client.post_graphql(PAYMENT_QUERY, variables)
    content = get_graphql_content(response)

    return content["data"]["payment"]
