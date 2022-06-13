from decimal import Decimal
from functools import partial

import graphene
import pytest
from prices import TaxedMoney, percentage_discount

from .....discount import DiscountValueType
from .....order import OrderEvents, OrderStatus
from ....discount.enums import DiscountValueTypeEnum
from ....tests.utils import get_graphql_content

ORDER_DISCOUNT_DELETE = """
mutation OrderDiscountDelete($discountId: ID!){
  orderDiscountDelete(discountId: $discountId){
    order{
      id
    }
    errors{
      field
      message
      code
    }
  }
}
"""


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
def test_delete_order_discount_from_order_with_old_id(
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_manage_orders,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = status
    order.save(update_fields=["status"])

    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    name = "discount translated"
    translated_name = "discount translated name"
    order_discount.name = name
    order_discount.translated_name = translated_name
    order_discount.old_id = 1
    order_discount.save(update_fields=["name", "translated_name", "old_id"])

    current_undiscounted_total = order.undiscounted_total

    variables = {
        "discountId": graphene.Node.to_global_id(
            "OrderDiscount", order_discount.old_id
        ),
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountDelete"]

    order.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 0

    assert order.undiscounted_total == current_undiscounted_total
    assert order.total == current_undiscounted_total

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_DELETED

    assert order.search_vector


ORDER_DISCOUNT_UPDATE = """
mutation OrderDiscountUpdate($discountId: ID!, $input: OrderDiscountCommonInput!){
  orderDiscountUpdate(discountId:$discountId, input: $input){
    order{
      id
      total{
        gross{
          amount
        }
      }
      undiscountedTotal{
        gross{
          amount
        }
      }
    }
    errors{
        field
        message
        code
      }
  }
}
"""


@pytest.mark.parametrize("status", (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED))
def test_update_percentage_order_discount_by_old_id(
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_manage_orders,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = status
    order.save(update_fields=["status"])

    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    order_discount.old_id = 1
    order_discount.save(update_fields=["old_id"])

    current_undiscounted_total = order.undiscounted_total

    reason = "The reason of the discount"
    value = Decimal("10.000")
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "value": value,
            "reason": reason,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    order.refresh_from_db()

    discount = partial(percentage_discount, percentage=value)
    expected_net_total = discount(current_undiscounted_total.net)
    expected_gross_total = discount(current_undiscounted_total.gross)
    expected_total = TaxedMoney(expected_net_total, expected_gross_total)

    errors = data["errors"]
    assert len(errors) == 0

    assert order.undiscounted_total == current_undiscounted_total

    assert expected_total == order.total

    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.PERCENTAGE
    assert order_discount.amount == (current_undiscounted_total - expected_total).gross
    assert order_discount.reason == reason

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_UPDATED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.PERCENTAGE.value
    assert discount_data["amount_value"] == str(order_discount.amount.amount)
