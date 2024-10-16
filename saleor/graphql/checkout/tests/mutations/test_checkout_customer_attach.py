from unittest.mock import patch

import graphene
from django.test import override_settings

from .....account.models import User
from .....checkout.actions import call_checkout_event
from .....checkout.error_codes import CheckoutErrorCode
from .....checkout.models import Checkout
from .....core.models import EventDelivery
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.transport.asynchronous.transport import send_webhook_request_async
from .....webhook.transport.utils import WebhookResponse, prepare_deferred_payload_data
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
    "saleor.graphql.checkout.mutations.checkout_customer_attach.call_checkout_event",
    wraps=call_checkout_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async",
    wraps=send_webhook_request_async.apply_async,
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_customer_triggers_webhooks(
    mocked_send_webhook_using_scheme_method,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event,
    setup_checkout_webhooks,
    settings,
    user_api_client,
    checkout_with_item,
    customer_user2,
    permission_impersonate_user,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    mocked_send_webhook_using_scheme_method.return_value = WebhookResponse(content="")
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

    checkout = Checkout.objects.get(
        token=content["data"]["checkoutCustomerAttach"]["checkout"]["token"]
    )
    deferred_payload_data = prepare_deferred_payload_data(
        subscribable_object=checkout, requestor=user_api_client.user, request_time=None
    )

    assert wrapped_call_checkout_event.called
    assert mocked_send_webhook_request_async.call_count == 1
    assert (
        mocked_send_webhook_request_async.call_args.kwargs["kwargs"][
            "deferred_payload_data"
        ]
        == deferred_payload_data
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_updated_webhook.id
    ).exists()

    sync_deliveries = {
        call.args[0].event_type: call.args[0]
        for call in mocked_send_webhook_request_sync.mock_calls
    }

    assert WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT in sync_deliveries
    shipping_methods_delivery = sync_deliveries[
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    ]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id

    assert WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS in sync_deliveries
    filter_shipping_delivery = sync_deliveries[
        WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    ]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id

    assert WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES in sync_deliveries
    tax_delivery = sync_deliveries[WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES]
    assert tax_delivery.webhook_id == tax_webhook.id
