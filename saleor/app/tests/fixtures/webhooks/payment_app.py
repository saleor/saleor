import pytest

from .....app.models import App
from .....webhook.event_types import WebhookEventSyncType
from .....webhook.models import Webhook, WebhookEvent
from .....webhook.tests.subscription_webhooks import subscription_queries


@pytest.fixture
def payment_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment App", is_active=True, identifier="saleor.payment.test.app"
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment-webhook-1",
        app=app,
        target_url="https://payment-gateway.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in WebhookEventSyncType.PAYMENT_EVENTS
        ]
    )
    return app


@pytest.fixture
def payment_app_with_subscription_webhooks(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment App", is_active=True, identifier="saleor.payment.test.app"
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment-subscription-webhook-1",
        app=app,
        target_url="https://payment-gateway.com/api/",
        subscription_query=subscription_queries.PAYMENT_AUTHORIZE,
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in WebhookEventSyncType.PAYMENT_EVENTS
        ]
    )
    return app


@pytest.fixture
def list_stored_payment_methods_app(db, permission_manage_payments):
    app = App.objects.create(
        name="List payment methods app",
        is_active=True,
        identifier="saleor.payment.app.list.stored.method",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="list_stored_payment_methods",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
    )
    return app


@pytest.fixture
def stored_payment_method_request_delete_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment method request delete",
        is_active=True,
        identifier="saleor.payment.app.payment.method.request.delete",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="stored_payment_method_request_delete",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.STORED_PAYMENT_METHOD_DELETE_REQUESTED,
    )
    return app


@pytest.fixture
def payment_gateway_initialize_tokenization_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment method request delete",
        is_active=True,
        identifier="saleor.payment.app.payment.gateway.initialize.tokenization",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment_gateway_initialize_tokenization",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION,
    )
    return app


@pytest.fixture
def payment_method_initialize_tokenization_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment method initialize tokenization",
        is_active=True,
        identifier="saleor.payment.app.payment.method.initialize.tokenization",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment_method_initialize_tokenization",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION,
    )
    return app


@pytest.fixture
def payment_method_process_tokenization_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment method process tokenization",
        is_active=True,
        identifier="saleor.payment.app.payment.method.process.tokenization",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment_method_process_tokenization",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION,
    )
    return app


@pytest.fixture
def payment_gateway_initialize_session_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment gateway initialize session",
        is_active=True,
        identifier="saleor.payment.app.payment.gateway.initialize.session",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment_gateway_initialize_session",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    )
    return app


@pytest.fixture
def transaction_process_session_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Transaction process session",
        is_active=True,
        identifier="saleor.payment.app.transaction.process.session",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="transaction_process_session",
        app=app,
        target_url="http://localhost:8000/endpoint/",
        subscription_query="""
            subscription TransactionProcessSession {
                event {
                    ... on TransactionProcessSession {
                        recipient {
                            id
                        }
                        data
                        merchantReference
                        action {
                            amount
                            currency
                            actionType
                        }
                        transaction {
                            id
                            token
                            pspReference
                            events {
                                pspReference
                            }
                        }
                        sourceObject {
                            ... on Checkout {
                                id
                                token
                                totalPrice {
                                    gross {
                                        currency
                                        amount
                                    }
                                }
                                shippingMethods {
                                    id
                                    name
                                }
                            }
                            ... on Order {
                                id
                                total {
                                    gross {
                                        currency
                                        amount
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_PROCESS_SESSION)
    return app


@pytest.fixture
def transaction_initialize_session_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Transaction initialize session",
        is_active=True,
        identifier="saleor.payment.app.transaction.initialize.session",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="Webhook",
        app=app,
        target_url="http://www.example.com",
        subscription_query="""
            subscription TransactionInitializeSession {
                event {
                    ... on TransactionInitializeSession {
                        transaction {
                            id
                        }
                        sourceObject {
                            ... on Checkout {
                                id
                                shippingMethods {
                                    id
                                    name
                                }
                                totalPrice {
                                    gross {
                                        amount
                                        currency
                                    }
                                }
                            }
                            ... on Order {
                                total {
                                    gross {
                                        amount
                                        currency
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """,
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.TRANSACTION_INITIALIZE_SESSION
    )
    return app
