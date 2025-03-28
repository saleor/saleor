from decimal import Decimal
from functools import partial
from unittest.mock import patch

import graphene
import pytest
from prices import Money, TaxedMoney, fixed_discount, percentage_discount

from .....core.prices import quantize_price
from .....core.taxes import zero_money
from .....discount import DiscountType, DiscountValueType, VoucherType
from .....discount.utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
)
from .....order import OrderEvents, OrderStatus
from .....order.calculations import fetch_order_prices_if_expired
from .....order.error_codes import OrderErrorCode
from .....order.interface import OrderTaxedPricesData
from ....discount.enums import DiscountValueTypeEnum
from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_DISCOUNT_ADD = """
mutation OrderDiscountAdd($orderId: ID!, $input: OrderDiscountCommonInput!){
  orderDiscountAdd(orderId:$orderId, input:$input){
    order{
      lines{
        id
      }
    }
    errors{
      field
      code
      message
    }
  }
}
"""


@pytest.mark.parametrize(
    ("value", "value_type"),
    [
        (Decimal("2222222"), DiscountValueTypeEnum.FIXED.name),
        (Decimal("101"), DiscountValueTypeEnum.PERCENTAGE.name),
    ],
)
def test_add_order_discount_incorrect_values(
    value, value_type, draft_order, staff_api_client, permission_group_manage_orders
):
    # given
    variables = {
        "orderId": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {"valueType": value_type, "value": value},
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]
    errors = data["errors"]
    error = data["errors"][0]
    assert error["field"] == "value"
    assert error["code"] == OrderErrorCode.INVALID.name
    assert len(errors) == 1


def test_add_fixed_order_discount_order_is_not_draft(
    order_with_lines, staff_api_client, permission_group_manage_orders
):
    # given
    value = Decimal("10")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order_with_lines.pk),
        "input": {"valueType": DiscountValueTypeEnum.FIXED.name, "value": value},
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]

    errors = data["errors"]
    assert len(errors) == 1
    error = data["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_add_fixed_order_discount_to_order(
    status,
    draft_order,
    staff_api_client,
    permission_group_manage_orders,
    plugins_manager,
):
    # given
    order = draft_order
    order.status = status
    order.save(update_fields=["status"])
    total_before_order_discount = order.total
    value = Decimal("10.000")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {"valueType": DiscountValueTypeEnum.FIXED.name, "value": value},
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderDiscountAdd"]

    order.refresh_from_db()
    expected_net = total_before_order_discount.net.amount - value
    errors = data["errors"]
    assert len(errors) == 0

    assert order.should_refresh_prices
    fetch_order_prices_if_expired(order, plugins_manager)

    # Use `net` values in comparison due to that fixture have taxes incluted in
    # prices but after recalculation taxes are removed because in tests we
    # don't use any tax app.
    assert order.undiscounted_total.net == total_before_order_discount.net
    assert expected_net == order.total.net.amount

    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.amount.amount == value
    assert order_discount.reason is None

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_ADDED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.FIXED.value
    assert Decimal(discount_data["amount_value"]) == order_discount.amount.amount


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_add_percentage_order_discount_to_order(
    status,
    draft_order,
    staff_api_client,
    permission_group_manage_orders,
    plugins_manager,
):
    order = draft_order
    order.status = status
    order.save(update_fields=["status"])
    total_before_order_discount = order.total
    reason = "The reason of the discount"
    value = Decimal("10.000")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "value": value,
            "reason": reason,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]

    order.refresh_from_db()

    discount = partial(percentage_discount, percentage=value)
    expected_net_total = discount(total_before_order_discount.net)
    expected_gross_total = discount(total_before_order_discount.gross)
    expected_total = TaxedMoney(expected_net_total, expected_gross_total)

    errors = data["errors"]
    assert len(errors) == 0

    assert order.should_refresh_prices
    fetch_order_prices_if_expired(order, plugins_manager)

    # Use `net` values in comparison due to that fixture have taxes included in
    # prices but after recalculation taxes are removed because in tests we
    # don't use any tax app.
    assert expected_net_total == order.total.net
    assert order.undiscounted_total.net == total_before_order_discount.net

    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.PERCENTAGE
    discount_amount = total_before_order_discount.net - expected_total.net
    assert order_discount.amount == discount_amount
    assert order_discount.reason == reason

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_ADDED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.PERCENTAGE.value
    assert Decimal(discount_data["amount_value"]) == order_discount.amount.amount


def test_add_order_discount_to_order_by_user_no_channel_access(
    draft_order,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    order = draft_order
    order.status = OrderStatus.UNCONFIRMED
    order.channel = channel_PLN
    order.save(update_fields=["status", "channel"])
    value = Decimal("10.000")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {"valueType": DiscountValueTypeEnum.FIXED.name, "value": value},
    }
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)

    # then
    assert_no_permission(response)


def test_add_fixed_order_discount_to_order_by_app(
    draft_order, app_api_client, permission_manage_orders, plugins_manager
):
    # given
    order = draft_order
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    total_before_order_discount = order.total
    value = Decimal("10.000")
    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {"valueType": DiscountValueTypeEnum.FIXED.name, "value": value},
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_DISCOUNT_ADD, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]

    order.refresh_from_db()
    expected_net = total_before_order_discount.net.amount - value

    errors = data["errors"]
    assert len(errors) == 0

    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.amount.amount == value
    assert order_discount.reason is None

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_ADDED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.FIXED.value
    assert Decimal(discount_data["amount_value"]) == order_discount.amount.amount

    assert order.should_refresh_prices
    fetch_order_prices_if_expired(order, plugins_manager)

    # Use `net` values in comparison due to that fixture have taxes incluted in
    # prices but after recalculation taxes are removed because in tests we
    # don't use any tax app.
    assert order.undiscounted_total.net == total_before_order_discount.net
    assert expected_net == order.total.net.amount


def test_add_manual_discount_replaces_entire_voucher(
    order_with_lines,
    staff_api_client,
    permission_group_manage_orders,
    voucher,
    plugins_manager,
):
    """Order discount based on voucher:entire_order should be replaced with manual."""
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status", "should_refresh_prices"])

    expected_voucher_discount_amount = Decimal("12")
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.discount_value_type == DiscountValueType.FIXED

    voucher.channel_listings.update(discount_value=expected_voucher_discount_amount)

    order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=expected_voucher_discount_amount,
        amount_value=expected_voucher_discount_amount,
        currency=order.currency,
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    manual_discount_value = Decimal("10.00")

    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "value": manual_discount_value,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderDiscountAdd"]
    order.refresh_from_db()
    assert not data["errors"]

    assert order.discounts.count() == 1

    expected_discount_amount = order.undiscounted_total.net * (
        manual_discount_value / Decimal(100)
    )
    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.value == manual_discount_value
    assert manual_discount.value_type == DiscountValueType.PERCENTAGE
    assert manual_discount.amount.amount == expected_discount_amount.amount

    assert order.should_refresh_prices
    fetch_order_prices_if_expired(order, plugins_manager)

    assert (
        order.total_net_amount
        == order.undiscounted_total_net_amount - expected_discount_amount.amount
    )
    assert (
        order.shipping_price_net_amount + order.subtotal_net_amount
        == order.total_net_amount
    )


def test_add_manual_discount_keeps_shipping_voucher(
    draft_order_with_free_shipping_voucher,
    staff_api_client,
    permission_group_manage_orders,
    plugins_manager,
):
    """Order discount based on voucher:shipping should be retained when adding manual."""
    # given
    order = draft_order_with_free_shipping_voucher

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    manual_discount_value = Decimal("10.00")

    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": manual_discount_value,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderDiscountAdd"]
    order.refresh_from_db()
    assert not data["errors"]

    assert order.discounts.count() == 2

    shipping_discount = order.discounts.get(type=DiscountType.VOUCHER)
    assert shipping_discount.value == Decimal("100")
    assert shipping_discount.value_type == DiscountValueType.PERCENTAGE
    assert shipping_discount.amount == order.undiscounted_base_shipping_price

    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.value == manual_discount_value
    assert manual_discount.value_type == DiscountValueType.FIXED
    assert manual_discount.amount.amount == manual_discount_value

    applied_discount_amount = manual_discount_value + shipping_discount.amount_value

    assert order.should_refresh_prices
    fetch_order_prices_if_expired(order, plugins_manager)
    assert (
        order.total_net_amount
        == order.undiscounted_total_net_amount - applied_discount_amount
    )
    assert (
        order.shipping_price_net_amount + order.subtotal_net_amount
        == order.total_net_amount
    )


def test_add_manual_discount_replaces_order_promotion(
    order_with_lines_and_order_promotion,
    staff_api_client,
    permission_group_manage_orders,
    plugins_manager,
):
    """Order discount should be deleted in a favour of manual discount."""
    # given
    order = order_with_lines_and_order_promotion
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    discount_value = Decimal("10.00")

    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": discount_value,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderDiscountAdd"]
    order.refresh_from_db()
    assert not data["errors"]

    assert order.discounts.count() == 1

    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.value == discount_value
    assert manual_discount.value_type == DiscountValueType.FIXED
    assert manual_discount.amount.amount == discount_value

    assert order.should_refresh_prices
    fetch_order_prices_if_expired(order, plugins_manager)

    assert (
        order.total_net_amount == order.undiscounted_total_net_amount - discount_value
    )
    assert (
        order.shipping_price_net_amount + order.subtotal_net_amount
        == order.total_net_amount
    )


def test_add_manual_discount_replaces_gift_discount(
    order_with_lines_and_gift_promotion,
    staff_api_client,
    permission_group_manage_orders,
    plugins_manager,
):
    """Order discount should be deleted in a favour of manual discount."""
    # given
    order = order_with_lines_and_gift_promotion
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    assert order.lines.count() == 3
    gift_line = order.lines.filter(is_gift=True).first()
    assert gift_line
    assert gift_line.discounts.get()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    discount_value = Decimal("10.00")

    variables = {
        "orderId": graphene.Node.to_global_id("Order", order.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": discount_value,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_ADD, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderDiscountAdd"]
    order.refresh_from_db()
    assert not data["errors"]

    assert order.lines.count() == 2
    assert not order.lines.filter(is_gift=True).first()

    assert order.discounts.count() == 1

    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.value == discount_value
    assert manual_discount.value_type == DiscountValueType.FIXED
    assert manual_discount.amount.amount == discount_value

    assert order.should_refresh_prices
    fetch_order_prices_if_expired(order, plugins_manager)
    assert (
        order.total_net_amount == order.undiscounted_total_net_amount - discount_value
    )
    assert (
        order.shipping_price_net_amount + order.subtotal_net_amount
        == order.total_net_amount
    )


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


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_update_percentage_order_discount_to_order(
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    order = draft_order_with_fixed_discount_order
    order.status = status
    order.save(update_fields=["status"])
    order_discount = draft_order_with_fixed_discount_order.discounts.get()
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    order.refresh_from_db()

    discount = partial(percentage_discount, percentage=value)
    expected_net_total = discount(current_undiscounted_total.net)
    expected_gross_total = discount(current_undiscounted_total.gross)
    expected_total = TaxedMoney(expected_net_total, expected_gross_total)

    errors = data["errors"]
    assert len(errors) == 0

    # Use `net` values in comparison due to that fixture have taxes included in
    # prices but after recalculation taxes are removed because in tests we
    # don't use any tax app.
    assert order.undiscounted_total.net == current_undiscounted_total.net
    assert expected_net_total == order.total.net

    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.PERCENTAGE
    discount_amount = current_undiscounted_total.net - expected_total.net
    assert order_discount.amount == discount_amount
    assert order_discount.reason == reason

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_UPDATED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.PERCENTAGE.value
    assert discount_data["amount_value"] == str(discount_amount.amount)


@patch("saleor.order.calculations.PluginsManager.calculate_order_shipping")
@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_update_fixed_order_discount_to_order(
    mocked_function,
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    order = draft_order_with_fixed_discount_order
    mocked_function.return_value = order.shipping_price
    order.status = status
    order.save(update_fields=["status"])
    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    current_undiscounted_total = order.undiscounted_total

    value = Decimal("50.000")
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": value,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    order.refresh_from_db()

    discount = partial(fixed_discount, discount=Money(value, currency=order.currency))
    expected_total = discount(current_undiscounted_total)

    errors = data["errors"]
    assert len(errors) == 0

    # Use `net` values in comparison due to that fixture have taxes incluted in
    # prices but after recalculation taxes are removed because in tests we
    # don't use any tax app.
    assert order.undiscounted_total.net == current_undiscounted_total.net
    assert expected_total.net == order.total.net

    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.FIXED
    discount_amount = current_undiscounted_total.net - expected_total.net
    assert order_discount.amount == discount_amount

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_UPDATED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.FIXED.value
    assert discount_data["amount_value"] == str(discount_amount.amount)


def test_update_order_discount_order_is_not_draft(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    draft_order_with_fixed_discount_order.status = OrderStatus.UNFULFILLED
    draft_order_with_fixed_discount_order.save()

    order_discount = draft_order_with_fixed_discount_order.discounts.get()

    value = Decimal("50")
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": value,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    errors = data["errors"]
    assert len(errors) == 1

    error = data["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name


@pytest.mark.parametrize(
    ("value", "value_type"),
    [
        (Decimal("2222222"), DiscountValueTypeEnum.FIXED.name),
        (Decimal("101"), DiscountValueTypeEnum.PERCENTAGE.name),
    ],
)
def test_update_order_discount_incorrect_values(
    value,
    value_type,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    order_discount = draft_order_with_fixed_discount_order.discounts.get()

    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
        "input": {
            "valueType": value_type,
            "value": value,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountUpdate"]

    errors = data["errors"]
    assert len(errors) == 1

    error = errors[0]
    assert error["field"] == "value"
    assert error["code"] == OrderErrorCode.INVALID.name


def test_update_order_discount_by_user_no_channel_access(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.UNCONFIRMED
    order.channel = channel_PLN
    order.save(update_fields=["status", "channel"])
    order_discount = draft_order_with_fixed_discount_order.discounts.get()

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
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_UPDATE, variables)

    # then
    assert_no_permission(response)


def test_update_percentage_order_discount_to_order_by_app(
    draft_order_with_fixed_discount_order,
    app_api_client,
    permission_manage_orders,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    order_discount = draft_order_with_fixed_discount_order.discounts.get()
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

    # when
    response = app_api_client.post_graphql(
        ORDER_DISCOUNT_UPDATE, variables, permissions=(permission_manage_orders,)
    )

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

    # Use `net` values in comparison due to that fixture have taxes included in
    # prices but after recalculation taxes are removed because in tests we
    # don't use any tax app.
    assert order.undiscounted_total.net == current_undiscounted_total.net
    assert expected_net_total == order.total.net

    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.value == value
    assert order_discount.value_type == DiscountValueType.PERCENTAGE
    discount_amount = current_undiscounted_total.net - expected_total.net
    assert order_discount.amount == discount_amount
    assert order_discount.reason == reason

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_UPDATED
    parameters = event.parameters
    discount_data = parameters.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == DiscountValueTypeEnum.PERCENTAGE.value
    assert discount_data["amount_value"] == str(discount_amount.amount)


ORDER_DISCOUNT_DELETE = """
mutation OrderDiscountDelete($discountId: ID!){
  orderDiscountDelete(discountId: $discountId){
    order{
      id
      discounts {
        id
      }
      total {
        net {
            amount
        }
        gross {
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


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_delete_order_discount_from_order(
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    order = draft_order_with_fixed_discount_order
    order.status = status
    order.save(update_fields=["status"])

    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    name = "discount translated"
    translated_name = "discount translated name"
    order_discount.name = name
    order_discount.translated_name = translated_name
    order_discount.save(update_fields=["name", "translated_name"])

    current_undiscounted_total = order.undiscounted_total

    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountDelete"]

    order.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 0

    assert order.undiscounted_total.net == current_undiscounted_total.net
    assert order.total.net == current_undiscounted_total.net

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_DELETED

    assert order.search_vector


def test_delete_order_discount_order_is_not_draft(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    draft_order_with_fixed_discount_order.status = OrderStatus.UNFULFILLED
    draft_order_with_fixed_discount_order.save()

    order_discount = draft_order_with_fixed_discount_order.discounts.get()

    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountDelete"]

    errors = data["errors"]
    assert len(errors) == 1

    assert draft_order_with_fixed_discount_order.discounts.get()

    error = data["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name


def test_delete_order_discount_from_order_by_user_no_channel_access(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.UNCONFIRMED
    order.channel = channel_PLN
    order.save(update_fields=["status", "channel"])

    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    name = "discount translated"
    translated_name = "discount translated name"
    order_discount.name = name
    order_discount.translated_name = translated_name
    order_discount.save(update_fields=["name", "translated_name"])

    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
    }
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)

    # then
    assert_no_permission(response)


def test_delete_order_discount_from_order_by_app(
    draft_order_with_fixed_discount_order,
    app_api_client,
    permission_manage_orders,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    order_discount = draft_order_with_fixed_discount_order.discounts.get()
    name = "discount translated"
    translated_name = "discount translated name"
    order_discount.name = name
    order_discount.translated_name = translated_name
    order_discount.save(update_fields=["name", "translated_name"])

    current_undiscounted_total = order.undiscounted_total

    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", order_discount.pk),
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_DISCOUNT_DELETE, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountDelete"]

    order.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 0

    assert order.undiscounted_total.net == current_undiscounted_total.net
    assert order.total.net == current_undiscounted_total.net

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_DISCOUNT_DELETED

    assert order.search_vector


def test_delete_manual_discount_from_order_with_subtotal_promotion(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
    order_promotion_rule,
):
    # given
    order = draft_order_with_fixed_discount_order
    manual_discount = draft_order_with_fixed_discount_order.discounts.get()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", manual_discount.pk),
    }

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderDiscountDelete"]
    assert not data["errors"]

    with pytest.raises(manual_discount._meta.model.DoesNotExist):
        manual_discount.refresh_from_db()

    order.refresh_from_db()
    order_discount = order.discounts.get()
    reward_value = order_promotion_rule.reward_value
    assert order_discount.value == reward_value
    assert order_discount.value_type == order_promotion_rule.reward_value_type

    undiscounted_subtotal = (
        order.undiscounted_total_net_amount - order.base_shipping_price_amount
    )
    assert order_discount.amount.amount == reward_value / 100 * undiscounted_subtotal
    assert (
        order.total_net_amount
        == order.undiscounted_total_net_amount - order_discount.amount.amount
    )


def test_delete_manual_discount_from_order_with_gift_promotion(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
    gift_promotion_rule,
):
    # given
    order = draft_order_with_fixed_discount_order
    manual_discount = draft_order_with_fixed_discount_order.discounts.get()
    assert order.lines.count() == 2

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", manual_discount.pk),
    }

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderDiscountDelete"]
    assert not data["errors"]

    with pytest.raises(manual_discount._meta.model.DoesNotExist):
        manual_discount.refresh_from_db()

    order.refresh_from_db()
    assert order.lines.count() == 3
    assert not order.discounts.exists()

    gift_line = order.lines.filter(is_gift=True).first()
    gift_discount = gift_line.discounts.get()
    gift_price = gift_line.variant.channel_listings.get(
        channel=order.channel
    ).price_amount

    assert gift_discount.value == gift_price
    assert gift_discount.amount.amount == gift_price
    assert gift_discount.value_type == DiscountValueType.FIXED

    assert order.total_net_amount == order.undiscounted_total_net_amount


def test_delete_manual_discount_from_order_with_entire_order_voucher(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
    voucher,
    plugins_manager,
):
    # given
    order = draft_order_with_fixed_discount_order
    currency = order.currency
    manual_discount = draft_order_with_fixed_discount_order.discounts.get()
    code = voucher.codes.first().code
    order.voucher_code = code
    order.voucher = voucher
    order.save(update_fields=["voucher_code", "voucher"])
    fetch_order_prices_if_expired(order, plugins_manager, None, True)
    assert order.discounts.get() == manual_discount
    voucher_discount_amount = voucher.channel_listings.get().discount
    undiscounted_total_net_amount = order.undiscounted_total_net_amount
    total_net_amount = undiscounted_total_net_amount - voucher_discount_amount.amount

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "discountId": graphene.Node.to_global_id("OrderDiscount", manual_discount.pk),
    }

    # when
    response = staff_api_client.post_graphql(ORDER_DISCOUNT_DELETE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderDiscountDelete"]
    assert not data["errors"]

    with pytest.raises(manual_discount._meta.model.DoesNotExist):
        manual_discount.refresh_from_db()

    voucher_discount = order.discounts.get()
    assert voucher_discount.type == DiscountType.VOUCHER
    assert voucher_discount.amount.amount == voucher_discount_amount.amount
    assert voucher_discount.reason == f"Voucher code: {code}"

    assert order.undiscounted_total_net_amount == undiscounted_total_net_amount
    assert (
        quantize_price(Decimal(data["order"]["total"]["net"]["amount"]), currency)
        == total_net_amount
    )


ORDER_LINE_DISCOUNT_UPDATE = """
mutation OrderLineDiscountUpdate($input: OrderDiscountCommonInput!, $orderLineId: ID!){
  orderLineDiscountUpdate(orderLineId: $orderLineId, input: $input){
    orderLine{
      unitPrice{
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


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_update_order_line_discount(
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = status
    order.save(update_fields=["status"])

    undiscounted_shipping_price = order.shipping_method.channel_listings.get(
        channel=order.channel
    ).price
    line_to_discount = order.lines.first()
    unit_price = Money(Decimal(7.3), currency="USD")
    line_to_discount.unit_price = TaxedMoney(unit_price, unit_price)
    line_to_discount.undiscounted_unit_price = line_to_discount.unit_price
    line_to_discount.undiscounted_base_unit_price = unit_price
    line_to_discount.base_unit_price = unit_price
    total_price = line_to_discount.unit_price * line_to_discount.quantity
    line_to_discount.total_price = total_price
    line_to_discount.undiscounted_total_price = total_price
    line_to_discount.save()

    line_to_discount.discounts.create(
        value_type="fixed",
        value=0,
        amount_value=0,
        name="Manual line discount",
        type="manual",
    )

    line_price_before_discount = line_to_discount.unit_price

    value = Decimal("5")
    value_type = DiscountValueTypeEnum.FIXED
    reason = "New reason for unit discount"
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.pk),
        "input": {
            "valueType": value_type.name,
            "value": value,
            "reason": reason,
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]

    line_to_discount.refresh_from_db()
    second_line = order.lines.last()
    order.refresh_from_db()

    order_discount = order.discounts.get()
    order_discount_amount = order_discount.amount
    discount_applied_to_lines = order_discount_amount - (
        undiscounted_shipping_price - order.shipping_price.gross
    )
    discount_applied_to_discounted_line = (
        discount_applied_to_lines
        - (second_line.base_unit_price - second_line.unit_price.gross)
        * second_line.quantity
    )
    assert discount_applied_to_discounted_line == quantize_price(
        (line_to_discount.base_unit_price - line_to_discount.unit_price.gross)
        * line_to_discount.quantity,
        order.currency,
    )

    errors = data["errors"]
    assert not errors

    discount = partial(
        fixed_discount,
        discount=Money(value, currency=order.currency),
    )
    expected_line_price = discount(line_price_before_discount)

    assert (
        line_to_discount.base_unit_price
        == quantize_price(expected_line_price, "USD").gross
    )
    unit_discount = line_to_discount.unit_discount
    assert unit_discount == (line_price_before_discount - expected_line_price).gross

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_UPDATED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_to_discount.refresh_from_db()
    assert line_to_discount.unit_discount_amount == value
    assert line_to_discount.unit_discount_type == DiscountValueType.FIXED

    line_data = lines[0]
    assert line_data.get("line_pk") == str(line_to_discount.pk)
    discount_data = line_data.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == value_type.value
    assert discount_data["amount_value"] == str(unit_discount.amount)

    line_discount = line_to_discount.discounts.get()
    assert line_discount.type == DiscountType.MANUAL
    assert line_discount.value == value
    assert line_discount.value_type == value_type.value
    assert line_discount.reason == reason
    assert line_discount.amount_value == value * line_to_discount.quantity


def test_update_order_line_discount_by_user_no_channel_access(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.channel = channel_PLN
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status", "channel"])
    line_to_discount = order.lines.first()

    value = Decimal("5")
    reason = "New reason for unit discount"
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": value,
            "reason": reason,
        },
    }
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)

    # then
    assert_no_permission(response)


def test_update_order_line_discount_by_app(
    draft_order_with_fixed_discount_order,
    app_api_client,
    permission_manage_orders,
    channel_PLN,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.channel = channel_PLN
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status", "channel"])
    line_to_discount = order.lines.first()

    value = Decimal("5")
    value_type = DiscountValueTypeEnum.FIXED
    reason = "New reason for unit discount"
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.pk),
        "input": {
            "valueType": value_type.name,
            "value": value,
            "reason": reason,
        },
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_LINE_DISCOUNT_UPDATE, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]

    line_to_discount.refresh_from_db()

    errors = data["errors"]
    assert not errors

    unit_discount = line_to_discount.unit_discount

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_UPDATED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == str(line_to_discount.pk)
    discount_data = line_data.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == value_type.value
    assert discount_data["amount_value"] == str(unit_discount.amount)

    line_discount = line_to_discount.discounts.get()
    assert line_discount.type == DiscountType.MANUAL
    assert line_discount.value == value
    assert line_discount.value_type == value_type.value
    assert line_discount.reason == reason
    assert line_discount.amount_value == value * line_to_discount.quantity


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
def test_update_order_line_discount_line_with_discount(
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = status
    order.save(update_fields=["status"])
    line_to_discount = order.lines.first()
    unit_price = quantize_price(Money(Decimal(7.3), currency="USD"), currency="USD")
    line_to_discount.base_unit_price = unit_price
    line_to_discount.unit_price = TaxedMoney(unit_price, unit_price)

    line_to_discount.unit_discount_amount = Decimal("2.500")
    line_to_discount.unit_discount_type = DiscountValueType.FIXED
    line_to_discount.unit_discount_value = Decimal("2.500")
    line_to_discount.undiscounted_unit_price_gross_amount = (
        line_to_discount.unit_price_gross_amount + line_to_discount.unit_discount_amount
    )
    line_to_discount.undiscounted_unit_price_net_amount = (
        line_to_discount.unit_price_net_amount + line_to_discount.unit_discount_amount
    )
    line_to_discount.undiscounted_total_price_gross_amount = (
        line_to_discount.undiscounted_unit_price_gross_amount
        * line_to_discount.quantity
    )
    line_to_discount.undiscounted_total_price_net_amount = (
        line_to_discount.undiscounted_unit_price_net_amount * line_to_discount.quantity
    )

    line_to_discount.undiscounted_base_unit_price_amount = (
        unit_price.amount + line_to_discount.unit_discount_amount
    )

    line_to_discount.save()

    line_discount_amount_before_update = line_to_discount.unit_discount_amount
    line_discount_value_before_update = line_to_discount.unit_discount_value

    line_undiscounted_price = line_to_discount.undiscounted_unit_price

    value = Decimal("50")
    value_type = DiscountValueTypeEnum.PERCENTAGE
    reason = "New reason for unit discount"
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.pk),
        "input": {
            "valueType": value_type.name,
            "value": value,
            "reason": reason,
        },
    }

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]

    line_to_discount.refresh_from_db()
    errors = data["errors"]
    assert not errors

    discount = partial(
        percentage_discount,
        percentage=value,
    )
    expected_line_price = discount(line_undiscounted_price)

    assert line_to_discount.base_unit_price == expected_line_price.gross
    unit_discount = line_to_discount.unit_discount
    assert unit_discount == (line_undiscounted_price - expected_line_price).gross

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_UPDATED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == str(line_to_discount.pk)
    discount_data = line_data.get("discount")

    assert discount_data["value"] == str(value)
    assert discount_data["value_type"] == value_type.value
    assert discount_data["amount_value"] == str(unit_discount.amount)

    assert discount_data["old_value"] == str(line_discount_value_before_update)
    assert discount_data["old_value_type"] == DiscountValueTypeEnum.FIXED.value
    assert discount_data["old_amount_value"] == str(line_discount_amount_before_update)

    line_discount = line_to_discount.discounts.get()
    assert line_discount.type == DiscountType.MANUAL
    assert line_discount.value == value
    assert line_discount.value_type == value_type.value
    assert line_discount.reason == reason
    assert (
        line_discount.amount_value
        == line_to_discount.unit_discount_amount * line_to_discount.quantity
    )


def test_update_order_line_discount_line_with_catalogue_promotion(
    order_with_lines_and_catalogue_promotion,
    staff_api_client,
    permission_group_manage_orders,
    tax_configuration_flat_rates,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines_and_catalogue_promotion
    currency = order.currency
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    line = order.lines.get(quantity=3)
    assert line.discounts.filter(type=DiscountType.PROMOTION).exists()
    unidscounted_unit_price = line.undiscounted_base_unit_price.amount
    tax_rate = Decimal("1.23")

    manual_discount_value = Decimal("5")
    value_type = DiscountValueTypeEnum.FIXED
    reason = "Manual fixed line discount"
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
        "input": {
            "valueType": value_type.name,
            "value": manual_discount_value,
            "reason": reason,
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]
    assert not data["errors"]
    line.refresh_from_db()

    line_discount = line.discounts.get()
    assert line_discount.type == DiscountType.MANUAL
    assert line_discount.value == manual_discount_value
    assert line_discount.value_type == value_type.value
    assert line_discount.reason == reason
    assert line_discount.amount_value == manual_discount_value * line.quantity

    line_unit_price = unidscounted_unit_price - manual_discount_value
    line_undiscounted_total_net_amount = quantize_price(
        unidscounted_unit_price * line.quantity,
        currency,
    )
    line_total_net_amount = quantize_price(
        line.base_unit_price_amount * line.quantity,
        currency,
    )
    assert line.undiscounted_unit_price_net_amount == unidscounted_unit_price
    assert line.undiscounted_unit_price_gross_amount == quantize_price(
        unidscounted_unit_price * tax_rate, currency
    )
    assert line.undiscounted_base_unit_price_amount == unidscounted_unit_price
    assert line.base_unit_price_amount == line_unit_price
    assert line.unit_price_net_amount == line_unit_price
    assert line.unit_price_gross_amount == quantize_price(
        line_unit_price * tax_rate, currency
    )
    assert line.total_price_net_amount == line_total_net_amount
    assert line.total_price_gross_amount == quantize_price(
        line_total_net_amount * tax_rate, currency
    )
    assert (
        line.undiscounted_total_price_net_amount == line_undiscounted_total_net_amount
    )
    assert line.undiscounted_total_price_gross_amount == quantize_price(
        line_undiscounted_total_net_amount * tax_rate, currency
    )


def test_update_order_line_discount_order_is_not_draft(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    draft_order_with_fixed_discount_order.status = OrderStatus.UNFULFILLED
    draft_order_with_fixed_discount_order.save()

    line_to_discount = draft_order_with_fixed_discount_order.lines.first()

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line_to_discount.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": Decimal("5"),
            "reason": "New reason for unit discount",
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]

    line_to_discount.refresh_from_db()

    errors = data["errors"]
    assert len(errors) == 1

    error = data["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name

    assert line_to_discount.unit_discount_amount == Decimal("0")


def test_add_manual_line_discount_order_with_voucher_specific_product(
    order_with_lines,
    voucher_specific_product_type,
    staff_api_client,
    permission_group_manage_orders,
    tax_configuration_flat_rates,
):
    """Manual line discount takes precedence over vouchers."""
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    voucher = voucher_specific_product_type
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    voucher_discount_value = Decimal("2")
    voucher_listing.discount_value = voucher_discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)

    # create voucher line discount
    create_or_update_voucher_discount_objects_for_order(order)

    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    manual_line_discount_value = Decimal("3")
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", discounted_line.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": manual_line_discount_value,
            "reason": "Manual line discount",
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLineDiscountUpdate"]
    assert not data["errors"]

    discounted_line.refresh_from_db()
    line_1.refresh_from_db()
    order.refresh_from_db()

    manual_discount_amount = manual_line_discount_value * discounted_line.quantity
    assert (
        order.total_net_amount
        == undiscounted_subtotal.amount + shipping_price.amount - manual_discount_amount
    )
    assert (
        order.total_gross_amount
        == (
            undiscounted_subtotal.amount
            + shipping_price.amount
            - manual_discount_amount
        )
        * tax_rate
    )
    assert (
        order.subtotal_net_amount
        == undiscounted_subtotal.amount - manual_discount_amount
    )
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - manual_discount_amount) * tax_rate
    )
    assert order.undiscounted_total_net == undiscounted_subtotal + shipping_price
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + shipping_price) * tax_rate
    )
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.base_shipping_price == shipping_price

    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount
        - manual_line_discount_value
    )
    assert (
        discounted_line.total_price_net_amount
        == discounted_line.unit_price_net_amount * discounted_line.quantity
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.unit_price_net_amount * discounted_line.quantity * tax_rate
    )
    assert (
        discounted_line.undiscounted_total_price_net_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * tax_rate
    )
    assert discounted_line.unit_discount_amount == manual_line_discount_value
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == "Manual line discount"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_net_amount
        == order.subtotal_net_amount - discounted_line.total_price_net_amount
    )
    assert (
        line_1.total_price_gross_amount
        == (order.subtotal_net_amount - discounted_line.total_price_net_amount)
        * tax_rate
    )
    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1


def test_add_manual_line_discount_order_with_voucher_apply_once_per_order(
    order_with_lines,
    voucher,
    staff_api_client,
    permission_group_manage_orders,
    tax_configuration_flat_rates,
):
    """Manual line discount takes precedence over vouchers."""
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    voucher_discount_value = Decimal("3")
    voucher_listing.discount_value = voucher_discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    lines = order.lines.all()
    discounted_line, line_1 = lines

    # create voucher line discount
    create_or_update_voucher_discount_objects_for_order(order)

    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    manual_line_discount_value = Decimal("3")
    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", discounted_line.pk),
        "input": {
            "valueType": DiscountValueTypeEnum.FIXED.name,
            "value": manual_line_discount_value,
            "reason": "Manual line discount",
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_UPDATE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderLineDiscountUpdate"]
    assert not data["errors"]

    discounted_line.refresh_from_db()
    line_1.refresh_from_db()
    order.refresh_from_db()

    manual_discount_amount = manual_line_discount_value * discounted_line.quantity
    assert (
        order.total_net_amount
        == undiscounted_subtotal.amount + shipping_price.amount - manual_discount_amount
    )
    assert (
        order.total_gross_amount
        == (
            undiscounted_subtotal.amount
            + shipping_price.amount
            - manual_discount_amount
        )
        * tax_rate
    )
    assert (
        order.subtotal_net_amount
        == undiscounted_subtotal.amount - manual_discount_amount
    )
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - manual_discount_amount) * tax_rate
    )
    assert order.undiscounted_total_net == undiscounted_subtotal + shipping_price
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + shipping_price) * tax_rate
    )
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.base_shipping_price == shipping_price

    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount
        - manual_line_discount_value
    )
    assert (
        discounted_line.total_price_net_amount
        == discounted_line.unit_price_net_amount * discounted_line.quantity
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.unit_price_net_amount * discounted_line.quantity * tax_rate
    )
    assert (
        discounted_line.undiscounted_total_price_net_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * tax_rate
    )
    assert discounted_line.unit_discount_amount == manual_line_discount_value
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == "Manual line discount"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_net_amount
        == order.subtotal_net_amount - discounted_line.total_price_net_amount
    )
    assert (
        line_1.total_price_gross_amount
        == (order.subtotal_net_amount - discounted_line.total_price_net_amount)
        * tax_rate
    )
    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1


ORDER_LINE_DISCOUNT_REMOVE = """
mutation OrderLineDiscountRemove($orderLineId: ID!){
  orderLineDiscountRemove(orderLineId: $orderLineId){
    orderLine{
      id
      totalPrice {
        net {
            amount
        }
        gross {
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


@pytest.mark.parametrize("status", [OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])
@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_unit")
@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_total")
def test_delete_discount_from_order_line(
    mocked_calculate_order_line_total,
    mocked_calculate_order_line_unit,
    status,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    order = draft_order_with_fixed_discount_order
    order.status = status
    order.save(update_fields=["status"])
    line = order.lines.first()

    line_undiscounted_price = TaxedMoney(
        line.undiscounted_base_unit_price, line.undiscounted_base_unit_price
    )
    line_undiscounted_total_price = line_undiscounted_price * line.quantity

    mocked_calculate_order_line_unit.return_value = OrderTaxedPricesData(
        undiscounted_price=line_undiscounted_price,
        price_with_discounts=line_undiscounted_price,
    )
    mocked_calculate_order_line_total.return_value = OrderTaxedPricesData(
        undiscounted_price=line_undiscounted_total_price,
        price_with_discounts=line_undiscounted_total_price,
    )

    line.unit_discount_amount = Decimal("2.5")
    line.unit_discount_type = DiscountValueType.FIXED
    line.unit_discount_value = Decimal("2.5")
    line.save()

    line.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=Decimal("2.5"),
        currency=order.currency,
    )

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]

    errors = data["errors"]
    assert len(errors) == 0

    line.refresh_from_db()

    assert line.unit_price == line_undiscounted_price
    assert line.total_price == line_undiscounted_total_price
    unit_discount = line.unit_discount
    currency = order.currency
    assert unit_discount == Money(Decimal(0), currency=currency)

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_REMOVED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == str(line.pk)

    assert not line.discounts.exists()


@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_unit")
@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_total")
def test_delete_discount_from_order_line_by_user_no_channel_access(
    mocked_calculate_order_line_total,
    mocked_calculate_order_line_unit,
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
):
    # given
    order = draft_order_with_fixed_discount_order
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order.channel = channel_PLN
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status", "channel"])
    line = order.lines.first()

    line_undiscounted_price = TaxedMoney(
        line.undiscounted_base_unit_price, line.undiscounted_base_unit_price
    )
    line_undiscounted_total_price = line_undiscounted_price * line.quantity

    mocked_calculate_order_line_unit.return_value = OrderTaxedPricesData(
        undiscounted_price=line_undiscounted_price,
        price_with_discounts=line_undiscounted_price,
    )
    mocked_calculate_order_line_total.return_value = OrderTaxedPricesData(
        undiscounted_price=line_undiscounted_total_price,
        price_with_discounts=line_undiscounted_total_price,
    )

    line.unit_discount_amount = Decimal("2.5")
    line.unit_discount_type = DiscountValueType.FIXED
    line.unit_discount_value = Decimal("2.5")
    line.save()

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_unit")
@patch("saleor.plugins.manager.PluginsManager.calculate_order_line_total")
def test_delete_discount_from_order_line_by_app(
    mocked_calculate_order_line_total,
    mocked_calculate_order_line_unit,
    draft_order_with_fixed_discount_order,
    app_api_client,
    permission_manage_orders,
    channel_PLN,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.channel = channel_PLN
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status", "channel"])
    line = order.lines.first()

    line_undiscounted_price = TaxedMoney(
        line.undiscounted_base_unit_price, line.undiscounted_base_unit_price
    )
    line_undiscounted_total_price = line_undiscounted_price * line.quantity

    mocked_calculate_order_line_unit.return_value = OrderTaxedPricesData(
        undiscounted_price=line_undiscounted_price,
        price_with_discounts=line_undiscounted_price,
    )
    mocked_calculate_order_line_total.return_value = OrderTaxedPricesData(
        undiscounted_price=line_undiscounted_total_price,
        price_with_discounts=line_undiscounted_total_price,
    )

    line.unit_discount_amount = Decimal("2.5")
    line.unit_discount_type = DiscountValueType.FIXED
    line.unit_discount_value = Decimal("2.5")
    line.save()

    line.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=Decimal("2.5"),
        currency=order.currency,
    )

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }

    # when
    response = app_api_client.post_graphql(
        ORDER_LINE_DISCOUNT_REMOVE, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]

    errors = data["errors"]
    assert len(errors) == 0

    line.refresh_from_db()

    assert line.unit_price == line_undiscounted_price
    assert line.total_price == line_undiscounted_total_price
    unit_discount = line.unit_discount
    currency = order.currency
    assert unit_discount == Money(Decimal(0), currency=currency)

    event = order.events.get()
    assert event.type == OrderEvents.ORDER_LINE_DISCOUNT_REMOVED
    parameters = event.parameters
    lines = parameters.get("lines", {})
    assert len(lines) == 1

    line_data = lines[0]
    assert line_data.get("line_pk") == str(line.pk)

    assert not line.discounts.exists()


def test_delete_order_line_discount_order_is_not_draft(
    draft_order_with_fixed_discount_order,
    staff_api_client,
    permission_group_manage_orders,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    draft_order_with_fixed_discount_order.status = OrderStatus.UNFULFILLED
    draft_order_with_fixed_discount_order.save()

    line = draft_order_with_fixed_discount_order.lines.first()

    line.unit_discount_amount = Decimal("2.5")
    line.unit_discount_type = DiscountValueType.FIXED
    line.unit_discount_value = Decimal("2.5")
    line.save()

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]

    errors = data["errors"]
    assert len(errors) == 1

    assert draft_order_with_fixed_discount_order.discounts.get()

    error = data["errors"][0]
    assert error["field"] == "orderId"
    assert error["code"] == OrderErrorCode.CANNOT_DISCOUNT.name

    assert line.unit_discount_amount == Decimal("2.5")


def test_delete_order_line_discount_line_with_catalogue_promotion(
    order_with_lines_and_catalogue_promotion,
    staff_api_client,
    permission_group_manage_orders,
):
    """Deleting the discount should restore undiscounted prices for the line."""
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines_and_catalogue_promotion
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    line = order.lines.get(quantity=3)

    manual_reward_value = Decimal(1)
    line.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_reward_value,
        amount_value=manual_reward_value * line.quantity,
        currency=order.currency,
        reason="Manual line discount",
    )

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]
    assert not data["errors"]
    line.refresh_from_db()
    assert not line.discounts.filter(type=DiscountType.PROMOTION).exists()
    assert line.unit_price_net_amount == line.undiscounted_unit_price_net_amount
    assert line.total_price_net_amount == line.undiscounted_total_price_net_amount


def test_delete_order_line_discount_with_line_level_voucher(
    order_with_lines,
    staff_api_client,
    permission_group_manage_orders,
    voucher_specific_product_type,
    tax_configuration_flat_rates,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    voucher = voucher_specific_product_type
    order = order_with_lines
    currency = order.currency
    line = order.lines.get(quantity=3)
    voucher.products.add(line.variant.product)
    order.status = OrderStatus.DRAFT
    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code
    order.save(update_fields=["status", "voucher", "voucher_code"])

    assert voucher.discount_value_type == DiscountValueType.PERCENTAGE
    line_undiscounted_total_price = line.undiscounted_total_price.net.amount
    voucher_discount_value = voucher.channel_listings.get().discount_value
    voucher_discount_amount = quantize_price(
        line_undiscounted_total_price * voucher_discount_value / 100, currency
    )

    manual_reward_value = Decimal(1)
    manual_line_discount = line.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_reward_value,
        amount_value=manual_reward_value * line.quantity,
        currency=order.currency,
        reason="Manual line discount",
    )

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }

    # when
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]
    assert not data["errors"]

    with pytest.raises(manual_line_discount._meta.model.DoesNotExist):
        manual_line_discount.refresh_from_db()

    voucher_discount = line.discounts.get()
    assert voucher_discount.type == DiscountType.VOUCHER
    assert voucher_discount.amount.amount == voucher_discount_amount
    assert voucher_discount.reason == f"Voucher code: {code}"

    order_line = data["orderLine"]
    assert (
        order_line["totalPrice"]["net"]["amount"]
        == line_undiscounted_total_price - voucher_discount_amount
    )


def test_delete_order_line_discount_with_line_level_voucher_deleted_in_meantime(
    order_with_lines,
    staff_api_client,
    permission_group_manage_orders,
    voucher_specific_product_type,
    tax_configuration_flat_rates,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    voucher = voucher_specific_product_type
    order = order_with_lines
    line = order.lines.get(quantity=3)
    voucher.products.add(line.variant.product)
    order.status = OrderStatus.DRAFT
    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code
    order.save(update_fields=["status", "voucher", "voucher_code"])

    assert voucher.discount_value_type == DiscountValueType.PERCENTAGE
    line_undiscounted_total_price = line.undiscounted_total_price.net.amount

    manual_reward_value = Decimal(1)
    manual_line_discount = line.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_reward_value,
        amount_value=manual_reward_value * line.quantity,
        currency=order.currency,
        reason="Manual line discount",
    )

    variables = {
        "orderLineId": graphene.Node.to_global_id("OrderLine", line.pk),
    }

    # when
    voucher.delete()
    response = staff_api_client.post_graphql(ORDER_LINE_DISCOUNT_REMOVE, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountRemove"]
    assert not data["errors"]

    with pytest.raises(manual_line_discount._meta.model.DoesNotExist):
        manual_line_discount.refresh_from_db()

    assert not line.discounts.first()

    order_line = data["orderLine"]
    assert order_line["totalPrice"]["net"]["amount"] == line_undiscounted_total_price
