from unittest.mock import ANY, patch

import graphene
import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from .....account.models import User
from .....checkout.actions import call_checkout_event
from .....checkout.error_codes import CheckoutErrorCode
from .....core.models import EventDelivery
from .....product.models import ProductChannelListing, ProductVariantChannelListing
from .....webhook.event_types import WebhookEventAsyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION_CHECKOUT_CUSTOMER_ATTACH = """
    mutation checkoutCustomerAttach($id: ID, $customerId: ID) {
        checkoutCustomerAttach(id: $id, customerId: $customerId) {
            checkout {
                token
                email
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
    assert data["checkout"]["email"] == customer_user2.email
    checkout.refresh_from_db()
    assert checkout.user == customer_user2
    assert checkout.email == customer_user2.email
    assert checkout.last_change != previous_last_change


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_checkout_customer_attach_when_line_without_channel_listing(
    channel_listing_model,
    listing_filter_field,
    user_api_client,
    checkout_with_item,
    customer_user2,
    permission_impersonate_user,
):
    # given
    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.save()

    line = checkout.lines.first()

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id, **{listing_filter_field: line.variant_id}
    ).delete()

    assert checkout.user is None
    previous_last_change = checkout.last_change

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user2.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # when
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_impersonate_user]
    )

    # then
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
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.generate_deferred_payloads.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_customer_triggers_webhooks(
    mocked_generate_deferred_payloads,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event,
    setup_checkout_webhooks,
    settings,
    user_api_client,
    checkout_with_item,
    customer_user2,
    permission_impersonate_user,
    address,
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

    # Ensure shipping is set so shipping webhooks are emitted
    checkout.shipping_address = address
    checkout.billing_address = address

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

    assert wrapped_call_checkout_event.called

    # confirm that event delivery was generated for each async webhook.
    checkout_update_delivery = EventDelivery.objects.get(
        webhook_id=checkout_updated_webhook.id
    )

    mocked_generate_deferred_payloads.assert_called_once_with(
        kwargs={
            "event_delivery_ids": [checkout_update_delivery.id],
            "deferred_payload_data": {
                "model_name": "checkout.checkout",
                "object_id": checkout_with_item.pk,
                "requestor_model_name": "account.user",
                "requestor_object_id": user_api_client.user.pk,
                "request_time": None,
            },
            "send_webhook_queue": settings.CHECKOUT_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
            "telemetry_context": ANY,
        },
        MessageGroupId="example.com",
    )

    # Deferred payload covers the sync and async actions
    assert not mocked_send_webhook_request_async.called
    assert not mocked_send_webhook_request_sync.called


@freeze_time("2024-05-31 12:00:01")
def test_checkout_customer_attach_do_not_mark_shipping_as_stale(
    user_api_client,
    checkout_with_item,
    customer_user2,
    permission_impersonate_user,
    checkout_delivery,
    address,
):
    # given
    expected_stale_time = timezone.now() + timezone.timedelta(minutes=10)

    checkout = checkout_with_item
    checkout.email = "old@email.com"
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = expected_stale_time
    checkout.save(
        update_fields=[
            "assigned_delivery",
            "shipping_address",
            "delivery_methods_stale_at",
        ]
    )

    query = MUTATION_CHECKOUT_CUSTOMER_ATTACH
    customer_id = graphene.Node.to_global_id("User", customer_user2.pk)
    variables = {"id": to_global_id_or_none(checkout), "customerId": customer_id}

    # when
    new_now = timezone.now() + timezone.timedelta(minutes=1)
    with freeze_time(new_now):
        response = user_api_client.post_graphql(
            query, variables, permissions=[permission_impersonate_user]
        )

    # then
    content = get_graphql_content(response)

    data = content["data"]["checkoutCustomerAttach"]
    assert not data["errors"]
    assert data["checkout"]["email"] == customer_user2.email
    checkout.refresh_from_db()
    assert checkout.delivery_methods_stale_at == expected_stale_time
