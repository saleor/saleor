import graphene
import pytest

from saleor.graphql.tests.utils import get_graphql_content

EVENT_DELIVERY_FILTER_QUERY = """
    query webhook(
      $id: ID!
      $first: Int, $last: Int, $after: String, $before: String,
      $filters: EventDeliveryFilterInput!
    ){
      webhook(id: $id){
        deliveries(
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


@pytest.mark.parametrize(
    "filter_value",
    ["SUCCESS", "PENDING", "FAILED"],
)
def test_delivery_status_filter(
    filter_value, event_delivery, staff_api_client, permission_manage_apps
):
    # given
    webhook_id = graphene.Node.to_global_id("Webhook", event_delivery.webhook.pk)
    variables = {"filters": {"status": filter_value}, "id": webhook_id, "first": 3}
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    response = staff_api_client.post_graphql(
        EVENT_DELIVERY_FILTER_QUERY, variables=variables
    )
    content = get_graphql_content(response)
    delivery_response = content["data"]["webhook"]["deliveries"]

    # then
    if filter_value == event_delivery.status.upper():
        delivery_response = delivery_response["edges"][0]["node"]
        assert delivery_response["status"] == filter_value
        assert delivery_response["id"] == graphene.Node.to_global_id(
            "EventDelivery", event_delivery.pk
        )
    else:
        assert len(delivery_response["edges"]) == 0
