import graphene

from .....order.models import FulfillmentStatus
from .....page.models import PageType
from ....tests.utils import get_graphql_content
from .test_fulfillment_return_products import ORDER_FULFILL_RETURN_MUTATION


def test_fulfillment_return_products_app_omits_reason_reference_when_configured(
    app_api_client,
    permission_manage_orders,
    order_with_lines,
    site_settings,
):
    # given - global reasonReference is always optional for apps
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.return_reason_reference_type = page_type
    site_settings.save(update_fields=["return_reason_reference_type"])

    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.pk)
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.pk)

    variables = {
        "order": order_id,
        "input": {
            "orderLines": [
                {
                    "orderLineId": line_id,
                    "quantity": 1,
                    "replace": False,
                },
            ],
            "reason": "Return reason without reference",
        },
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_FULFILL_RETURN_MUTATION,
        variables,
        permissions=(permission_manage_orders,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderFulfillmentReturnProducts"]
    errors = data["errors"]
    assert not errors

    return_fulfillment = data["returnFulfillment"]
    assert return_fulfillment["status"] == FulfillmentStatus.RETURNED.upper()
