import json
from collections import defaultdict
from unittest.mock import Mock, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.models import Group, User
from ......core.utils.json_serializer import CustomJsonEncoder
from ......permission.enums import AccountPermissions, OrderPermissions
from ......webhook.event_types import WebhookEventAsyncType
from ......webhook.payloads import generate_meta, generate_requestor
from .....tests.utils import assert_no_permission, get_graphql_content
from ....mutations.staff import StaffDelete, StaffUpdate
from ....mutations.staff.base import UserDelete

STAFF_DELETE_MUTATION = """
        mutation DeleteStaff($id: ID!) {
            staffDelete(id: $id) {
                errors {
                    field
                    code
                    message
                    permissions
                }
                user {
                    id
                }
            }
        }
    """


def test_staff_delete(staff_api_client, permission_manage_staff):
    query = STAFF_DELETE_MUTATION
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": user_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]
    assert data["errors"] == []
    assert not User.objects.filter(pk=staff_user.id).exists()


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_staff_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_staff,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": user_id}

    # when
    response = staff_api_client.post_graphql(
        STAFF_DELETE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]

    # then
    assert not data["errors"]
    assert not User.objects.filter(pk=staff_user.id).exists()
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("User", staff_user.id),
                "email": staff_user.email,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.STAFF_DELETED,
        [any_webhook],
        staff_user,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


@patch("saleor.account.signals.delete_from_storage_task.delay")
def test_staff_delete_with_avatar(
    delete_from_storage_task_mock,
    staff_api_client,
    image,
    permission_manage_staff,
    media_root,
):
    query = STAFF_DELETE_MUTATION
    staff_user = User.objects.create(
        email="staffuser@example.com", avatar=image, is_staff=True
    )
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": user_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]
    assert data["errors"] == []
    assert not User.objects.filter(pk=staff_user.id).exists()
    delete_from_storage_task_mock.assert_called_once_with(staff_user.avatar.name)


def test_staff_delete_app_no_permission(app_api_client, permission_manage_staff):
    query = STAFF_DELETE_MUTATION
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": user_id}

    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    assert_no_permission(response)


def test_staff_delete_out_of_scope_user(
    staff_api_client,
    superuser_api_client,
    permission_manage_staff,
    permission_manage_products,
):
    query = STAFF_DELETE_MUTATION
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    staff_user.user_permissions.add(permission_manage_products)
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": user_id}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]
    assert not data["user"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == AccountErrorCode.OUT_OF_SCOPE_USER.name

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]

    assert data["errors"] == []
    assert not User.objects.filter(pk=staff_user.id).exists()


def test_staff_delete_left_not_manageable_permissions(
    staff_api_client,
    superuser_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
):
    query = STAFF_DELETE_MUTATION
    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage staff"),
            Group(name="manage orders"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_staff)
    group3.permissions.add(permission_manage_orders)

    staff_user, staff_user1, staff_user2 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2, staff_user1)
    group3.user_set.add(staff_user1)

    user_id = graphene.Node.to_global_id("User", staff_user1.id)
    variables = {"id": user_id}

    # for staff user
    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == AccountErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    assert set(errors[0]["permissions"]) == {
        AccountPermissions.MANAGE_USERS.name,
        OrderPermissions.MANAGE_ORDERS.name,
    }
    assert User.objects.filter(pk=staff_user1.id).exists()

    # for superuser
    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]
    errors = data["errors"]

    assert not errors
    assert not User.objects.filter(pk=staff_user1.id).exists()


def test_staff_delete_all_permissions_manageable(
    staff_api_client,
    staff_users,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
):
    query = STAFF_DELETE_MUTATION
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
    group3.permissions.add(permission_manage_users, permission_manage_orders)

    staff_user, staff_user1, staff_user2 = staff_users
    group1.user_set.add(staff_user1)
    group2.user_set.add(staff_user2)
    group3.user_set.add(staff_user1)

    user_id = graphene.Node.to_global_id("User", staff_user1.id)
    variables = {"id": user_id}

    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]
    errors = data["errors"]

    assert len(errors) == 0
    assert not User.objects.filter(pk=staff_user1.id).exists()


def test_user_delete_errors(staff_user, admin_user):
    info = Mock(context=Mock(user=staff_user))
    with pytest.raises(ValidationError) as e:
        UserDelete.clean_instance(info, staff_user)

    msg = "You cannot delete your own account."
    assert e.value.error_dict["id"][0].message == msg

    info = Mock(context=Mock(user=staff_user))
    with pytest.raises(ValidationError) as e:
        UserDelete.clean_instance(info, admin_user)

    msg = "Cannot delete this account."
    assert e.value.error_dict["id"][0].message == msg


def test_staff_delete_errors(staff_user, customer_user, admin_user):
    info = Mock(context=Mock(user=staff_user, app=None))
    with pytest.raises(ValidationError) as e:
        StaffDelete.clean_instance(info, customer_user)
    msg = "Cannot delete a non-staff users."
    assert e.value.error_dict["id"][0].message == msg

    # should not raise any errors
    info = Mock(context=Mock(user=admin_user, app=None))
    StaffDelete.clean_instance(info, staff_user)


def test_staff_update_errors(staff_user, customer_user, admin_user):
    errors = defaultdict(list)
    input = {"is_active": None}
    StaffUpdate.clean_is_active(input, customer_user, staff_user, errors)
    assert not errors["is_active"]

    input["is_active"] = False
    StaffUpdate.clean_is_active(input, staff_user, staff_user, errors)
    assert len(errors["is_active"]) == 1
    assert (
        errors["is_active"][0].code.upper()
        == AccountErrorCode.DEACTIVATE_OWN_ACCOUNT.name
    )

    errors = defaultdict(list)
    StaffUpdate.clean_is_active(input, admin_user, staff_user, errors)
    assert len(errors["is_active"]) == 2
    assert {error.code.upper() for error in errors["is_active"]} == {
        AccountErrorCode.DEACTIVATE_SUPERUSER_ACCOUNT.name,
        AccountErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name,
    }

    errors = defaultdict(list)
    # should not raise any errors
    StaffUpdate.clean_is_active(input, customer_user, staff_user, errors)
    assert not errors["is_active"]
