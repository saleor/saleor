import graphene
import json
import pytest
from tests.api.utils import get_graphql_content

META_LABEL = "TEST_LABEL"
META_CLIENT = "TEST_PLUGIN"

KEY = "name"
VALUE = "Bond"


@pytest.fixture
def customer_with_meta(customer_user):
    customer_user.store_private_meta(META_LABEL, META_CLIENT, {KEY: VALUE})
    customer_user.save()
    return customer_user


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


def test_get_private_meta(
    staff_api_client, permission_manage_users, customer_with_meta
):
    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    variables = {"id": user_id}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(GET_PRIVATE_META_QUERY, variables)
    meta = get_graphql_content(response)["data"]["user"]["privateMeta"][0]

    assert meta["label"] == META_LABEL
    assert meta["clients"] == [
        {"metadata": [{"key": KEY, "value": VALUE}], "name": META_CLIENT}
    ]


MY_PRIVATE_META_QUERY = """
    {
        me {
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


def test_user_has_no_access_to_private_meta(user_api_client, customer_with_meta):
    response = user_api_client.post_graphql(MY_PRIVATE_META_QUERY)
    data = json.loads(response.content.decode("utf8"))
    assert data["errors"] is not None
    assert data["data"]["me"]["privateMeta"] is None
