import json

import graphene
import pytest

from tests.api.utils import get_graphql_content

PRIVATE_META_NAMESPACE = "TEST_NAMESPACE"
PUBLIC_META_NAMESPACE = "PUBLIC_NAMESPACE"


META_CLIENT = "TEST_PLUGIN"

PRIVATE_KEY = "name"
PRIVATE_VALUE = "Bond"

PUBLIC_KEY = "purpose"
PUBLIC_VALUE = "42"


@pytest.fixture
def customer_with_meta(customer_user):
    customer_user.store_private_meta(
        namespace=PRIVATE_META_NAMESPACE,
        client=META_CLIENT,
        item={PRIVATE_KEY: PRIVATE_VALUE},
    )
    customer_user.store_meta(
        namespace=PUBLIC_META_NAMESPACE,
        client=META_CLIENT,
        item={PUBLIC_KEY: PUBLIC_VALUE},
    )
    customer_user.save()
    return customer_user


GET_PRIVATE_META_QUERY = """
    query UserMeta($id: ID!) {
        user(id: $id) {
            email
            privateMeta {
                namespace
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
    response = staff_api_client.post_graphql(
        GET_PRIVATE_META_QUERY, variables, permissions=[permission_manage_users]
    )
    meta = get_graphql_content(response)["data"]["user"]["privateMeta"][0]

    assert meta["namespace"] == PRIVATE_META_NAMESPACE
    assert meta["clients"] == [
        {
            "metadata": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}],
            "name": META_CLIENT,
        }
    ]


MY_PRIVATE_META_QUERY = """
    {
        me {
            email
            privateMeta {
                namespace
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
    assert data["data"]["me"] is None


UPDATE_PRIVATE_METADATA_MUTATION = """
    mutation TokenCreate($id: ID!, $input: MetaInput!) {
      userUpdatePrivateMetadata(
        id: $id
        input: $input
      ) {
        user {
          privateMeta {
            namespace
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
    }
"""


def test_update_private_metadata_through_mutation(
    staff_api_client, permission_manage_users, customer_with_meta
):
    NEW_VALUE = "NEW_VALUE"
    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    variables = {
        "id": user_id,
        "input": {
            "namespace": PRIVATE_META_NAMESPACE,
            "clientName": META_CLIENT,
            "key": PRIVATE_KEY,
            "value": NEW_VALUE,
        },
    }
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    meta = get_graphql_content(response)["data"]["userUpdatePrivateMetadata"]["user"][
        "privateMeta"
    ][0]

    assert meta["namespace"] == PRIVATE_META_NAMESPACE
    assert meta["clients"] == [
        {"metadata": [{"key": PRIVATE_KEY, "value": NEW_VALUE}], "name": META_CLIENT}
    ]


def test_add_new_key_value_pair_to_private_metadata_using_mutation(
    staff_api_client, permission_manage_users, customer_with_meta
):
    NEW_KEY = "NEW_KEY"
    NEW_VALUE = "NEW_VALUE"
    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    variables = {
        "id": user_id,
        "input": {
            "namespace": PRIVATE_META_NAMESPACE,
            "clientName": META_CLIENT,
            "key": NEW_KEY,
            "value": NEW_VALUE,
        },
    }
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    meta = get_graphql_content(response)["data"]["userUpdatePrivateMetadata"]["user"][
        "privateMeta"
    ][0]

    expected_metadata = [
        {"key": NEW_KEY, "value": NEW_VALUE},
        {"key": PRIVATE_KEY, "value": PRIVATE_VALUE},
    ]
    assert meta["namespace"] == PRIVATE_META_NAMESPACE
    assert meta["clients"] == [{"metadata": expected_metadata, "name": META_CLIENT}]


CLEAR_METADATA_MUTATION = """
    mutation UserClearStoredMetadata($id: ID!, $input: MetaPath!) {
      userClearStoredMetadata(
        id: $id
        input: $input
      ) {
        user {
          privateMeta {
            namespace
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
    }
"""


def test_clear_private_metadata_through_mutation(
    staff_api_client, permission_manage_users, customer_with_meta
):
    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    variables = {
        "id": user_id,
        "input": {
            "namespace": PRIVATE_META_NAMESPACE,
            "clientName": META_CLIENT,
            "key": PRIVATE_KEY,
        },
    }
    response = staff_api_client.post_graphql(
        CLEAR_METADATA_MUTATION, variables, permissions=[permission_manage_users]
    )
    meta = get_graphql_content(response)["data"]["userClearStoredMetadata"]["user"][
        "privateMeta"
    ][0]

    assert meta["namespace"] == PRIVATE_META_NAMESPACE
    assert meta["clients"] == []


def test_clear_silently_private_metadata_from_nonexistent_client(
    staff_api_client, permission_manage_users, customer_with_meta
):
    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    WRONG_CLIENT = "WONG"
    variables = {
        "id": user_id,
        "input": {
            "namespace": PRIVATE_META_NAMESPACE,
            "clientName": WRONG_CLIENT,
            "key": PRIVATE_KEY,
        },
    }
    response = staff_api_client.post_graphql(
        CLEAR_METADATA_MUTATION, variables, permissions=[permission_manage_users]
    )
    meta = get_graphql_content(response)["data"]["userClearStoredMetadata"]["user"][
        "privateMeta"
    ][0]

    assert meta["namespace"] == PRIVATE_META_NAMESPACE
    assert meta["clients"] == [
        {
            "metadata": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}],
            "name": META_CLIENT,
        }
    ]


MY_PUBLIC_META_QUERY = """
    {
        me {
            email
            meta {
                namespace
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


def test_access_users_public_metadata(user_api_client, customer_with_meta):
    response = user_api_client.post_graphql(MY_PUBLIC_META_QUERY)
    data = json.loads(response.content.decode("utf8"))
    assert "errors" not in data

    meta = get_graphql_content(response)["data"]["me"]["meta"][0]
    assert meta["namespace"] == PUBLIC_META_NAMESPACE
    assert meta["clients"] == [
        {"metadata": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}], "name": META_CLIENT}
    ]


GET_META_QUERY = """
    query UserMeta($id: ID!) {
        user(id: $id) {
            email
            meta {
                namespace
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


def test_staff_access_to_public_metadata(
    staff_api_client, permission_manage_users, customer_with_meta
):
    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    variables = {"id": user_id}
    response = staff_api_client.post_graphql(
        GET_META_QUERY, variables, permissions=[permission_manage_users]
    )
    meta = get_graphql_content(response)["data"]["user"]["meta"][0]

    assert meta["namespace"] == PUBLIC_META_NAMESPACE
    assert meta["clients"] == [
        {"metadata": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}], "name": META_CLIENT}
    ]


UPDATE_METADATA_MUTATION = """
    mutation TokenCreate($id: ID!, $input: MetaInput!) {
      userUpdateMetadata(
        id: $id
        input: $input
      ) {
        user {
          meta {
            namespace
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
    }
"""


def test_update_metadata_through_mutation(user_api_client, customer_with_meta):
    NEW_VALUE = "NEW_VALUE"
    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    variables = {
        "id": user_id,
        "input": {
            "namespace": PUBLIC_META_NAMESPACE,
            "clientName": META_CLIENT,
            "key": PUBLIC_KEY,
            "value": NEW_VALUE,
        },
    }
    resp = user_api_client.post_graphql(UPDATE_METADATA_MUTATION, variables)
    meta = get_graphql_content(resp)["data"]["userUpdateMetadata"]["user"]["meta"][0]

    assert meta["namespace"] == PUBLIC_META_NAMESPACE
    assert meta["clients"] == [
        {"metadata": [{"key": PUBLIC_KEY, "value": NEW_VALUE}], "name": META_CLIENT}
    ]


def test_add_new_key_value_pair_to_metadata_using_mutation(
    user_api_client, customer_with_meta
):
    NEW_KEY = "NEW_KEY"
    NEW_VALUE = "NEW_VALUE"
    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    variables = {
        "id": user_id,
        "input": {
            "namespace": PUBLIC_META_NAMESPACE,
            "clientName": META_CLIENT,
            "key": NEW_KEY,
            "value": NEW_VALUE,
        },
    }
    response = user_api_client.post_graphql(UPDATE_METADATA_MUTATION, variables)
    meta = get_graphql_content(response)["data"]["userUpdateMetadata"]["user"]["meta"][
        0
    ]

    expected_metadata = [
        {"key": NEW_KEY, "value": NEW_VALUE},
        {"key": PUBLIC_KEY, "value": PUBLIC_VALUE},
    ]
    assert meta["namespace"] == PUBLIC_META_NAMESPACE
    assert meta["clients"] == [{"metadata": expected_metadata, "name": META_CLIENT}]


def test_add_new_namespace_metadata_using_mutation(user_api_client, customer_with_meta):
    NEW_KEY = "NEW_KEY"
    NEW_VALUE = "NEW_VALUE"
    NEW_NAMESPACE = "NEW_NAMESPACE"
    NEW_CLIENT = "NEW_CLIENT"

    user_id = graphene.Node.to_global_id("User", customer_with_meta.id)
    variables = {
        "id": user_id,
        "input": {
            "namespace": NEW_NAMESPACE,
            "clientName": NEW_CLIENT,
            "key": NEW_KEY,
            "value": NEW_VALUE,
        },
    }
    response = user_api_client.post_graphql(UPDATE_METADATA_MUTATION, variables)
    meta = get_graphql_content(response)["data"]["userUpdateMetadata"]["user"]["meta"]

    assert meta[0]["namespace"] == NEW_NAMESPACE
    assert meta[0]["clients"] == [
        {"metadata": [{"key": NEW_KEY, "value": NEW_VALUE}], "name": NEW_CLIENT}
    ]
    assert meta[1]["namespace"] == PUBLIC_META_NAMESPACE
    assert meta[1]["clients"] == [
        {"metadata": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}], "name": META_CLIENT}
    ]
