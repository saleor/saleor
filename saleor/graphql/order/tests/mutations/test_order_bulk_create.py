import copy

import graphene
import pytest
from django.utils import timezone

from .....order import OrderStatus
from .....order.models import Order, OrderEvent, OrderLine
from ....core.enums import ErrorPolicyEnum
from ....tests.utils import get_graphql_content

ORDER_BULK_CREATE = """
    mutation OrderBulkCreate(
        $orders: [OrderBulkCreateInput!]!,
        $errorPolicy: ErrorPolicyEnum
    ) {
        orderBulkCreate(orders: $orders, errorPolicy: $errorPolicy) {
            count
            results {
                order {
                    id
                    discount {
                        amount
                    }
                    discountName
                    redirectUrl
                    lines {
                        productName
                        productSku
                        quantity
                        id
                    }
                    billingAddress{
                        city
                        streetAddress1
                        postalCode
                    }
                    events {
                        message
                    }
                    weight {
                        value
                    }
                    displayGrossPrices
                    fulfillments {
                        lines {
                            quantity
                            orderLine {
                                id
                            }
                        }
                    }
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    }
"""


@pytest.fixture
def order_bulk_input(
    app,
    channel_PLN,
    customer_user,
    default_tax_class,
    graphql_address_data,
    shipping_method_channel_PLN,
    variant,
    warehouse,
):
    shipping_method = shipping_method_channel_PLN
    user = {
        "id": graphene.Node.to_global_id("User", customer_user.id),
        "email": None,
    }
    delivery_method = {
        # "warehouseId": graphene.Node.to_global_id("Warehouse", warehouses[0].id),
        "shippingMethodId": graphene.Node.to_global_id(
            "ShippingMethod", shipping_method.id
        ),
        "shippingTaxClassId": graphene.Node.to_global_id(
            "TaxClass", default_tax_class.id
        ),
    }
    line = {
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.id),
        "createdAt": timezone.now(),
        "isShippingRequired": True,
        "isGiftCard": False,
        "quantity": 5,
        "quantityFulfilled": 0,
        "totalPrice": {
            "gross": 100,
            "net": 80,
        },
        "undiscountedTotalPrice": {
            "gross": 100,
            "net": 80,
        },
        "taxRate": 20,
        "taxClassId": graphene.Node.to_global_id("TaxClass", default_tax_class.id),
    }
    note = {
        "message": "Test message",
        "date": timezone.now(),
        "userId": graphene.Node.to_global_id("User", customer_user.id),
        # "appId": graphene.Node.to_global_id("App", app.id),
    }
    return {
        "channel": channel_PLN.slug,
        "createdAt": timezone.now(),
        "status": OrderStatus.DRAFT,
        "user": user,
        "billingAddress": graphql_address_data,
        "shippingAddress": graphql_address_data,
        "currency": "PLN",
        "languageCode": "PL",
        "deliveryMethod": delivery_method,
        "lines": [line],
        "notes": [note],
        "weight": "10.15",
    }


def test_order_bulk_create(
    staff_api_client,
    permission_manage_orders,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()
    order_lines_count = OrderLine.objects.count()
    order_events_count = OrderEvent.objects.count()

    order = order_bulk_input

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]
    order = data[0]["order"]
    assert order["lines"]
    assert order["events"][0]["message"] == "Test message"
    assert order["weight"]["value"] == 10.15
    assert order["displayGrossPrices"]

    assert Order.objects.count() == orders_count + 1
    assert OrderLine.objects.count() == order_lines_count + 1
    assert OrderEvent.objects.count() == order_events_count + 1


def test_order_bulk_create_multiple_orders(
    staff_api_client,
    permission_manage_orders,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()
    order_lines_count = OrderLine.objects.count()

    order_1 = order_bulk_input
    order_2 = order_bulk_input

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {"orders": [order_1, order_2]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 2
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]
    assert not data[1]["errors"]
    order_1 = data[0]["order"]
    order_2 = data[1]["order"]

    assert order_1["lines"]
    assert order_2["lines"]
    assert Order.objects.count() == orders_count + 2
    assert OrderLine.objects.count() == order_lines_count + 2


def test_order_bulk_create_reject_failed_rows(
    staff_api_client,
    permission_manage_orders,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()
    order_lines_count = OrderLine.objects.count()

    order_1 = order_bulk_input
    order_2 = copy.deepcopy(order_bulk_input)
    order_2["channel"] = "non-existing-channel"

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {
        "errorPolicy": ErrorPolicyEnum.REJECT_FAILED_ROWS.name,
        "orders": [order_1, order_2],
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]
    assert data[0]["order"]
    assert data[0]["order"]["lines"]

    assert not data[1]["order"]
    errors = data[1]["errors"]
    assert (
        errors[0]["message"] == "Channel instance with slug=non-existing-channel"
        " doesn't exist."
    )

    assert Order.objects.count() == orders_count + 1
    assert OrderLine.objects.count() == order_lines_count + 1


def test_order_bulk_create_ignore_failed(
    staff_api_client,
    permission_manage_orders,
    order_bulk_input,
    app,
):
    # given
    orders_count = Order.objects.count()
    order_lines_count = OrderLine.objects.count()
    order_events_count = OrderEvent.objects.count()

    order = order_bulk_input
    order["notes"][0]["appId"] = graphene.Node.to_global_id("App", app.id)

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
        "orders": [order],
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"][0]
    assert data["order"]
    assert data["order"]["lines"]
    assert data["order"]["events"]
    assert data["errors"][0]["message"] == "Note input contains both userId and appId."

    assert Order.objects.count() == orders_count + 1
    assert OrderLine.objects.count() == order_lines_count + 1
    assert OrderEvent.objects.count() == order_events_count + 1
