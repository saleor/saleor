from functools import partial
from unittest.mock import ANY, Mock, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ......account.models import User
from ......attribute.models import AssignedUserAttributeValue, AttributeValue
from ......page.models import Page
from ......webhook.event_types import WebhookEventAsyncType
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
        None,
        WebhookEventAsyncType.CUSTOMER_DELETED,
        [any_webhook],
        customer_user,
        SimpleLazyObject(lambda: staff_api_client.user),
        legacy_data_generator=ANY,
        allow_replica=False,
    )

    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
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


def test_deletes_unique_attribute_values_and_keeps_shared_choices(
    staff_api_client,
    customer_user,
    permission_manage_users,
    description_customer_attribute,
    loyalty_customer_attribute,
):
    # given: the customer has a unique (plain text) value and a shared choice
    plain_text = "Notes about the customer"
    unique_value = AttributeValue.objects.create(
        attribute=description_customer_attribute,
        name=plain_text,
        slug=f"{customer_user.pk}_{description_customer_attribute.pk}",
        plain_text=plain_text,
    )
    choice_value = loyalty_customer_attribute.values.get(slug="gold")
    AssignedUserAttributeValue.objects.create(user=customer_user, value=unique_value)
    AssignedUserAttributeValue.objects.create(user=customer_user, value=choice_value)
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_DELETE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then: the unique value is deleted with the user, the shared choice stays
    content = get_graphql_content(response)
    assert content["data"]["customerDelete"]["errors"] == []
    assert User.objects.filter(pk=customer_user.pk).exists() is False
    assert AttributeValue.objects.filter(pk=unique_value.pk).exists() is False
    assert AttributeValue.objects.filter(pk=choice_value.pk).exists() is True


def test_deletes_single_reference_attribute_values(
    staff_api_client,
    customer_user,
    permission_manage_users,
    customer_type_page_single_reference_attribute,
    page,
):
    # given: the customer holds a per-user single-reference value
    reference_value = AttributeValue.objects.create(
        attribute=customer_type_page_single_reference_attribute,
        name=page.title,
        slug=f"{customer_user.pk}_{page.pk}",
        reference_page=page,
    )
    AssignedUserAttributeValue.objects.create(user=customer_user, value=reference_value)
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_DELETE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then: the per-user value is deleted with the user, the referenced page stays
    content = get_graphql_content(response)
    assert content["data"]["customerDelete"]["errors"] == []
    assert User.objects.filter(pk=customer_user.pk).exists() is False
    assert AttributeValue.objects.filter(pk=reference_value.pk).exists() is False
    assert Page.objects.filter(pk=page.pk).exists() is True


def test_deleting_user_keeps_other_users_single_reference_values(
    staff_api_client,
    customer_user,
    customer_user2,
    permission_manage_users,
    customer_type_page_single_reference_attribute,
    default_customer_type,
    page,
):
    # given: both users reference the same page through the same attribute,
    # assigned via the real mutation path so the per-user value creation
    # (not a hand-built slug) is what is under test
    default_customer_type.customer_attributes.add(
        customer_type_page_single_reference_attribute
    )
    attribute_id = graphene.Node.to_global_id(
        "Attribute", customer_type_page_single_reference_attribute.pk
    )
    page_id = graphene.Node.to_global_id("Page", page.pk)
    staff_api_client.user.user_permissions.add(permission_manage_users)
    update_mutation = """
        mutation CustomerUpdate($id: ID!, $input: CustomerInput!) {
            customerUpdate(id: $id, input: $input) {
                errors {
                    field
                    message
                }
            }
        }
    """
    for user in [customer_user, customer_user2]:
        variables = {
            "id": graphene.Node.to_global_id("User", user.pk),
            "input": {"attributes": [{"id": attribute_id, "reference": page_id}]},
        }
        response = staff_api_client.post_graphql(update_mutation, variables)
        content = get_graphql_content(response)
        assert content["data"]["customerUpdate"]["errors"] == []
    # the same reference produced one value row per user - rows are not shared
    values = AttributeValue.objects.filter(
        attribute=customer_type_page_single_reference_attribute
    )
    assert values.count() == 2

    # when: one of the users is deleted
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}
    response = staff_api_client.post_graphql(CUSTOMER_DELETE_MUTATION, variables)

    # then: only the deleted user's value is gone
    content = get_graphql_content(response)
    assert content["data"]["customerDelete"]["errors"] == []
    assert User.objects.filter(pk=customer_user.pk).exists() is False
    remaining_value = AttributeValue.objects.get(
        attribute=customer_type_page_single_reference_attribute
    )
    assert remaining_value.uservalueassignment.get().user == customer_user2
    assert remaining_value.reference_page == page
