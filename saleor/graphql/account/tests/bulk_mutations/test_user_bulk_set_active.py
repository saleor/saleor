import graphene

from .....account.models import User
from ....tests.utils import get_graphql_content

USER_CHANGE_ACTIVE_STATUS_MUTATION = """
    mutation userChangeActiveStatus($ids: [ID!]!, $is_active: Boolean!) {
        userBulkSetActive(ids: $ids, isActive: $is_active) {
            count
            errors {
                field
                message
            }
        }
    }
    """


def test_staff_bulk_set_active(
    staff_api_client, user_list_not_active, permission_manage_users
):
    users = user_list_not_active
    active_status = True
    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in users],
        "is_active": active_status,
    }
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["userBulkSetActive"]
    assert data["count"] == users.count()
    users = User.objects.filter(pk__in=[user.pk for user in users])
    assert all(user.is_active for user in users)


def test_staff_bulk_set_not_active(
    staff_api_client, user_list, permission_manage_users
):
    users = user_list
    active_status = False
    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in users],
        "is_active": active_status,
    }
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["userBulkSetActive"]
    assert data["count"] == len(users)
    users = User.objects.filter(pk__in=[user.pk for user in users])
    assert not any(user.is_active for user in users)


def test_change_active_status_for_superuser(
    staff_api_client, superuser, permission_manage_users
):
    users = [superuser]
    superuser_id = graphene.Node.to_global_id("User", superuser.id)
    active_status = False
    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in users],
        "is_active": active_status,
    }
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["userBulkSetActive"]
    assert data["errors"][0]["field"] == superuser_id
    assert (
        data["errors"][0]["message"] == "Cannot activate or deactivate "
        "superuser's account."
    )


def test_change_active_status_for_himself(staff_api_client, permission_manage_users):
    users = [staff_api_client.user]
    user_id = graphene.Node.to_global_id("User", staff_api_client.user.id)
    active_status = False
    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in users],
        "is_active": active_status,
    }
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["userBulkSetActive"]
    assert data["errors"][0]["field"] == user_id
    assert (
        data["errors"][0]["message"] == "Cannot activate or deactivate "
        "your own account."
    )
