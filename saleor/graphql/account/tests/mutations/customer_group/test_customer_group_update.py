import graphene

from ......account.models import CustomerGroup
from .....tests.utils import get_graphql_content

CUSTOMER_GROUP_UPDATE_MUTATION = """
mutation($id: ID!, $input: CustomerGroupUpdateInput!) {
    customerGroupUpdate(id: $id, input: $input) {
        errors {
            field
            message
        }
        customerGroup {
            id
            name
            customers(first: 10) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
}

"""


def test_customer_group_add_users(staff_api_client, permission_manage_users, user_list):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_users)
    name = "Test Customer Group"
    customer_group = CustomerGroup.objects.create(name=name)
    user_ids_to_add = [
        graphene.Node.to_global_id("User", user.pk) for user in user_list[1:3]
    ]

    variables = {
        "id": graphene.Node.to_global_id("CustomerGroup", customer_group.pk),
        "input": {
            "addCustomers": user_ids_to_add,
        },
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_GROUP_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    group_customers = [
        c["node"]
        for c in content["data"]["customerGroupUpdate"]["customerGroup"]["customers"][
            "edges"
        ]
    ]
    assert content["data"]["customerGroupUpdate"]["errors"] == []
    assert {c["id"] for c in group_customers} == set(user_ids_to_add)


def test_customer_group_remove_users(
    staff_api_client, permission_manage_users, user_list
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_users)
    name = "Test Customer Group"
    customer_group = CustomerGroup.objects.create(name=name)
    customer_group.customers.add(*user_list)
    customer_group.save()
    users_to_remove = user_list[1:3]
    user_ids_to_remove = [
        graphene.Node.to_global_id("User", user.pk) for user in users_to_remove
    ]
    remaining_user_ids = [
        graphene.Node.to_global_id("User", user.pk)
        for user in user_list
        if user not in users_to_remove
    ]

    variables = {
        "id": graphene.Node.to_global_id("CustomerGroup", customer_group.pk),
        "input": {
            "removeCustomers": user_ids_to_remove,
        },
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_GROUP_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    group_customers = [
        c["node"]
        for c in content["data"]["customerGroupUpdate"]["customerGroup"]["customers"][
            "edges"
        ]
    ]
    assert content["data"]["customerGroupUpdate"]["errors"] == []
    assert {c["id"] for c in group_customers} == set(remaining_user_ids)


def test_customer_group_update_without_permission(staff_api_client):
    # given
    customer_group = CustomerGroup.objects.create(name="Name")
    variables = {
        "id": graphene.Node.to_global_id("CustomerGroup", customer_group.pk),
        "input": {
            "name": "Test Customer Group",
        },
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_GROUP_UPDATE_MUTATION, variables)

    # then
    response_data = response.json()
    assert len(response_data["errors"]) == 1
    assert response_data["data"]["customerGroupUpdate"] is None
