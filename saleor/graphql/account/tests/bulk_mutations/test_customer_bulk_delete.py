from unittest.mock import patch

import graphene

from .....account.models import User
from .....attribute.models import AssignedUserAttributeValue, AttributeValue
from ....tests.utils import get_graphql_content

CUSTOMER_BULK_DELETE_MUTATION = """
    mutation customerBulkDelete($ids: [ID!]!) {
        customerBulkDelete(ids: $ids) {
            count
        }
    }
"""


@patch("saleor.graphql.account.mutations.base.account_events.customer_deleted_event")
def test_delete_customers(
    mocked_deletion_event,
    staff_api_client,
    staff_user,
    user_list,
    permission_manage_users,
):
    user_1, user_2, *users = user_list

    query = CUSTOMER_BULK_DELETE_MUTATION

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    assert content["data"]["customerBulkDelete"]["count"] == 2

    deleted_customers = [user_1, user_2]
    saved_customers = users

    # Ensure given customers were properly deleted and others properly saved
    # and any related event was properly triggered

    # Ensure the customers were properly deleted and others were preserved
    assert not User.objects.filter(
        id__in=[user.id for user in deleted_customers]
    ).exists()
    assert User.objects.filter(
        id__in=[user.id for user in saved_customers]
    ).count() == len(saved_customers)

    mocked_deletion_event.assert_called_once_with(
        staff_user=staff_user, app=None, deleted_count=len(deleted_customers)
    )


@patch(
    "saleor.graphql.account.bulk_mutations.customer_bulk_delete.get_webhooks_for_event"
)
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_customers_trigger_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    staff_user,
    user_list,
    permission_manage_users,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["customerBulkDelete"]["count"] == 2
    assert mocked_webhook_trigger.call_count == 2


@patch("saleor.graphql.account.mutations.base.account_events.customer_deleted_event")
def test_delete_customers_by_app(
    mocked_deletion_event,
    app_api_client,
    staff_user,
    user_list,
    permission_manage_users,
):
    user_1, user_2, *users = user_list

    query = CUSTOMER_BULK_DELETE_MUTATION

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    assert content["data"]["customerBulkDelete"]["count"] == 2

    deleted_customers = [user_1, user_2]
    saved_customers = users

    # Ensure given customers were properly deleted and others properly saved
    # and any related event was properly triggered

    # Ensure the customers were properly deleted and others were preserved
    assert not User.objects.filter(
        id__in=[user.id for user in deleted_customers]
    ).exists()
    assert User.objects.filter(
        id__in=[user.id for user in saved_customers]
    ).count() == len(saved_customers)

    mocked_deletion_event.assert_called_once_with(
        staff_user=None,
        app=app_api_client.app,
        deleted_count=len(deleted_customers),
    )


def test_deletes_unique_attribute_values_and_keeps_shared_choices(
    staff_api_client,
    customer_user,
    customer_user2,
    permission_manage_users,
    description_customer_attribute,
    loyalty_customer_attribute,
):
    # given: each customer has a unique (plain text) value and a shared choice
    customers = [customer_user, customer_user2]
    unique_values = []
    choice_value = loyalty_customer_attribute.values.get(slug="gold")
    for customer in customers:
        plain_text = f"Notes about customer {customer.pk}"
        unique_value = AttributeValue.objects.create(
            attribute=description_customer_attribute,
            name=plain_text,
            slug=f"{customer.pk}_{description_customer_attribute.pk}",
            plain_text=plain_text,
        )
        unique_values.append(unique_value)
        AssignedUserAttributeValue.objects.create(user=customer, value=unique_value)
        AssignedUserAttributeValue.objects.create(user=customer, value=choice_value)
    variables = {
        "ids": [
            graphene.Node.to_global_id("User", customer.pk) for customer in customers
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then: the unique values are deleted with the users, the shared choice stays
    content = get_graphql_content(response)
    assert content["data"]["customerBulkDelete"]["count"] == len(customers)
    assert (
        User.objects.filter(pk__in=[customer.pk for customer in customers]).exists()
        is False
    )
    assert (
        AttributeValue.objects.filter(
            pk__in=[value.pk for value in unique_values]
        ).exists()
        is False
    )
    assert AttributeValue.objects.filter(pk=choice_value.pk).exists() is True
