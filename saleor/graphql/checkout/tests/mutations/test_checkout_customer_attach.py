from unittest.mock import call, patch

import graphene
from django.test import override_settings

from .....account.models import User
from .....checkout.actions import call_checkout_event_for_checkout
from .....checkout.error_codes import CheckoutErrorCode
from .....core.models import EventDelivery
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_CHECKOUT_CUSTOMER_ATTACH = """
    mutation checkoutCustomerAttach($id: ID, $customerId: ID) {
        checkoutCustomerAttach(id: $id, customerId: $customerId) {
            checkout {
                token
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_checkout_customer_attach(
    user_api_client, checkout_with_item, customer_user2, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user2.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )
    content = get_graphql_content(response)

    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user2
    assert checkout.email == customer_user2.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_with_customer_id_same_as_in_request(
    user_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    response = user_api_client.post_graphql(
        query,
        variables,
    )
    content = get_graphql_content(response, ignore_errors=True)

    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_no_customer_id(
    api_client, user_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should fail for unauthenticated customers
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # Mutation should succeed for authenticated customer
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_by_app(
    app_api_client, checkout_with_item, customer_user, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.user == customer_user
    assert checkout.email == customer_user.email
    assert checkout.last_change != previous_last_change


def test_checkout_customer_attach_by_app_no_customer_id(
    app_api_client, checkout_with_item, permission_impersonate_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    variables = {"id": to_global_id_or_none(checkout)}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_impersonate_user],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutCustomerAttach"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.REQUIRED.name
    assert data["errors"][0]["field"] == "customerId"


def test_checkout_customer_attach_by_app_without_permission(
    app_api_client, checkout_with_item, customer_user
):
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()
    assert checkout.user is None

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # Mutation should succeed for authenticated customer
    response = app_api_client.post_graphql(
        query,
        variables,
    )

    assert_no_permission(response)


def test_checkout_customer_attach_user_to_checkout_with_user(
    user_api_client, customer_user, user_checkout, address
):
    checkout = user_checkout

    query = """
    mutation checkoutCustomerAttach($id: ID) {
        checkoutCustomerAttach(id: $id) {
            checkout {
                token
            }
            errors {
                field
                message
                code
            }
        }
    }
"""

    default_address = address.get_copy()
    second_user = User.objects.create_user(
        "test2@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Test2",
        last_name="Tested",
    )

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    customer_id = graphene.Node.to_global_id("User", second_user.pk)
    variables = {"id": checkout_id, "customerId": customer_id}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_with_active_problems_flow(user_api_client, checkout_with_problems):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variables = {"id": to_global_id_or_none(checkout_with_problems), "customerId": None}

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_CUSTOMER_ATTACH,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutCustomerAttach"]["errors"]


@patch(
    "saleor.graphql.checkout.mutations.checkout_customer_attach.call_checkout_event_for_checkout",
    wraps=call_checkout_event_for_checkout,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_customer_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event_for_checkout,
    setup_checkout_webhooks,
    settings,
    user_api_client,
    checkout_with_item,
    customer_user2,
    permission_impersonate_user,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user2.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # when
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutCustomerAttach"]["errors"]

    # confirm that event delivery was generated for each webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )
    tax_delivery = EventDelivery.objects.get(webhook_id=tax_webhook.id)
    shipping_methods_delivery = EventDelivery.objects.get(
        webhook_id=shipping_webhook.id,
        event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )
    filter_shipping_delivery = EventDelivery.objects.get(
        webhook_id=shipping_filter_webhook.id,
        event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
    )

    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": checkout_update_delivery.id},
        queue=settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
    mocked_send_webhook_request_sync.assert_has_calls(
        [
            call(shipping_methods_delivery, timeout=settings.WEBHOOK_SYNC_TIMEOUT),
            call(filter_shipping_delivery, timeout=settings.WEBHOOK_SYNC_TIMEOUT),
            call(tax_delivery),
        ]
    )
    assert wrapped_call_checkout_event_for_checkout.called
