import graphene

from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

ADDRESS_QUERY = """
query address($id: ID!) {
    address(id: $id) {
        postalCode
        lastName
        firstName
        city
        country {
          code
        }
    }
}
"""


def test_address_query_as_owner(user_api_client, customer_user):
    address = customer_user.addresses.first()
    variables = {"id": graphene.Node.to_global_id("Address", address.pk)}
    response = user_api_client.post_graphql(ADDRESS_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["address"]
    assert data["country"]["code"] == address.country.code


def test_address_query_as_not_owner(
    user_api_client, customer_user, address_other_country
):
    variables = {"id": graphene.Node.to_global_id("Address", address_other_country.pk)}
    response = user_api_client.post_graphql(ADDRESS_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["address"]
    assert not data


def test_address_query_as_app_with_permission(
    app_api_client,
    address_other_country,
    permission_manage_users,
):
    variables = {"id": graphene.Node.to_global_id("Address", address_other_country.pk)}
    response = app_api_client.post_graphql(
        ADDRESS_QUERY, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["address"]
    assert data["country"]["code"] == address_other_country.country.code


def test_address_query_as_app_without_permission(
    app_api_client, app, address_other_country
):
    variables = {"id": graphene.Node.to_global_id("Address", address_other_country.pk)}
    response = app_api_client.post_graphql(ADDRESS_QUERY, variables)
    assert_no_permission(response)


def test_address_query_as_anonymous_user(api_client, address_other_country):
    variables = {"id": graphene.Node.to_global_id("Address", address_other_country.pk)}
    response = api_client.post_graphql(ADDRESS_QUERY, variables)
    assert_no_permission(response)


def test_address_query_invalid_id(
    staff_api_client,
    address_other_country,
):
    id = "..afs"
    variables = {"id": id}
    response = staff_api_client.post_graphql(ADDRESS_QUERY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["address"] is None


def test_address_query_with_invalid_object_type(
    staff_api_client,
    address_other_country,
):
    variables = {"id": graphene.Node.to_global_id("Order", address_other_country.pk)}
    response = staff_api_client.post_graphql(ADDRESS_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["address"] is None


ADDRESS_FEDERATION_QUERY = """
  query GetUserInFederation($representations: [_Any]) {
    _entities(representations: $representations) {
      __typename
      ... on Address {
        id
        city
      }
    }
  }
"""


def test_customer_query_address_federation(user_api_client, customer_user, address):
    customer_user.addresses.add(address)

    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "representations": [
            {
                "__typename": "Address",
                "id": address_id,
            },
        ],
    }

    response = user_api_client.post_graphql(ADDRESS_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Address",
            "id": address_id,
            "city": address.city,
        }
    ]


def test_customer_query_other_user_address_federation(
    user_api_client, staff_user, customer_user, address
):
    staff_user.addresses.add(address)

    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "representations": [
            {
                "__typename": "Address",
                "id": address_id,
            },
        ],
    }

    response = user_api_client.post_graphql(ADDRESS_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_staff_query_other_user_address_federation(
    staff_api_client, customer_user, address
):
    customer_user.addresses.add(address)

    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "representations": [
            {
                "__typename": "Address",
                "id": address_id,
            },
        ],
    }

    response = staff_api_client.post_graphql(ADDRESS_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_staff_query_other_user_address_with_permission_federation(
    staff_api_client, customer_user, address, permission_manage_users
):
    customer_user.addresses.add(address)

    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "representations": [
            {
                "__typename": "Address",
                "id": address_id,
            },
        ],
    }

    response = staff_api_client.post_graphql(
        ADDRESS_FEDERATION_QUERY,
        variables,
        permissions=[permission_manage_users],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_app_query_address_federation(app_api_client, address, permission_manage_users):
    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "representations": [
            {
                "__typename": "Address",
                "id": address_id,
            },
        ],
    }

    response = app_api_client.post_graphql(
        ADDRESS_FEDERATION_QUERY,
        variables,
        permissions=[permission_manage_users],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Address",
            "id": address_id,
            "city": address.city,
        }
    ]


def test_app_no_permission_query_address_federation(app_api_client, address):
    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "representations": [
            {
                "__typename": "Address",
                "id": address_id,
            },
        ],
    }

    response = app_api_client.post_graphql(ADDRESS_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_unauthenticated_query_address_federation(api_client, address):
    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "representations": [
            {
                "__typename": "Address",
                "id": address_id,
            },
        ],
    }

    response = api_client.post_graphql(ADDRESS_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]
