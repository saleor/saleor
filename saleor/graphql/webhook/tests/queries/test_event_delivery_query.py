import datetime

import graphene

from .....core import EventDeliveryStatus
from .....core.models import EventDelivery
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import get_graphql_content

EVENT_DELIVERY_QUERY = """
    query webhook(
      $id: ID!
      $first: Int, $last: Int, $after: String, $before: String,
    ){
      webhook(id: $id){
        eventDeliveries(
            first: $first, last: $last, after: $after, before: $before,
        ){
           edges{
             node{
               status
               eventType
               id
               payload
               attempts(first: $first){
                edges{
                  node{
                    id
                    duration
                    response
                    requestHeaders
                    responseHeaders
                    responseStatusCode
                  }
                }
              }
            }
          }
        }
      }
    }
"""


EVENT_DELIVERIES_PAGINATION_QUERY = """
    query webhook($id: ID!, $first: Int!, $after: String){
      webhook(id: $id){
        eventDeliveries(first: $first, after: $after){
          pageInfo{
            hasNextPage
            endCursor
          }
          edges{
            node{
              id
            }
          }
        }
      }
    }
"""


def _fetch_event_deliveries_page(client, webhook_id, first, after=None):
    response = client.post_graphql(
        EVENT_DELIVERIES_PAGINATION_QUERY,
        variables={"id": webhook_id, "first": first, "after": after},
    )
    data = get_graphql_content(response)["data"]["webhook"]["eventDeliveries"]
    return [edge["node"]["id"] for edge in data["edges"]], data["pageInfo"]


def test_event_deliveries_pagination_with_shared_created_at(
    webhook, staff_api_client, permission_manage_apps
):
    """Walk three pages of deliveries sharing the model's default ordering value.

    The default ordering (`-created_at`) is not unique - deliveries fanned out for
    a single event are bulk created and can land on the same timestamp - so without
    a tie-breaker the cursor cannot advance past such a group.
    """
    # given
    page_size = 2
    deliveries = EventDelivery.objects.bulk_create(
        [
            EventDelivery(webhook=webhook, event_type=WebhookEventAsyncType.ANY)
            for _ in range(5)
        ]
    )
    delivery_pks = [delivery.pk for delivery in deliveries]
    # `created_at` is `auto_now_add`, so the shared timestamp has to be forced in SQL
    EventDelivery.objects.filter(pk__in=delivery_pks).update(
        created_at=datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC)
    )
    # the deliveries tie on `created_at`, so they fall back to descending pk
    expected_ids = [
        graphene.Node.to_global_id("EventDelivery", pk) for pk in reversed(delivery_pks)
    ]
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    first_page_ids, first_page_info = _fetch_event_deliveries_page(
        staff_api_client, webhook_id, page_size
    )
    second_page_ids, second_page_info = _fetch_event_deliveries_page(
        staff_api_client, webhook_id, page_size, after=first_page_info["endCursor"]
    )
    third_page_ids, third_page_info = _fetch_event_deliveries_page(
        staff_api_client, webhook_id, page_size, after=second_page_info["endCursor"]
    )

    # then
    assert first_page_ids == expected_ids[:2]
    assert first_page_info["hasNextPage"] is True

    assert second_page_ids == expected_ids[2:4]
    assert second_page_info["hasNextPage"] is True
    assert second_page_info["endCursor"] != first_page_info["endCursor"]

    assert third_page_ids == expected_ids[4:]
    assert third_page_info["hasNextPage"] is False


def test_webhook_delivery_attempt_query(
    event_attempt, staff_api_client, permission_manage_apps
):
    # given
    webhook_id = graphene.Node.to_global_id(
        "Webhook", event_attempt.delivery.webhook.pk
    )
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"id": webhook_id, "first": 3}
    delivery = event_attempt.delivery
    delivery_id = graphene.Node.to_global_id("EventDelivery", delivery.pk)

    # when
    response = staff_api_client.post_graphql(EVENT_DELIVERY_QUERY, variables=variables)
    content = get_graphql_content(response)
    delivery_response = content["data"]["webhook"]["eventDeliveries"]["edges"][0][
        "node"
    ]
    attempts_response = delivery_response["attempts"]["edges"]

    # then
    assert delivery_response["id"] == delivery_id
    assert delivery_response["status"] == EventDeliveryStatus.PENDING.upper()
    assert delivery_response["eventType"] == WebhookEventAsyncType.ANY.upper()
    assert delivery_response["payload"] == delivery.payload.get_payload()
    assert len(attempts_response) == 1
    assert attempts_response[0]["node"]["response"] == event_attempt.response
    assert attempts_response[0]["node"]["duration"] == event_attempt.duration
    assert (
        attempts_response[0]["node"]["requestHeaders"] == event_attempt.request_headers
    )
    assert (
        attempts_response[0]["node"]["responseHeaders"]
        == event_attempt.response_headers
    )
    assert (
        attempts_response[0]["node"]["responseStatusCode"]
        == event_attempt.response_status_code
    )


def test_webhook_delivery_attempt_query_deprecated_payload_in_database(
    event_attempt_payload_in_database, staff_api_client, permission_manage_apps
):
    # given
    event_attempt = event_attempt_payload_in_database
    webhook_id = graphene.Node.to_global_id(
        "Webhook", event_attempt.delivery.webhook.pk
    )
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"id": webhook_id, "first": 3}
    delivery = event_attempt.delivery
    delivery_id = graphene.Node.to_global_id("EventDelivery", delivery.pk)

    # when
    response = staff_api_client.post_graphql(EVENT_DELIVERY_QUERY, variables=variables)
    content = get_graphql_content(response)
    delivery_response = content["data"]["webhook"]["eventDeliveries"]["edges"][0][
        "node"
    ]
    attempts_response = delivery_response["attempts"]["edges"]

    # then
    assert delivery_response["id"] == delivery_id
    assert delivery_response["status"] == EventDeliveryStatus.PENDING.upper()
    assert delivery_response["eventType"] == WebhookEventAsyncType.ANY.upper()
    assert (
        delivery_response["payload"]
        == delivery.payload.get_payload()
        == delivery.payload.payload
    )
    assert len(attempts_response) == 1
    assert attempts_response[0]["node"]["response"] == event_attempt.response
    assert attempts_response[0]["node"]["duration"] == event_attempt.duration
    assert (
        attempts_response[0]["node"]["requestHeaders"] == event_attempt.request_headers
    )
    assert (
        attempts_response[0]["node"]["responseHeaders"]
        == event_attempt.response_headers
    )
    assert (
        attempts_response[0]["node"]["responseStatusCode"]
        == event_attempt.response_status_code
    )
