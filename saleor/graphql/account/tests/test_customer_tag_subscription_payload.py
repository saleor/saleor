import json

import graphene

from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)

CUSTOMER_TAG_ASSIGNED_SUBSCRIPTION = """
    subscription {
        event {
            ... on CustomerTagAssigned {
                user {
                    id
                }
                customerTags {
                    id
                    slug
                }
            }
        }
    }
"""

CUSTOMER_TAG_UNASSIGNED_SUBSCRIPTION = """
    subscription {
        event {
            ... on CustomerTagUnassigned {
                user {
                    id
                }
                customerTags {
                    id
                    slug
                }
            }
        }
    }
"""


def test_customer_tag_assigned_subscription_payload(
    subscription_webhook, customer_user, customer_tag
):
    # given
    event_type = WebhookEventAsyncType.CUSTOMER_TAG_ASSIGNED
    webhook = subscription_webhook(CUSTOMER_TAG_ASSIGNED_SUBSCRIPTION, event_type)
    subject = {"user": customer_user, "customer_tags": [customer_tag]}

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, subject, [webhook])

    # then
    assert len(deliveries) == 1
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload["user"]["id"] == graphene.Node.to_global_id("User", customer_user.pk)
    assert payload["customerTags"] == [
        {
            "id": graphene.Node.to_global_id("CustomerTag", customer_tag.pk),
            "slug": customer_tag.slug,
        }
    ]


def test_customer_tag_unassigned_subscription_payload(
    subscription_webhook, customer_user, customer_tag
):
    # given
    event_type = WebhookEventAsyncType.CUSTOMER_TAG_UNASSIGNED
    webhook = subscription_webhook(CUSTOMER_TAG_UNASSIGNED_SUBSCRIPTION, event_type)
    subject = {"user": customer_user, "customer_tags": [customer_tag]}

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, subject, [webhook])

    # then
    assert len(deliveries) == 1
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload["user"]["id"] == graphene.Node.to_global_id("User", customer_user.pk)
    assert payload["customerTags"][0]["slug"] == customer_tag.slug
