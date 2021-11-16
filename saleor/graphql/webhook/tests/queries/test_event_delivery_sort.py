import graphene
import pytest
from freezegun import freeze_time

from .....core.models import EventDelivery, EventDeliveryAttempt
from .....webhook.event_types import WebhookEventType
from ....tests.utils import get_graphql_content

EVENT_DELIVERY_SORT_QUERY = """
    query webhook(
      $id: ID!
      $first: Int, $last: Int, $after: String, $before: String,
      $sortBy: EventDeliverySortingInput
    ){
      webhook(id: $id){
        deliveries(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy

        ){
           edges{
             node{
               eventType
               id
            }
          }
        }
      }
    }
"""


@pytest.mark.parametrize(
    "event_delivery_sort",
    [
        {"field": "CREATED_AT", "direction": "ASC"},
        {"field": "CREATED_AT", "direction": "DESC"},
    ],
)
def test_webhook_delivery_query_sort(
    event_delivery_sort,
    webhook,
    event_payload,
    staff_api_client,
    permission_manage_apps,
):
    # given
    with freeze_time("2020-03-18 12:00:00"):
        delivery_new = EventDelivery.objects.create(
            event_type=WebhookEventType.ORDER_CREATED,
            payload=event_payload,
            webhook=webhook,
        )
    with freeze_time("2020-03-18 13:00:00"):
        delivery_old = EventDelivery.objects.create(
            event_type=WebhookEventType.ORDER_CANCELLED,
            payload=event_payload,
            webhook=webhook,
        )
    delivery_new_id = graphene.Node.to_global_id("EventDelivery", delivery_new.pk)
    delivery_old_id = graphene.Node.to_global_id("EventDelivery", delivery_old.pk)
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"id": webhook_id, "first": 2, "sortBy": event_delivery_sort}

    # when
    response = staff_api_client.post_graphql(
        EVENT_DELIVERY_SORT_QUERY, variables=variables
    )
    content = get_graphql_content(response)
    deliveries_response = content["data"]["webhook"]["deliveries"]["edges"]

    # then
    if event_delivery_sort["direction"] == "ASC":
        assert deliveries_response[0]["node"]["id"] == delivery_new_id
        assert deliveries_response[1]["node"]["id"] == delivery_old_id

    if event_delivery_sort["direction"] == "DESC":
        assert deliveries_response[0]["node"]["id"] == delivery_old_id
        assert deliveries_response[1]["node"]["id"] == delivery_new_id


EVENT_DELIVERY_ATTEMPT_SORT_QUERY = """
    query webhook(
      $id: ID!
      $first: Int,
      $sortBy: EventDeliverySortingInput
    ){
      webhook(id: $id){
        deliveries(
            first: $first
        ){
           edges{
             node{
               eventType
               id
               attempts(first: $first sortBy: $sortBy){
                 edges{
                   node{
                     id
                     taskId
                     createdAt
                     response
                   }
                 }
               }
             }
           }
        }
      }
    }
"""


@pytest.mark.parametrize(
    "event_delivery_attempt_sort",
    [
        {"field": "CREATED_AT", "direction": "ASC"},
        {"field": "CREATED_AT", "direction": "DESC"},
    ],
)
def test_webhook_delivery_attempt__query_sort(
    event_delivery_attempt_sort,
    event_delivery,
    staff_api_client,
    permission_manage_apps,
):
    # given
    with freeze_time("2020-03-18 12:00:00"):
        attempt_new = EventDeliveryAttempt.objects.create(
            delivery=event_delivery,
            task_id="example_old_task_id",
            duration=None,
            response="example_old_response",
            response_headers=None,
            request_headers=None,
        )

    with freeze_time("2020-03-18 13:00:00"):
        attempt_old = EventDeliveryAttempt.objects.create(
            delivery=event_delivery,
            task_id="example_new_task_id",
            duration=None,
            response="example_new_response",
            response_headers=None,
            request_headers=None,
        )

    attempt_new_id = graphene.Node.to_global_id("EventDeliveryAttempt", attempt_new.pk)
    attempt_old_id = graphene.Node.to_global_id("EventDeliveryAttempt", attempt_old.pk)
    webhook_id = graphene.Node.to_global_id("Webhook", event_delivery.webhook.pk)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"id": webhook_id, "first": 2, "sortBy": event_delivery_attempt_sort}

    # when
    response = staff_api_client.post_graphql(
        EVENT_DELIVERY_ATTEMPT_SORT_QUERY, variables=variables
    )
    content = get_graphql_content(response)
    deliveries_response = content["data"]["webhook"]["deliveries"]["edges"][0]
    attempts_response = deliveries_response["node"]["attempts"]["edges"]

    # then
    if event_delivery_attempt_sort["direction"] == "ASC":
        assert attempts_response[0]["node"]["id"] == attempt_new_id
        assert attempts_response[1]["node"]["id"] == attempt_old_id

    if event_delivery_attempt_sort["direction"] == "DESC":
        assert attempts_response[0]["node"]["id"] == attempt_old_id
        assert attempts_response[1]["node"]["id"] == attempt_new_id
