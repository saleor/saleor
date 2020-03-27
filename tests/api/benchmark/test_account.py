from unittest.mock import MagicMock

import graphene
import pytest
from django.core.files import File

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
