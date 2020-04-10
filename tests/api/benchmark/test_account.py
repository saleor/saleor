from unittest.mock import MagicMock

import graphene
import pytest
from django.contrib.auth.models import Group
from django.core.files import File

from saleor.account.models import User
from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_staff_user(
    staff_api_client,
    address,
    permission_manage_users,
    media_root,
    permission_group_manage_users,
    permission_manage_orders,
    permission_manage_products,
    permission_manage_staff,
    count_queries,
):
    group = permission_group_manage_users
    group.permissions.add(permission_manage_products)

    staff_user = group.user_set.first()
    staff_user.user_permissions.add(permission_manage_orders, permission_manage_staff)
    staff_user.addresses.add(address.get_copy())

    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    staff_user.avatar = avatar_mock
    staff_user.save()

    # update query in #5389 (deprecated 'permissions' field)
    query = """
        query User($id: ID!) {
            user(id: $id) {
                email
                firstName
                lastName
                isStaff
                isActive
                addresses {
                    id
                    isDefaultShippingAddress
                    isDefaultBillingAddress
                }
                orders {
                    totalCount
                }
                dateJoined
                lastLogin
                defaultShippingAddress {
                    firstName
                    lastName
                    companyName
                    streetAddress1
                    streetAddress2
                    city
                    cityArea
                    postalCode
                    countryArea
                    phone
                    country {
                        code
                    }
                    isDefaultShippingAddress
                    isDefaultBillingAddress
                }
                defaultBillingAddress {
                    firstName
                    lastName
                    companyName
                    streetAddress1
                    streetAddress2
                    city
                    cityArea
                    postalCode
                    countryArea
                    phone
                    country {
                        code
                    }
                    isDefaultShippingAddress
                    isDefaultBillingAddress
                }
                avatar {
                    url
                }
                permissions {
                    code
                    name
                }
                userPermissions {
                    code
                    name
                }
                permissionGroups {
                    name
                    permissions {
                        code
                    }
                }
            }
        }
    """
    user_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {"id": user_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert data


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_staff_create(
    staff_api_client,
    staff_user,
    media_root,
    permission_group_manage_users,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_users,
    count_queries,
):
    query = """
        mutation CreateStaff(
                $email: String, $redirect_url: String, $add_groups: [ID!]
            ) {
            staffCreate(input: {email: $email, redirectUrl: $redirect_url,
                    addGroups: $add_groups }) {
                staffErrors {
                    field
                    code
                    permissions
                    groups
                }
                user {
                    id
                    email
                    isStaff
                    isActive
                    userPermissions {
                        code
                    }
                    permissions {
                        code
                    }
                    permissionGroups {
                        name
                        permissions {
                            code
                        }
                    }
                    avatar {
                        url
                    }
                }
            }
        }
    """
    group = permission_group_manage_users
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    email = "api_user@example.com"
    variables = {
        "email": email,
        "redirect_url": "https://www.example.com",
        "add_groups": [graphene.Node.to_global_id("Group", group.pk)],
    }

    staff_count = User.objects.filter(is_staff=True).count()
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]

    assert User.objects.filter(is_staff=True).count() == staff_count + 1
    assert data["user"]
    assert not data["staffErrors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_staff_update_groups_and_permissions(
    staff_api_client,
    staff_users,
    media_root,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
    permission_manage_products,
    count_queries,
):
    query = """
    mutation UpdateStaff(
                $id: ID!, $input: StaffUpdateInput!) {
            staffUpdate(
                    id: $id,
                    input: $input) {
                staffErrors {
                    field
                    code
                    message
                    permissions
                    groups
                }
                user {
                    userPermissions {
                        code
                    }
                    permissions {
                        code
                    }
                    permissionGroups {
                        name
                    }
                    isActive
                }
            }
        }
    """
    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage staff"),
            Group(name="manage orders and products"),
        ]
    )
    group1, group2, group3 = groups
    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders, permission_manage_products)

    staff_user, staff_user1, staff_user2 = staff_users
    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2, staff_user1)
    group3.user_set.add(staff_user2)

    id = graphene.Node.to_global_id("User", staff_user1.id)
    variables = {
        "id": id,
        "input": {
            "addGroups": [
                graphene.Node.to_global_id("Group", gr.pk) for gr in [group2, group3]
            ],
            "removeGroups": [graphene.Node.to_global_id("Group", group1.pk)],
        },
    }

    staff_api_client.user.user_permissions.add(
        permission_manage_users, permission_manage_orders, permission_manage_products
    )

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["staffErrors"] == []
    assert len(data["user"]["userPermissions"]) == 3
    assert {perm["code"].lower() for perm in data["user"]["userPermissions"]} == {
        permission_manage_orders.codename,
        permission_manage_products.codename,
        permission_manage_staff.codename,
    }
    assert len(data["user"]["permissionGroups"]) == 2
    assert {group["name"] for group in data["user"]["permissionGroups"]} == {
        group2.name,
        group3.name,
    }
    # deprecated, to remove in #5389
    assert len(data["user"]["permissions"]) == 3
    assert {perm["code"].lower() for perm in data["user"]["permissions"]} == {
        permission_manage_orders.codename,
        permission_manage_products.codename,
        permission_manage_staff.codename,
    }


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_delete_staff_members(
    staff_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
    count_queries,
):
    """Ensure user can delete users when all permissions will be manageable."""
    query = """
        mutation staffBulkDelete($ids: [ID]!) {
            staffBulkDelete(ids: $ids) {
                count
                staffErrors{
                    code
                    field
                    permissions
                    users
                }
            }
        }
    """

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage staff"),
            Group(name="manage users and orders"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders, permission_manage_users)

    staff_user, staff_user1, staff_user2 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1, staff_user)
    group3.user_set.add(staff_user1, staff_user)

    staff_user.user_permissions.add(
        permission_manage_users, permission_manage_orders, permission_manage_staff
    )
    variables = {
        "ids": [
            graphene.Node.to_global_id("User", user.id)
            for user in [staff_user1, staff_user2]
        ]
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffBulkDelete"]
    errors = data["staffErrors"]

    assert not errors
    assert data["count"] == 2
    assert not User.objects.filter(
        id__in=[user.id for user in [staff_user1, staff_user2]]
    ).exists()
