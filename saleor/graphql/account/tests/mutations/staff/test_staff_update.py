import json
from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.core.files import File
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.models import Group, User
from ......core.utils.json_serializer import CustomJsonEncoder
from ......giftcard.models import GiftCard
from ......giftcard.search import update_gift_cards_search_vector
from ......permission.enums import AccountPermissions
from ......webhook.event_types import WebhookEventAsyncType
from ......webhook.payloads import generate_meta, generate_requestor
from .....tests.utils import assert_no_permission, get_graphql_content

STAFF_UPDATE_MUTATIONS = """
    mutation UpdateStaff(
            $id: ID!, $input: StaffUpdateInput!) {
        staffUpdate(
                id: $id,
                input: $input) {
            errors {
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
                permissionGroups {
                    name
                }
                isActive
                email
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


def test_staff_update(staff_api_client, permission_manage_staff, media_root):
    query = STAFF_UPDATE_MUTATIONS
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    assert not staff_user.search_document
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id, "input": {"isActive": False}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []
    assert data["user"]["userPermissions"] == []
    assert not data["user"]["isActive"]
    staff_user.refresh_from_db()
    assert not staff_user.search_document


def test_staff_update_metadata(staff_api_client, permission_manage_staff):
    # given
    query = STAFF_UPDATE_MUTATIONS
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    assert not staff_user.search_document
    id = graphene.Node.to_global_id("User", staff_user.id)
    metadata = [{"key": "test key", "value": "test value"}]
    variables = {"id": id, "input": {"metadata": metadata}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []
    assert data["user"]["userPermissions"] == []
    assert data["user"]["metadata"] == metadata
    staff_user.refresh_from_db()
    assert not staff_user.search_document


def test_staff_update_private_metadata(staff_api_client, permission_manage_staff):
    # given
    query = STAFF_UPDATE_MUTATIONS
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    assert not staff_user.search_document
    id = graphene.Node.to_global_id("User", staff_user.id)
    metadata = [{"key": "test key", "value": "test value"}]
    variables = {"id": id, "input": {"privateMetadata": metadata}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []
    assert data["user"]["userPermissions"] == []
    assert data["user"]["privateMetadata"] == metadata
    staff_user.refresh_from_db()
    assert not staff_user.search_document


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_staff_update_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_staff,
    media_root,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    assert not staff_user.search_document
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id, "input": {"isActive": False}}

    # when
    response = staff_api_client.post_graphql(
        STAFF_UPDATE_MUTATIONS, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]

    # then
    assert not data["errors"]
    assert data["user"]
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
        WebhookEventAsyncType.STAFF_UPDATED,
        [any_webhook],
        staff_user,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


def test_staff_update_email(staff_api_client, permission_manage_staff, media_root):
    query = STAFF_UPDATE_MUTATIONS
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    assert not staff_user.search_document
    id = graphene.Node.to_global_id("User", staff_user.id)
    new_email = "test@email.com"
    variables = {"id": id, "input": {"email": new_email}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []
    assert data["user"]["userPermissions"] == []
    assert data["user"]["isActive"]
    staff_user.refresh_from_db()
    assert staff_user.search_document == f"{new_email}\n"


@pytest.mark.parametrize("field", ["firstName", "lastName"])
def test_staff_update_name_field(
    field, staff_api_client, permission_manage_staff, media_root
):
    query = STAFF_UPDATE_MUTATIONS
    email = "staffuser@example.com"
    staff_user = User.objects.create(email=email, is_staff=True)
    assert not staff_user.search_document
    id = graphene.Node.to_global_id("User", staff_user.id)
    value = "Name"
    variables = {"id": id, "input": {field: value}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []
    assert data["user"]["userPermissions"] == []
    assert data["user"]["isActive"]
    staff_user.refresh_from_db()
    assert staff_user.search_document == f"{email}\n{value.lower()}\n"


def test_staff_update_app_no_permission(
    app_api_client, permission_manage_staff, media_root
):
    query = STAFF_UPDATE_MUTATIONS
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id, "input": {"isActive": False}}

    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    assert_no_permission(response)


def test_staff_update_groups_and_permissions(
    staff_api_client,
    media_root,
    permission_manage_staff,
    permission_manage_users,
    permission_manage_orders,
    permission_manage_products,
):
    query = STAFF_UPDATE_MUTATIONS
    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage orders"), Group(name="empty")]
    )
    group1, group2, group3 = groups
    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_orders)

    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    staff_user.groups.add(group1)

    id = graphene.Node.to_global_id("User", staff_user.id)
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
    assert data["errors"] == []
    assert {perm["code"].lower() for perm in data["user"]["userPermissions"]} == {
        permission_manage_orders.codename,
    }
    assert {group["name"] for group in data["user"]["permissionGroups"]} == {
        group2.name,
        group3.name,
    }


def test_staff_update_out_of_scope_user(
    staff_api_client,
    superuser_api_client,
    permission_manage_staff,
    permission_manage_orders,
    media_root,
):
    query = STAFF_UPDATE_MUTATIONS
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    staff_user.user_permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id, "input": {"isActive": False}}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert not data["user"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == AccountErrorCode.OUT_OF_SCOPE_USER.name

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["user"]["email"] == staff_user.email
    assert data["user"]["isActive"] is False
    assert not data["errors"]


def test_staff_update_out_of_scope_groups(
    staff_api_client,
    superuser_api_client,
    permission_manage_staff,
    media_root,
    permission_manage_users,
    permission_manage_orders,
    permission_manage_products,
):
    query = STAFF_UPDATE_MUTATIONS

    groups = Group.objects.bulk_create(
        [
            Group(name="manage users"),
            Group(name="manage orders"),
            Group(name="manage products"),
        ]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_orders)
    group3.permissions.add(permission_manage_products)

    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {
        "id": id,
        "input": {
            "isActive": False,
            "addGroups": [
                graphene.Node.to_global_id("Group", gr.pk) for gr in [group1, group2]
            ],
            "removeGroups": [graphene.Node.to_global_id("Group", group3.pk)],
        },
    }

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    errors = data["errors"]
    assert not data["user"]
    assert len(errors) == 2

    expected_errors = [
        {
            "field": "addGroups",
            "code": AccountErrorCode.OUT_OF_SCOPE_GROUP.name,
            "permissions": None,
            "groups": [graphene.Node.to_global_id("Group", group1.pk)],
        },
        {
            "field": "removeGroups",
            "code": AccountErrorCode.OUT_OF_SCOPE_GROUP.name,
            "permissions": None,
            "groups": [graphene.Node.to_global_id("Group", group3.pk)],
        },
    ]
    for error in errors:
        error.pop("message")
        assert error in expected_errors

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["user"]["email"] == staff_user.email
    assert {group["name"] for group in data["user"]["permissionGroups"]} == {
        group1.name,
        group2.name,
    }


def test_staff_update_duplicated_input_items(
    staff_api_client,
    permission_manage_staff,
    media_root,
    permission_manage_orders,
    permission_manage_users,
):
    query = STAFF_UPDATE_MUTATIONS

    groups = Group.objects.bulk_create(
        [Group(name="manage users"), Group(name="manage orders"), Group(name="empty")]
    )
    group1, group2, group3 = groups

    group1.permissions.add(permission_manage_users)
    group2.permissions.add(permission_manage_orders)

    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    staff_api_client.user.user_permissions.add(
        permission_manage_orders, permission_manage_users
    )
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {
        "id": id,
        "input": {
            "addGroups": [
                graphene.Node.to_global_id("Group", gr.pk) for gr in [group1, group2]
            ],
            "removeGroups": [
                graphene.Node.to_global_id("Group", gr.pk)
                for gr in [group1, group2, group3]
            ],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] is None
    assert errors[0]["code"] == AccountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert set(errors[0]["groups"]) == {
        graphene.Node.to_global_id("Group", gr.pk) for gr in [group1, group2]
    }
    assert errors[0]["permissions"] is None


def test_staff_update_doesnt_change_existing_avatar(
    staff_api_client,
    permission_manage_staff,
    media_root,
    staff_users,
):
    query = STAFF_UPDATE_MUTATIONS

    mock_file = MagicMock(spec=File)
    mock_file.name = "image.jpg"

    staff_user, staff_user1, _ = staff_users

    id = graphene.Node.to_global_id("User", staff_user1.id)
    variables = {"id": id, "input": {"isActive": False}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []

    staff_user.refresh_from_db()
    assert not staff_user.avatar


def test_staff_update_deactivate_with_manage_staff_left_not_manageable_perms(
    staff_api_client,
    superuser_api_client,
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    media_root,
):
    query = STAFF_UPDATE_MUTATIONS
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
    group3.user_set.add(staff_user2)

    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)

    id = graphene.Node.to_global_id("User", staff_user1.id)
    variables = {"id": id, "input": {"isActive": False}}

    # for staff user
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    errors = data["errors"]

    assert not data["user"]
    assert len(errors) == 1
    assert errors[0]["field"] == "isActive"
    assert errors[0]["code"] == AccountErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.name
    assert len(errors[0]["permissions"]) == 1
    assert errors[0]["permissions"][0] == AccountPermissions.MANAGE_USERS.name

    # for superuser
    response = superuser_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    errors = data["errors"]

    staff_user1.refresh_from_db()
    assert data["user"]["email"] == staff_user1.email
    assert data["user"]["isActive"] is False
    assert not errors
    assert not staff_user1.is_active


def test_staff_update_deactivate_with_manage_staff_all_perms_manageable(
    staff_api_client,
    staff_users,
    permission_manage_users,
    permission_manage_staff,
    permission_manage_orders,
    media_root,
):
    query = STAFF_UPDATE_MUTATIONS
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
    group1.user_set.add(staff_user1, staff_user2)
    group2.user_set.add(staff_user2, staff_user1)
    group3.user_set.add(staff_user2)

    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)

    id = graphene.Node.to_global_id("User", staff_user1.id)
    variables = {"id": id, "input": {"isActive": False}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    errors = data["errors"]

    staff_user1.refresh_from_db()
    assert not errors
    assert staff_user1.is_active is False


def test_staff_update_update_email_assign_gift_cards_and_orders(
    staff_api_client, permission_manage_staff, gift_card, order
):
    # given
    query = STAFF_UPDATE_MUTATIONS
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)

    new_email = "testuser@example.com"

    gift_card.created_by = None
    gift_card.created_by_email = new_email
    gift_card.save(update_fields=["created_by", "created_by_email"])

    order.user = None
    order.user_email = new_email
    order.save(update_fields=["user_email", "user"])

    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id, "input": {"email": new_email}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []
    assert data["user"]["userPermissions"] == []
    assert data["user"]["email"] == new_email
    gift_card.refresh_from_db()
    staff_user.refresh_from_db()
    assert gift_card.created_by == staff_user
    assert gift_card.created_by_email == staff_user.email
    order.refresh_from_db()
    assert order.user == staff_user


def test_staff_update_trigger_gift_card_search_vector_update(
    staff_api_client, permission_manage_staff, gift_card_list
):
    # given
    query = STAFF_UPDATE_MUTATIONS
    new_email = "testuser@example.com"
    user = staff_api_client.user

    id = graphene.Node.to_global_id("User", user.id)
    variables = {"id": id, "input": {"email": new_email}}

    gift_card_1, gift_card_2, gift_card_3 = gift_card_list
    gift_card_1.created_by = user
    gift_card_2.used_by = user
    gift_card_3.created_by_email = new_email
    GiftCard.objects.bulk_update(
        gift_card_list, ["created_by", "used_by", "created_by_email"]
    )

    update_gift_cards_search_vector(gift_card_list)
    for card in gift_card_list:
        card.refresh_from_db()
        assert card.search_index_dirty is False

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["staffUpdate"]["errors"]
    user.refresh_from_db()
    assert user.email == new_email
    for card in gift_card_list:
        card.refresh_from_db()
        assert card.search_index_dirty is True
