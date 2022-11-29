from decimal import Decimal

import graphene
import pytest
from prices import TaxedMoney

from .....core.taxes import zero_money, zero_taxed_money
from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from ....tests.utils import get_graphql_content

ORDER_UPDATE_SHIPPING_QUERY = """
    mutation orderUpdateShipping($order: ID!, $shippingMethod: ID) {
        orderUpdateShipping(
                order: $order, input: {shippingMethod: $shippingMethod}) {
            errors {
                field
                code
                message
            }
            order {
                id
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


@pytest.mark.parametrize("status", [OrderStatus.UNCONFIRMED, OrderStatus.DRAFT])
def test_order_update_shipping(
    status,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.base_shipping_price = zero_money(order.currency)
    order.status = status
    order.save()
    assert order.shipping_method != shipping_method

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id

    order.refresh_from_db()
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    shipping_price = TaxedMoney(shipping_total, shipping_total)
    assert order.status == status
    assert order.shipping_method == shipping_method
    assert order.base_shipping_price == shipping_total
    assert order.shipping_price_net == shipping_price.net
    assert order.shipping_price_gross == shipping_price.gross
    assert order.shipping_tax_rate == Decimal("0.0")
    assert order.shipping_method_name == shipping_method.name

    shipping_tax_class = shipping_method.tax_class
    assert order.shipping_tax_rate is not None
    assert order.shipping_tax_class == shipping_tax_class
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )


@pytest.mark.parametrize("status", [OrderStatus.UNCONFIRMED, OrderStatus.DRAFT])
def test_order_update_shipping_no_shipping_method_channel_listings(
    status,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = status
    order.save()
    assert order.shipping_method != shipping_method
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    shipping_method.channel_listings.all().delete()
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert errors[0]["field"] == "shippingMethod"


def test_order_update_shipping_tax_included(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    address = order_with_lines.shipping_address
    address.country = "DE"
    address.save()

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.tax_calculation_strategy = "FLAT_RATES"
    tc.prices_entered_with_tax = True
    tc.save()
    shipping_method.tax_class.country_rates.get_or_create(country="DE", rate=19)

    # when
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id

    order.refresh_from_db()
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    shipping_price = TaxedMoney(
        shipping_total / Decimal("1.19"), shipping_total
    ).quantize()
    assert order.status == OrderStatus.UNCONFIRMED
    assert order.shipping_method == shipping_method
    assert order.base_shipping_price == shipping_total
    assert order.shipping_price_net == shipping_price.net
    assert order.shipping_price_gross == shipping_price.gross
    assert order.shipping_tax_rate == Decimal("0.19")
    assert order.shipping_method_name == shipping_method.name


def test_order_update_shipping_clear_shipping_method(
    staff_api_client, permission_manage_orders, order, staff_user, shipping_method
):
    order.shipping_method = shipping_method
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id,
    ).get_total()

    shipping_price = TaxedMoney(shipping_total, shipping_total)
    order.shipping_price = shipping_price
    order.shipping_method_name = "Example shipping"
    order.save()

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"order": order_id, "shippingMethod": None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id

    order.refresh_from_db()
    assert order.shipping_method is None
    assert order.base_shipping_price == zero_money(order.currency)
    assert order.shipping_price == zero_taxed_money(order.currency)
    assert order.shipping_method_name is None

    assert order.shipping_tax_class is None
    assert order.shipping_tax_class_metadata == {}
    assert order.shipping_tax_class_private_metadata == {}


def test_order_update_shipping_shipping_required(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"order": order_id, "shippingMethod": None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "shippingMethod"
    assert data["errors"][0]["message"] == (
        "Shipping method is required for this order."
    )


@pytest.mark.parametrize(
    "status",
    [
        OrderStatus.UNFULFILLED,
        OrderStatus.FULFILLED,
        OrderStatus.PARTIALLY_RETURNED,
        OrderStatus.RETURNED,
        OrderStatus.CANCELED,
    ],
)
def test_order_update_shipping_not_editable_order(
    status,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = status
    order.save()
    assert order.shipping_method != shipping_method
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == OrderErrorCode.NOT_EDITABLE.name


def test_order_update_shipping_no_shipping_address(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    order.shipping_address = None
    order.save()
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "order"
    assert data["errors"][0]["message"] == (
        "Cannot choose a shipping method for an order without" " the shipping address."
    )


def test_order_update_shipping_incorrect_shipping_method(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    zone = shipping_method.shipping_zone
    zone.countries = ["DE"]
    zone.save()
    assert order.shipping_address.country.code not in zone.countries
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "shippingMethod"
    assert data["errors"][0]["message"] == (
        "Shipping method cannot be used with this order."
    )


def test_order_update_shipping_shipping_zone_without_channels(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    order.channel.shipping_zones.clear()
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name


def test_order_update_shipping_excluded_shipping_method_postal_code(
    staff_api_client,
    permission_manage_orders,
    order_unconfirmed,
    staff_user,
    shipping_method_excluded_by_postal_code,
):
    order = order_unconfirmed
    order.shipping_method = shipping_method_excluded_by_postal_code
    shipping_total = shipping_method_excluded_by_postal_code.channel_listings.get(
        channel_id=order.channel_id,
    ).get_total()

    shipping_price = TaxedMoney(shipping_total, shipping_total)
    order.shipping_price = shipping_price
    order.shipping_method_name = "Example shipping"
    order.save()

    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method_excluded_by_postal_code.id
    )
    variables = {"order": order_id, "shippingMethod": method_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["errors"][0]["field"] == "shippingMethod"
    assert data["errors"][0]["message"] == (
        "Shipping method cannot be used with this order."
    )


def test_draft_order_clear_shipping_method(
    staff_api_client, draft_order, permission_manage_orders
):
    # given
    assert draft_order.shipping_method
    assert draft_order.base_shipping_price != zero_money(draft_order.currency)
    assert draft_order.shipping_price != zero_taxed_money(draft_order.currency)
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", draft_order.id)
    variables = {"order": order_id, "shippingMethod": None}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id

    draft_order.refresh_from_db()
    assert draft_order.shipping_method is None
    assert draft_order.base_shipping_price == zero_money(draft_order.currency)
    assert draft_order.shipping_price == zero_taxed_money(draft_order.currency)
    assert draft_order.shipping_method_name is None


ORDER_UPDATE_SHIPPING_QUERY_WITH_TOTAL = """
mutation OrderUpdateShipping(
    $orderId: ID!
    $shippingMethod: OrderUpdateShippingInput!
) {
    orderUpdateShipping(order: $orderId, input: $shippingMethod) {
        order {
            shippingMethod {
                id
            }
        }
        errors {
            field
            message
        }
    }
}
"""


@pytest.mark.parametrize(
    "input, response_msg",
    [
        ({"shippingMethod": ""}, "Shipping method cannot be empty."),
        ({}, "Shipping method must be provided to perform mutation."),
    ],
)
def test_order_shipping_update_mutation_return_error_for_empty_value(
    draft_order, permission_manage_orders, staff_api_client, input, response_msg
):
    query = ORDER_UPDATE_SHIPPING_QUERY_WITH_TOTAL

    order = draft_order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"orderId": order_id, "shippingMethod": input}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=(permission_manage_orders,),
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]

    assert data["errors"][0]["message"] == response_msg


def test_order_shipping_update_mutation_properly_recalculate_total(
    draft_order,
    permission_manage_orders,
    staff_api_client,
):
    query = ORDER_UPDATE_SHIPPING_QUERY_WITH_TOTAL

    order = draft_order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"orderId": order_id, "shippingMethod": {"shippingMethod": None}}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=(permission_manage_orders,),
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["shippingMethod"] is None
