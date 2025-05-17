from ......account.models import CustomerGroup
from .....tests.utils import get_graphql_content

CUSTOMER_GROUP_CREATE_MUTATION = """
mutation($input: CustomerGroupInput!) {
    customerGroupCreate(input: $input) {
        errors {
            field
            message
        }
        customerGroup {
            id
            name
        }
    }
}

"""


def test_customer_group_create(staff_api_client, permission_manage_users):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_users)
    variables = {
        "input": {
            "name": "Test Customer Group",
        }
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_GROUP_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["customerGroupCreate"]["errors"] == []
    assert (
        content["data"]["customerGroupCreate"]["customerGroup"]["name"]
        == variables["input"]["name"]
    )


def test_customer_group_create_with_existing_name(
    staff_api_client, permission_manage_users
):
    # given
    name = "Test Customer Group"
    customer_group = CustomerGroup.objects.create(name=name)
    staff_api_client.user.user_permissions.add(permission_manage_users)
    variables = {
        "input": {
            "name": customer_group.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_GROUP_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["customerGroupCreate"]["errors"]) == 1
    error = content["data"]["customerGroupCreate"]["errors"][0]
    assert error["field"] == "name"


def test_customer_group_create_without_permission(staff_api_client):
    # given
    variables = {
        "input": {
            "name": "Test Customer Group",
        }
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_GROUP_CREATE_MUTATION, variables)

    # then
    response_data = response.json()
    assert len(response_data["errors"]) == 1
    assert response_data["data"]["customerGroupCreate"] is None
