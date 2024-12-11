from typing import Union

import pytest

from ....app.models import App
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.models import Webhook, WebhookEvent


@pytest.fixture
def webhook(app):
    webhook = Webhook.objects.create(
        name="Simple webhook", app=app, target_url="http://www.example.com/test"
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    return webhook


@pytest.fixture
def webhook_without_name(app):
    webhook = Webhook.objects.create(app=app, target_url="http://www.example.com/test")
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    return webhook


@pytest.fixture
def webhook_removed_app(removed_app):
    webhook = Webhook.objects.create(
        name="Removed app webhook",
        app=removed_app,
        target_url="http://www.example.com/test",
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    return webhook


@pytest.fixture
def any_webhook(app):
    webhook = Webhook.objects.create(
        name="Any webhook", app=app, target_url="http://www.example.com/any"
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ANY)
    return webhook


@pytest.fixture
def observability_webhook(db, permission_manage_observability):
    app = App.objects.create(name="Observability App", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_observability)

    webhook = Webhook.objects.create(
        name="observability-webhook-1",
        app=app,
        target_url="https://observability-app.com/api/",
    )
    webhook.events.create(event_type=WebhookEventAsyncType.OBSERVABILITY)
    return webhook


@pytest.fixture
def webhooks_without_events(apps_without_webhooks):
    NUMBER_OF_WEBHOOKS_PER_APP = 6
    webhooks = []

    for app in apps_without_webhooks[:2]:
        for index in range(NUMBER_OF_WEBHOOKS_PER_APP):
            webhook = Webhook(
                name=f"Webhook_{index}",
                app=app,
                target_url=f"http://localhost/test_{index}",
                is_active=index % 2,
            )
            webhooks.append(webhook)

    return Webhook.objects.bulk_create(webhooks)


@pytest.fixture
def setup_checkout_webhooks(
    permission_handle_taxes,
    permission_manage_shipping,
    permission_manage_checkouts,
):
    subscription_async_webhooks = """
    fragment IssuingPrincipal on IssuingPrincipal {
      ... on App {
        id
        name
      }
      ... on User {
        id
        email
      }
    }

    fragment CheckoutFragment on Checkout {
      shippingMethods {
        id
        name
      }
      shippingPrice {
        gross {
          amount
        }
      }
      totalPrice {
        gross {
          amount
        }
      }
    }

    subscription {
      event {
        ... on CheckoutCreated {
          issuingPrincipal {
            ...IssuingPrincipal
          }
          checkout {
            ...CheckoutFragment
          }
        }
        ... on CheckoutUpdated {
          issuingPrincipal {
            ...IssuingPrincipal
          }
          checkout {
            ...CheckoutFragment
          }
        }
        ... on CheckoutFullyPaid {
          issuingPrincipal {
            ...IssuingPrincipal
          }
          checkout {
            ...CheckoutFragment
          }
        }
        ... on CheckoutMetadataUpdated {
          issuingPrincipal {
            ...IssuingPrincipal
          }
          checkout {
            ...CheckoutFragment
          }
        }
      }
    }
    """

    def _setup(additional_checkout_event):
        tax_app, shipping_app, additional_app = App.objects.bulk_create(
            [
                App(
                    name="Sample tax app",
                    is_active=True,
                    identifier="saleor.app.tax",
                ),
                App(
                    name="Sample shipping app",
                    is_active=True,
                    identifier="saleor.app.shipping",
                ),
                App(
                    name="Sample async webhook app",
                    is_active=True,
                    identifier="saleor.app.additional",
                ),
            ]
        )
        tax_app.permissions.add(permission_handle_taxes)
        shipping_app.permissions.set(
            [permission_manage_shipping, permission_manage_checkouts]
        )
        additional_app.permissions.add(permission_manage_checkouts)
        (
            tax_webhook,
            shipping_webhook,
            shipping_filter_webhook,
            additional_webhook,
        ) = Webhook.objects.bulk_create(
            [
                Webhook(
                    name="Tax webhook",
                    app=tax_app,
                    target_url="http://127.0.0.1/test",
                    subscription_query="subscription{ event{ ...on CalculateTaxes{ __typename } } }",
                ),
                Webhook(
                    name="Shipping webhook",
                    app=shipping_app,
                    target_url="http://127.0.0.1/test",
                    subscription_query="subscription { event { ... on ShippingListMethodsForCheckout { __typename } } }",
                ),
                Webhook(
                    name="Shipping webhook",
                    app=shipping_app,
                    target_url="http://127.0.0.1/test",
                    subscription_query="subscription { event { ... on CheckoutFilterShippingMethods { __typename } } }",
                ),
                Webhook(
                    name="Checkout additional webhook",
                    app=additional_app,
                    target_url="http://127.0.0.1/test",
                    subscription_query=subscription_async_webhooks,
                ),
            ]
        )

        WebhookEvent.objects.bulk_create(
            [
                WebhookEvent(
                    event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                    webhook_id=tax_webhook.id,
                ),
                WebhookEvent(
                    event_type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
                    webhook_id=shipping_filter_webhook.id,
                ),
                WebhookEvent(
                    event_type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                    webhook_id=shipping_webhook.id,
                ),
                WebhookEvent(
                    event_type=additional_checkout_event,
                    webhook_id=additional_webhook.id,
                ),
            ]
        )
        return (
            tax_webhook,
            shipping_webhook,
            shipping_filter_webhook,
            additional_webhook,
        )

    return _setup


@pytest.fixture
def setup_order_webhooks(
    permission_handle_taxes,
    permission_manage_shipping,
    permission_manage_orders,
):
    subscription_async_webhooks = """
    fragment OrderFragment on Order {
      shippingPrice {
        gross {
          amount
        }
      }
      total {
        gross {
          amount
        }
      }
    }

    subscription {
      event {
        ... on OrderCreated {
          order {
            ...OrderFragment
          }
        }
        ... on OrderUpdated {
          order {
            ...OrderFragment
          }
        }
        ... on OrderPaid {
          order {
            ...OrderFragment
          }
        }
        ... on OrderExpired {
          order {
            ...OrderFragment
          }
        }
        ... on OrderRefunded {
          order {
            ...OrderFragment
          }
        }
        ... on OrderConfirmed {
          order {
            ...OrderFragment
          }
        }
        ... on OrderFullyPaid {
          order {
            ...OrderFragment
          }
        }
        ... on OrderFulfilled {
          order {
            ...OrderFragment
          }
        }
        ... on OrderCancelled {
          order {
            ...OrderFragment
          }
        }
        ... on OrderBulkCreated {
          orders {
            ...OrderFragment
          }
        }
        ... on OrderFullyRefunded {
          order {
            ...OrderFragment
          }
        }
        ... on OrderMetadataUpdated {
          order {
            ...OrderFragment
          }
        }
        ... on DraftOrderCreated {
          order {
            ...OrderFragment
          }
        }
        ... on DraftOrderUpdated {
          order {
            ...OrderFragment
          }
        }
        ... on DraftOrderDeleted {
          order {
            ...OrderFragment
          }
        }
      }
    }
    """

    def _setup(additional_order_event: Union[str, list[str]]):
        tax_app, shipping_app, additional_app = App.objects.bulk_create(
            [
                App(
                    name="Sample tax app",
                    is_active=True,
                    identifier="saleor.app.tax",
                ),
                App(
                    name="Sample shipping app",
                    is_active=True,
                    identifier="saleor.app.shipping",
                ),
                App(
                    name="Sample async webhook app",
                    is_active=True,
                    identifier="saleor.app.additional",
                ),
            ]
        )
        tax_app.permissions.add(permission_handle_taxes)
        shipping_app.permissions.set(
            [permission_manage_shipping, permission_manage_orders]
        )
        additional_app.permissions.add(permission_manage_orders)
        (
            tax_webhook,
            shipping_filter_webhook,
            additional_webhook,
        ) = Webhook.objects.bulk_create(
            [
                Webhook(
                    name="Tax webhook",
                    app=tax_app,
                    target_url="http://127.0.0.1/test",
                    subscription_query="subscription{ event{ ...on CalculateTaxes{ __typename } } }",
                ),
                Webhook(
                    name="Shipping webhook",
                    app=shipping_app,
                    target_url="http://127.0.0.1/test",
                    subscription_query="subscription { event { ... on OrderFilterShippingMethods { __typename } } }",
                ),
                Webhook(
                    name="Checkout additional webhook",
                    app=additional_app,
                    target_url="http://127.0.0.1/test",
                    subscription_query=subscription_async_webhooks,
                ),
            ]
        )
        if isinstance(additional_order_event, str):
            additional_order_event = [
                additional_order_event,
            ]
        additional_events = [
            WebhookEvent(
                event_type=event,
                webhook_id=additional_webhook.id,
            )
            for event in additional_order_event
        ]
        WebhookEvent.objects.bulk_create(
            [
                WebhookEvent(
                    event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES,
                    webhook_id=tax_webhook.id,
                ),
                WebhookEvent(
                    event_type=WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS,
                    webhook_id=shipping_filter_webhook.id,
                ),
            ]
            + additional_events
        )
        return (
            tax_webhook,
            shipping_filter_webhook,
            additional_webhook,
        )

    return _setup
