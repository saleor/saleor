import json

import graphene

from .....webhook.event_types import WebhookEventSyncType
from .....webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)
from .payloads import generate_payment_payload


def test_payment_authorize(payment, subscription_payment_authorize_webhook):
    # given
    webhooks = [subscription_payment_authorize_webhook]
    event_type = WebhookEventSyncType.PAYMENT_AUTHORIZE

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, payment, webhooks)

    # then
    expected_payload = generate_payment_payload(payment)
    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_payment_capture(payment, subscription_payment_capture_webhook):
    # given
    webhooks = [subscription_payment_capture_webhook]
    event_type = WebhookEventSyncType.PAYMENT_CAPTURE

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, payment, webhooks)

    # then
    expected_payload = generate_payment_payload(payment)
    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_payment_refund(payment, subscription_payment_refund_webhook):
    # given
    webhooks = [subscription_payment_refund_webhook]
    event_type = WebhookEventSyncType.PAYMENT_REFUND

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, payment, webhooks)

    # then
    expected_payload = generate_payment_payload(payment)
    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_payment_void(payment, subscription_payment_void_webhook):
    # given
    webhooks = [subscription_payment_void_webhook]
    event_type = WebhookEventSyncType.PAYMENT_VOID

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, payment, webhooks)

    # then
    expected_payload = generate_payment_payload(payment)
    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_payment_confirm(payment, subscription_payment_confirm_webhook):
    # given
    webhooks = [subscription_payment_confirm_webhook]
    event_type = WebhookEventSyncType.PAYMENT_CONFIRM

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, payment, webhooks)

    # then
    expected_payload = generate_payment_payload(payment)
    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_payment_process(payment, subscription_payment_process_webhook):
    # given
    webhooks = [subscription_payment_process_webhook]
    event_type = WebhookEventSyncType.PAYMENT_PROCESS

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, payment, webhooks)

    # then
    expected_payload = generate_payment_payload(payment)
    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_payment_list_gateways(checkout, subscription_payment_list_gateways_webhook):
    # given

    webhooks = [subscription_payment_list_gateways_webhook]
    event_type = WebhookEventSyncType.PAYMENT_LIST_GATEWAYS
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when

    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)

    # then
    expected_payload = {"checkout": {"id": checkout_id}}
    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]
