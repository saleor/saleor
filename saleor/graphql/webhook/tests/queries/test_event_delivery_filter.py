import graphene

from .....core import EventDeliveryStatus
from ....tests.utils import get_graphql_content

EVENT_DELIVERY_FILTER_QUERY = """
    query webhook(
      $id: ID!
      $first: Int, $last: Int, $after: String, $before: String,
      $filters: EventDeliveryFilterInput!
    ){
      webhook(id: $id){
        eventDeliveries(
            first: $first, last: $last, after: $after, before: $before,
            filter: $filters
        ){
           edges{
             node{
               status
               eventType
               id
            }
          }
        }
      }
    }
"""


def test_delivery_status_filter(
    event_delivery, staff_api_client, permission_manage_apps
):
    # given
    webhook_id = graphene.Node.to_global_id("Webhook", event_delivery.webhook.pk)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {
        "filters": {"status": EventDeliveryStatus.PENDING.upper()},
        "id": webhook_id,
        "first": 3,
    }
    # when
    response = staff_api_client.post_graphql(
        EVENT_DELIVERY_FILTER_QUERY, variables=variables
    )
    content = get_graphql_content(response)
    delivery_response = content["data"]["webhook"]["eventDeliveries"]

    # then
    assert delivery_response["edges"][0]["node"]["id"] == graphene.Node.to_global_id(
        "EventDelivery", event_delivery.pk
    )


def test_delivery_status_filter_no_results(
    event_delivery, staff_api_client, permission_manage_apps
):
    # given
    webhook_id = graphene.Node.to_global_id("Webhook", event_delivery.webhook.pk)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {
        "filters": {"status": EventDeliveryStatus.SUCCESS.upper()},
        "id": webhook_id,
        "first": 3,
    }
    # when
    response = staff_api_client.post_graphql(
        EVENT_DELIVERY_FILTER_QUERY, variables=variables
    )
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["webhook"]["eventDeliveries"]["edges"]) == 0
