from unittest.mock import Mock, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ......webhook.event_types import WebhookEventAsyncType
from ......webhook.payloads import generate_customer_payload
from .....tests.utils import get_graphql_content
from ....mutations.staff import CustomerDelete

CUSTOMER_DELETE_MUTATION = """
    mutation CustomerDelete($id: ID, $externalReference: String) {
        customerDelete(id: $id, externalReference: $externalReference) {
            errors {
                field
                message
            }
            user {
                id
                externalReference
            }
        }
    }
"""


@patch("saleor.account.signals.delete_from_storage_task.delay")
@patch("saleor.graphql.account.mutations.base.account_events.customer_deleted_event")
def test_customer_delete(
    mocked_deletion_event,
    delete_from_storage_task_mock,
    staff_api_client,
    staff_user,
    customer_user,
    image,
    permission_manage_users,
    media_root,
):
    """Ensure deleting a customer actually deletes the customer and creates proper
    related events"""

    query = CUSTOMER_DELETE_MUTATION
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    customer_user.avatar = image
    customer_user.save(update_fields=["avatar"])
    variables = {"id": customer_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerDelete"]
    assert data["errors"] == []
    assert data["user"]["id"] == customer_id

    # Ensure the customer was properly deleted
    # and any related event was properly triggered
    mocked_deletion_event.assert_called_once_with(
        staff_user=staff_user, app=None, deleted_count=1
    )
    delete_from_storage_task_mock.assert_called_once_with(customer_user.avatar.name)


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_customer_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    customer_user,
    permission_manage_users,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": customer_id}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_DELETE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerDelete"]

    # then
    assert data["errors"] == []
    assert data["user"]["id"] == customer_id
    mocked_webhook_trigger.assert_called_once_with(
        generate_customer_payload(customer_user, staff_api_client.user),
        WebhookEventAsyncType.CUSTOMER_DELETED,
        [any_webhook],
        customer_user,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


@patch("saleor.account.signals.delete_from_storage_task.delay")
@patch("saleor.graphql.account.mutations.base.account_events.customer_deleted_event")
def test_customer_delete_by_app(
    mocked_deletion_event,
    delete_from_storage_task_mock,
    app_api_client,
    app,
    customer_user,
    image,
    permission_manage_users,
    media_root,
):
    """Ensure deleting a customer actually deletes the customer and creates proper
    related events"""

    query = CUSTOMER_DELETE_MUTATION
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    customer_user.avatar = image
    customer_user.save(update_fields=["avatar"])
    variables = {"id": customer_id}
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerDelete"]
    assert data["errors"] == []
    assert data["user"]["id"] == customer_id

    # Ensure the customer was properly deleted
    # and any related event was properly triggered
    assert mocked_deletion_event.call_count == 1
    args, kwargs = mocked_deletion_event.call_args
    assert kwargs["deleted_count"] == 1
    assert kwargs["staff_user"] is None
    assert kwargs["app"] == app
    delete_from_storage_task_mock.assert_called_once_with(customer_user.avatar.name)


def test_customer_delete_errors(customer_user, admin_user, staff_user):
    info = Mock(context=Mock(user=admin_user))
    with pytest.raises(ValidationError) as e:
        CustomerDelete.clean_instance(info, staff_user)

    msg = "Cannot delete a staff account."
    assert e.value.error_dict["id"][0].message == msg

    # should not raise any errors
    CustomerDelete.clean_instance(info, customer_user)


def test_customer_delete_by_external_reference(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    user = customer_user
    query = CUSTOMER_DELETE_MUTATION
    ext_ref = "test-ext-ref"
    user.external_reference = ext_ref
    user.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["customerDelete"]
    with pytest.raises(user._meta.model.DoesNotExist):
        user.refresh_from_db()
    assert not data["errors"]
    assert data["user"]["externalReference"] == ext_ref
    assert data["user"]["id"] == graphene.Node.to_global_id("User", user.id)


def test_delete_customer_by_both_id_and_external_reference(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    query = CUSTOMER_DELETE_MUTATION
    variables = {"externalReference": "whatever", "id": "whatever"}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["customerDelete"]["errors"]
    assert (
        errors[0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_delete_customer_by_external_reference_not_existing(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    query = CUSTOMER_DELETE_MUTATION
    ext_ref = "non-existing-ext-ref"
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["customerDelete"]["errors"]
    assert errors[0]["message"] == f"Couldn't resolve to a node: {ext_ref}"
