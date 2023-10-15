import json
from unittest.mock import call, patch
from urllib.parse import urlencode

import graphene
from django.contrib.auth.tokens import default_token_generator
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.models import Group, User
from ......account.notifications import get_default_user_payload
from ......core.notify_events import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.utils.json_serializer import CustomJsonEncoder
from ......core.utils.url import prepare_url
from ......webhook.event_types import WebhookEventAsyncType
from ......webhook.payloads import generate_meta, generate_requestor
from .....tests.utils import assert_no_permission, get_graphql_content

STAFF_CREATE_MUTATION = """
    mutation CreateStaff(
        $input: StaffCreateInput!
    ) {
        staffCreate(
            input: $input
        ){
            errors {
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
                permissionGroups {
                    name
                    permissions {
                        code
                    }
                }
                avatar {
                    url
                }
                metadata {
                    key
                    value
                }
                privateMetadata {
                    key
                    value
                }
            }
        }
    }
"""


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_staff_create(
    mocked_notify,
    staff_api_client,
    staff_user,
    media_root,
    permission_group_manage_users,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_users,
    channel_PLN,
    site_settings,
):
    group = permission_group_manage_users
    group.permissions.add(permission_manage_products)
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    email = "api_user@example.com"
    redirect_url = "https://www.example.com"
    metadata = [{"key": "test key", "value": "test value"}]
    private_metadata = [{"key": "private test key", "value": "private test value"}]
    variables = {
        "input": {
            "email": email,
            "redirectUrl": redirect_url,
            "addGroups": [graphene.Node.to_global_id("Group", group.pk)],
            "metadata": metadata,
            "privateMetadata": private_metadata,
        }
    }

    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert data["errors"] == []
    assert data["user"]["email"] == email
    assert data["user"]["isStaff"]
    assert data["user"]["isActive"]
    assert data["user"]["metadata"] == metadata
    assert data["user"]["privateMetadata"] == private_metadata

    expected_perms = {
        permission_manage_products.codename,
        permission_manage_users.codename,
    }
    permissions = data["user"]["userPermissions"]
    assert {perm["code"].lower() for perm in permissions} == expected_perms

    staff_user = User.objects.get(email=email)

    assert staff_user.is_staff
    assert staff_user.search_document == f"{email}\n".lower()

    groups = data["user"]["permissionGroups"]
    assert len(groups) == 1
    assert {perm["code"].lower() for perm in groups[0]["permissions"]} == expected_perms

    token = default_token_generator.make_token(staff_user)
    params = urlencode({"email": email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(staff_user),
        "password_set_url": password_set_url,
        "token": token,
        "recipient_email": staff_user.email,
        "channel_slug": None,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_SET_STAFF_PASSWORD,
        payload=expected_payload,
        channel_slug=None,
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_promote_customer_to_staff_user(
    mocked_notify,
    staff_api_client,
    staff_user,
    customer_user,
    media_root,
    permission_group_manage_users,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_users,
    channel_PLN,
):
    group = permission_group_manage_users
    group.permissions.add(permission_manage_products)
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    redirect_url = "https://www.example.com"
    email = customer_user.email
    variables = {
        "input": {
            "email": email,
            "redirectUrl": redirect_url,
            "addGroups": [graphene.Node.to_global_id("Group", group.pk)],
        }
    }

    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert data["errors"] == []
    assert data["user"]["email"] == email
    assert data["user"]["isStaff"]
    assert data["user"]["isActive"]

    expected_perms = {
        permission_manage_products.codename,
        permission_manage_users.codename,
    }
    permissions = data["user"]["userPermissions"]
    assert {perm["code"].lower() for perm in permissions} == expected_perms

    staff_user = User.objects.get(email=email)

    assert staff_user.is_staff

    groups = data["user"]["permissionGroups"]
    assert len(groups) == 1
    assert {perm["code"].lower() for perm in groups[0]["permissions"]} == expected_perms

    mocked_notify.assert_not_called()


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_staff_create_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    staff_user,
    permission_group_manage_users,
    permission_manage_staff,
    permission_manage_users,
    channel_PLN,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user.user_permissions.add(permission_manage_users)
    email = "api_user@example.com"
    redirect_url = "https://www.example.com"
    variables = {
        "input": {
            "email": email,
            "redirectUrl": redirect_url,
            "addGroups": [
                graphene.Node.to_global_id("Group", permission_group_manage_users.pk)
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    new_staff_user = User.objects.get(email=email)

    # then
    assert not data["errors"]
    assert data["user"]
    expected_call = call(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("User", new_staff_user.id),
                "email": email,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.STAFF_CREATED,
        [any_webhook],
        new_staff_user,
        SimpleLazyObject(lambda: staff_api_client.user),
    )

    assert expected_call in mocked_webhook_trigger.call_args_list


def test_staff_create_app_no_permission(
    app_api_client,
    staff_user,
    media_root,
    permission_group_manage_users,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_users,
):
    group = permission_group_manage_users
    group.permissions.add(permission_manage_products)
    staff_user.user_permissions.add(permission_manage_products, permission_manage_users)
    email = "api_user@example.com"
    variables = {
        "input": {
            "email": email,
            "redirectUrl": "https://www.example.com",
            "addGroups": [graphene.Node.to_global_id("Group", group.pk)],
        }
    }

    response = app_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )

    assert_no_permission(response)


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_staff_create_out_of_scope_group(
    mocked_notify,
    staff_api_client,
    superuser_api_client,
    media_root,
    permission_manage_staff,
    permission_manage_users,
    permission_group_manage_users,
    channel_PLN,
    site_settings,
):
    """Ensure user can't create staff with groups which are out of user scope.
    Ensure superuser pass restrictions.
    """
    group = permission_group_manage_users
    group2 = Group.objects.create(name="second group")
    group2.permissions.add(permission_manage_staff)
    email = "api_user@example.com"
    redirect_url = "https://www.example.com"
    variables = {
        "input": {
            "email": email,
            "redirectUrl": redirect_url,
            "addGroups": [
                graphene.Node.to_global_id("Group", gr.pk) for gr in [group, group2]
            ],
        }
    }

    # for staff user
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    errors = data["errors"]
    assert not data["user"]
    assert len(errors) == 1

    expected_error = {
        "field": "addGroups",
        "code": AccountErrorCode.OUT_OF_SCOPE_GROUP.name,
        "permissions": None,
        "groups": [graphene.Node.to_global_id("Group", group.pk)],
    }

    assert errors[0] == expected_error

    mocked_notify.assert_not_called()

    # for superuser
    response = superuser_api_client.post_graphql(STAFF_CREATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]

    assert data["errors"] == []
    assert data["user"]["email"] == email
    assert data["user"]["isStaff"]
    assert data["user"]["isActive"]
    expected_perms = {
        permission_manage_staff.codename,
        permission_manage_users.codename,
    }
    permissions = data["user"]["userPermissions"]
    assert {perm["code"].lower() for perm in permissions} == expected_perms

    staff_user = User.objects.get(email=email)

    assert staff_user.is_staff

    expected_groups = [
        {
            "name": group.name,
            "permissions": [{"code": permission_manage_users.codename.upper()}],
        },
        {
            "name": group2.name,
            "permissions": [{"code": permission_manage_staff.codename.upper()}],
        },
    ]
    groups = data["user"]["permissionGroups"]
    assert len(groups) == 2
    for group in expected_groups:
        assert group in groups
    token = default_token_generator.make_token(staff_user)
    params = urlencode({"email": email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(staff_user),
        "password_set_url": password_set_url,
        "token": token,
        "recipient_email": staff_user.email,
        "channel_slug": None,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_SET_STAFF_PASSWORD,
        payload=expected_payload,
        channel_slug=None,
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_staff_create_send_password_with_url(
    mocked_notify, staff_api_client, media_root, permission_manage_staff, site_settings
):
    email = "api_user@example.com"
    redirect_url = "https://www.example.com"
    variables = {"input": {"email": email, "redirectUrl": redirect_url}}

    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert not data["errors"]

    staff_user = User.objects.get(email=email)
    assert staff_user.is_staff

    token = default_token_generator.make_token(staff_user)
    params = urlencode({"email": email, "token": token})
    password_set_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(staff_user),
        "password_set_url": password_set_url,
        "token": token,
        "recipient_email": staff_user.email,
        "channel_slug": None,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_SET_STAFF_PASSWORD,
        payload=expected_payload,
        channel_slug=None,
    )


def test_staff_create_without_send_password(
    staff_api_client, media_root, permission_manage_staff
):
    email = "api_user@example.com"
    variables = {"input": {"email": email}}
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert not data["errors"]
    User.objects.get(email=email)


def test_staff_create_with_invalid_url(
    staff_api_client, media_root, permission_manage_staff
):
    email = "api_user@example.com"
    variables = {"input": {"email": email, "redirectUrl": "invalid"}}
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert data["errors"][0] == {
        "field": "redirectUrl",
        "code": AccountErrorCode.INVALID.name,
        "permissions": None,
        "groups": None,
    }
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_staff_create_with_not_allowed_url(
    staff_api_client, media_root, permission_manage_staff
):
    email = "api_userrr@example.com"
    variables = {"input": {"email": email, "redirectUrl": "https://www.fake.com"}}
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert data["errors"][0] == {
        "field": "redirectUrl",
        "code": AccountErrorCode.INVALID.name,
        "permissions": None,
        "groups": None,
    }
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_staff_create_with_upper_case_email(
    staff_api_client, media_root, permission_manage_staff
):
    # given
    email = "api_user@example.com"
    variables = {"input": {"email": email}}

    # when
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["staffCreate"]
    assert not data["errors"]
    assert data["user"]["email"] == email.lower()
