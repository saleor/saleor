from tests.api.utils import get_graphql_content

GET_PRIVATE_META_QUERY = """
    query UserMeta($id: ID!) {
        user(id: $id) {
            email
            privateMeta {
                label
                clients {
                    name
                    metadata {
                        key
                        value
                    }
                }
            }
        }
    }
"""


def test_get_private_meta(staff_api_client, permission_manage_users, customer_user):
    variables = {"id": customer_user.id}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(GET_PRIVATE_META_QUERY, variables)
    content = get_graphql_content(response)
