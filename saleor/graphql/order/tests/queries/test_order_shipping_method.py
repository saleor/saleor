import pytest
from measurement.measures import Weight

from ....tests.utils import get_graphql_content

ORDERS_QUERY_SHIPPING_METHODS = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    availableShippingMethods {
                        name
                        price {
                            amount
                        }
                    }
                }
            }
        }
    }
"""


def test_order_query_without_available_shipping_methods(
    staff_api_client,
    permission_group_manage_orders,
    order,
    shipping_method_channel_PLN,
    channel_USD,
):
    order.channel = channel_USD
    order.shipping_method = shipping_method_channel_PLN
    order.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["availableShippingMethods"]) == 0


@pytest.mark.parametrize("minimum_order_weight_value", [0, 2, None])
def test_order_available_shipping_methods_with_weight_based_shipping_method(
    staff_api_client,
    order_line,
    shipping_method_weight_based,
    permission_group_manage_orders,
    minimum_order_weight_value,
):
    shipping_method = shipping_method_weight_based
    order = order_line.order
    if minimum_order_weight_value is not None:
        weight = Weight(kg=minimum_order_weight_value)
        shipping_method.minimum_order_weight = weight
        order.weight = weight
        order.save(update_fields=["weight"])
    else:
        shipping_method.minimum_order_weight = minimum_order_weight_value

    shipping_method.save(update_fields=["minimum_order_weight"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    shipping_methods = [
        method["name"] for method in order_data["availableShippingMethods"]
    ]
    assert shipping_method.name in shipping_methods


def test_order_available_shipping_methods_weight_method_with_higher_minimal_weigh(
    staff_api_client,
    order_line,
    shipping_method_weight_based,
    permission_group_manage_orders,
):
    order = order_line.order

    shipping_method = shipping_method_weight_based
    weight_value = 5
    shipping_method.minimum_order_weight = Weight(kg=weight_value)
    shipping_method.save(update_fields=["minimum_order_weight"])

    order.weight = Weight(kg=1)
    order.save(update_fields=["weight"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    shipping_methods = [
        method["name"] for method in order_data["availableShippingMethods"]
    ]
    assert shipping_method.name not in shipping_methods


def test_order_query_shipping_zones_with_available_shipping_methods(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    shipping_zone,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["availableShippingMethods"]) == 1


def test_order_query_shipping_zones_without_channel(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    shipping_zone,
    channel_USD,
):
    channel_USD.shipping_zones.clear()
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]

    assert len(order_data["availableShippingMethods"]) == 0


def test_order_query_shipping_methods_excluded_postal_codes(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines_channel_PLN,
    channel_PLN,
):
    order = order_with_lines_channel_PLN
    order.shipping_method.postal_code_rules.create(start="HB3", end="HB6")
    order.shipping_address.postal_code = "HB5"
    order.shipping_address.save(update_fields=["postal_code"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["availableShippingMethods"] == []


def test_order_available_shipping_methods_query(
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
    shipping_zone,
):
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_price = shipping_method.channel_listings.get(
        channel_id=fulfilled_order.channel_id
    ).price

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(ORDERS_QUERY_SHIPPING_METHODS)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    method = order_data["availableShippingMethods"][0]

    assert shipping_price.amount == method["price"]["amount"]
