from ...account.utils.fragments import ADDRESS_FRAGMENT
from ...utils import get_graphql_content

USER_QUERY = (
    """
    query User($id: ID!) {
        user(id: $id) {
            id
            email
            firstName
            lastName
            isStaff
            isActive
            isConfirmed
            addresses {
                ...Address
            }
            checkoutIds
            orders(first: 10) {
                totalCount
                edges {
                    node {
                        id
                        number
                    }
                }
            }
            defaultShippingAddress {
                ...Address
            }
            defaultBillingAddress {
                ...Address
            }
        }
    }
"""
    + ADDRESS_FRAGMENT
)


def get_user(
    staff_api_client,
    user_id,
):
    variables = {"id": user_id}

    response = staff_api_client.post_graphql(
        USER_QUERY,
        variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["user"]

    return data
