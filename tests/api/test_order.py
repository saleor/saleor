import uuid
from datetime import date, timedelta
from unittest.mock import ANY, MagicMock, Mock, call, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time
from prices import Money, TaxedMoney

from saleor.account.models import CustomerEvent
from saleor.core.permissions import OrderPermissions
from saleor.core.taxes import zero_taxed_money
from saleor.graphql.core.enums import ReportingPeriod
from saleor.graphql.order.mutations.orders import (
    clean_order_cancel,
    clean_order_capture,
    clean_refund_payment,
    try_payment_action,
)
from saleor.graphql.order.utils import validate_draft_order
from saleor.graphql.payment.types import PaymentChargeStatusEnum
from saleor.order import OrderStatus, events as order_events
from saleor.order.error_codes import OrderErrorCode
from saleor.order.models import Order, OrderEvent
from saleor.payment import ChargeStatus, CustomPaymentChoices, PaymentError
from saleor.payment.models import Payment
from saleor.plugins.manager import PluginsManager
from saleor.shipping.models import ShippingMethod
from saleor.warehouse.models import Allocation, Stock

from ..utils import get_available_quantity_for_stock
from .utils import assert_no_permission, get_graphql_content


@pytest.fixture
def orders_query_with_filter():
    query = """
      query ($filter: OrderFilterInput!, ) {
        orders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """
    return query


@pytest.fixture
def draft_orders_query_with_filter():
    query = """
      query ($filter: OrderDraftFilterInput!, ) {
        draftOrders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """
    return query


@pytest.fixture
def orders(customer_user):
    return Order.objects.bulk_create(
        [
            Order(user=customer_user, status=OrderStatus.CANCELED, token=uuid.uuid4()),
            Order(
                user=customer_user, status=OrderStatus.UNFULFILLED, token=uuid.uuid4()
            ),
            Order(
                user=customer_user,
                status=OrderStatus.PARTIALLY_FULFILLED,
                token=uuid.uuid4(),
            ),
            Order(user=customer_user, status=OrderStatus.FULFILLED, token=uuid.uuid4()),
            Order(user=customer_user, status=OrderStatus.DRAFT, token=uuid.uuid4()),
        ]
    )


def test_orderline_query(staff_api_client, permission_manage_orders, fulfilled_order):
    order = fulfilled_order
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        lines {
                            thumbnail(size: 540) {
                                url
                            }
                            variant {
                                id
                            }
                        }
                    }
                }
            }
        }
    """
    line = order.lines.first()
    line.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["lines"][0]["thumbnail"] is None
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)
    assert order_data["lines"][0]["variant"]["id"] == variant_id


def test_order_query(
    staff_api_client, permission_manage_orders, fulfilled_order, shipping_zone
):
    order = fulfilled_order
    query = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    number
                    canFinalize
                    status
                    statusDisplay
                    paymentStatus
                    paymentStatusDisplay
                    userEmail
                    isPaid
                    shippingPrice {
                        gross {
                            amount
                        }
                    }
                    lines {
                        id
                    }
                    fulfillments {
                        fulfillmentOrder
                    }
                    payments{
                        id
                    }
                    subtotal {
                        net {
                            amount
                        }
                    }
                    total {
                        net {
                            amount
                        }
                    }
                    availableShippingMethods {
                        id
                        price {
                            amount
                        }
                        minimumOrderPrice {
                            amount
                            currency
                        }
                        type
                    }
                }
            }
        }
    }
    """
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["number"] == str(order.pk)
    assert order_data["canFinalize"] is True
    assert order_data["status"] == order.status.upper()
    assert order_data["statusDisplay"] == order.get_status_display()
    payment_status = PaymentChargeStatusEnum.get(order.get_payment_status()).name
    assert order_data["paymentStatus"] == payment_status
    payment_status_display = order.get_payment_status_display()
    assert order_data["paymentStatusDisplay"] == payment_status_display
    assert order_data["isPaid"] == order.is_fully_paid()
    assert order_data["userEmail"] == order.user_email
    expected_price = Money(
        amount=str(order_data["shippingPrice"]["gross"]["amount"]), currency="USD"
    )
    assert expected_price == order.shipping_price.gross
    assert len(order_data["lines"]) == order.lines.count()
    fulfillment = order.fulfillments.first().fulfillment_order
    fulfillment_order = order_data["fulfillments"][0]["fulfillmentOrder"]
    assert fulfillment_order == fulfillment
    assert len(order_data["payments"]) == order.payments.count()

    expected_methods = ShippingMethod.objects.applicable_shipping_methods(
        price=order.get_subtotal().gross,
        weight=order.get_total_weight(),
        country_code=order.shipping_address.country.code,
    )
    assert len(order_data["availableShippingMethods"]) == (expected_methods.count())

    method = order_data["availableShippingMethods"][0]
    expected_method = expected_methods.first()
    assert float(expected_method.price.amount) == method["price"]["amount"]
    assert float(expected_method.minimum_order_price.amount) == (
        method["minimumOrderPrice"]["amount"]
    )
    assert expected_method.type.upper() == method["type"]


@pytest.mark.parametrize(
    "expected_price_type, expected_price, display_gross_prices",
    (("gross", 13, True), ("net", 10, False)),
)
def test_order_available_shipping_methods_query(
    expected_price_type,
    expected_price,
    display_gross_prices,
    monkeypatch,
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    shipping_zone,
    site_settings,
):
    query = """
    query OrdersQuery {
        orders(first: 1) {
            edges {
                node {
                    availableShippingMethods {
                        id
                        price {
                            amount
                        }
                        type
                    }
                }
            }
        }
    }
    """
    shipping_method = shipping_zone.shipping_methods.first()
    taxed_price = TaxedMoney(net=Money(10, "USD"), gross=Money(13, "USD"))
    apply_taxes_to_shipping_mock = Mock(return_value=taxed_price)
    monkeypatch.setattr(
        PluginsManager, "apply_taxes_to_shipping", apply_taxes_to_shipping_mock
    )
    site_settings.display_gross_prices = display_gross_prices
    site_settings.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    method = order_data["availableShippingMethods"][0]

    apply_taxes_to_shipping_mock.assert_called_once_with(shipping_method.price, ANY)
    assert expected_price == method["price"]["amount"]


def test_order_query_customer(api_client):
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    response = api_client.post_graphql(query)
    assert_no_permission(response)


def test_order_query_gift_cards(
    staff_api_client, permission_manage_orders, order_with_lines, gift_card
):
    query = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            giftCards {
                displayCode
                currentBalance {
                    amount
                }
            }
        }
    }
    """

    order_with_lines.gift_cards.add(gift_card)

    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    gift_card_data = content["data"]["order"]["giftCards"][0]

    assert gift_card.display_code == gift_card_data["displayCode"]
    assert (
        gift_card.current_balance.amount == gift_card_data["currentBalance"]["amount"]
    )


def test_order_query_draft_excluded(staff_api_client, permission_manage_orders, orders):
    query = """
    query OrdersQuery {
        orders(first: 10) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    edges = get_graphql_content(response)["data"]["orders"]["edges"]

    assert len(edges) == Order.objects.confirmed().count()


def test_draft_order_query(staff_api_client, permission_manage_orders, orders):
    query = """
    query DraftOrdersQuery {
        draftOrders(first: 10) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == Order.objects.drafts().count()


def test_nested_order_events_query(
    staff_api_client,
    permission_manage_orders,
    fulfilled_order,
    fulfillment,
    staff_user,
    warehouse,
):
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        events {
                            date
                            type
                            user {
                                email
                            }
                            message
                            email
                            emailType
                            amount
                            quantity
                            composedId
                            orderNumber
                            fulfilledItems {
                                quantity
                                orderLine {
                                    productName
                                    variantName
                                }
                            }
                            paymentId
                            paymentGateway
                            warehouse {
                                name
                            }
                        }
                    }
                }
            }
        }
    """

    event = order_events.fulfillment_fulfilled_items_event(
        order=fulfilled_order,
        user=staff_user,
        fulfillment_lines=fulfillment.lines.all(),
    )
    event.parameters.update(
        {
            "message": "Example note",
            "email_type": order_events.OrderEventsEmails.PAYMENT,
            "amount": "80.00",
            "quantity": "10",
            "composed_id": "10-10",
            "warehouse": warehouse.pk,
        }
    )
    event.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]
    assert data["message"] == event.parameters["message"]
    assert data["amount"] == float(event.parameters["amount"])
    assert data["emailType"] == "PAYMENT_CONFIRMATION"
    assert data["quantity"] == int(event.parameters["quantity"])
    assert data["composedId"] == event.parameters["composed_id"]
    assert data["user"]["email"] == staff_user.email
    assert data["type"] == "FULFILLMENT_FULFILLED_ITEMS"
    assert data["date"] == event.date.isoformat()
    assert data["orderNumber"] == str(fulfilled_order.pk)
    assert data["fulfilledItems"] == [
        {
            "quantity": line.quantity,
            "orderLine": {
                "productName": line.order_line.product_name,
                "variantName": line.order_line.variant_name,
            },
        }
        for line in fulfillment.lines.all()
    ]
    assert data["paymentId"] is None
    assert data["paymentGateway"] is None
    assert data["warehouse"]["name"] == warehouse.name


def test_payment_information_order_events_query(
    staff_api_client, permission_manage_orders, order, payment_dummy, staff_user
):
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        events {
                            type
                            user {
                                email
                            }
                            message
                            email
                            emailType
                            amount
                            quantity
                            composedId
                            orderNumber
                            lines {
                                quantity
                            }
                            paymentId
                            paymentGateway
                        }
                    }
                }
            }
        }
    """

    amount = order.total.gross.amount

    order_events.payment_captured_event(
        order=order, user=staff_user, amount=amount, payment=payment_dummy
    )

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    assert data["message"] is None
    assert Money(str(data["amount"]), "USD") == order.total.gross
    assert data["emailType"] is None
    assert data["quantity"] is None
    assert data["composedId"] is None
    assert data["lines"] is None
    assert data["user"]["email"] == staff_user.email
    assert data["type"] == "PAYMENT_CAPTURED"
    assert data["orderNumber"] == str(order.pk)
    assert data["paymentId"] == payment_dummy.token
    assert data["paymentGateway"] == payment_dummy.gateway


def test_non_staff_user_cannot_only_see_his_order(user_api_client, order):
    query = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            number
        }
    }
    """
    ID = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": ID}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_query_order_as_app(app_api_client, permission_manage_orders, order):
    query = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            token
        }
    }
    """
    ID = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": ID}
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    assert order_data["token"] == order.token


def test_draft_order_create(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
):
    variant_0 = variant
    query = """
    mutation draftCreate(
        $user: ID, $discount: Decimal, $lines: [OrderLineCreateInput],
        $shippingAddress: AddressInput, $shippingMethod: ID, $voucher: ID,
        $customerNote: String) {
            draftOrderCreate(
                input: {user: $user, discount: $discount,
                lines: $lines, shippingAddress: $shippingAddress,
                shippingMethod: $shippingMethod, voucher: $voucher,
                customerNote: $customerNote}) {
                    errors {
                        field
                        message
                    }
                    order {
                        discount {
                            amount
                        }
                        discountName
                        lines {
                            productName
                            productSku
                            quantity
                        }
                        status
                        voucher {
                            code
                        }
                        customerNote
                    }
                }
        }
    """

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "user": user_id,
        "discount": discount,
        "lines": variant_list,
        "shippingAddress": shipping_address,
        "shippingMethod": shipping_id,
        "voucher": voucher_id,
        "customerNote": customer_note,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note

    order = Order.objects.first()
    assert order.user == customer_user
    # billing address should be copied
    assert order.billing_address.pk != customer_user.default_billing_address.pk
    assert (
        order.billing_address.as_data()
        == customer_user.default_billing_address.as_data()
    )
    assert order.shipping_method == shipping_method
    assert order.shipping_address.first_name == graphql_address_data["firstName"]

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


def test_draft_order_update(
    staff_api_client, permission_manage_orders, order_with_lines, voucher
):
    order = order_with_lines
    assert not order.voucher
    assert not order.customer_note
    query = """
        mutation draftUpdate($id: ID!, $voucher: ID!, $customerNote: String) {
            draftOrderUpdate(id: $id,
                             input: {voucher: $voucher, customerNote: $customerNote}) {
                errors {
                    field
                    message
                }
                order {
                    userEmail
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    customer_note = "Test customer note"
    variables = {"id": order_id, "voucher": voucher_id, "customerNote": customer_note}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    order.refresh_from_db()
    assert order.voucher
    assert order.customer_note == customer_note


def test_draft_order_update_doing_nothing_generates_no_events(
    staff_api_client, permission_manage_orders, order_with_lines
):
    assert not OrderEvent.objects.exists()

    query = """
        mutation draftUpdate($id: ID!) {
            draftOrderUpdate(id: $id, input: {}) {
                errors {
                    field
                    message
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    response = staff_api_client.post_graphql(
        query, {"id": order_id}, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)

    # Ensure not event was created
    assert not OrderEvent.objects.exists()


def test_draft_order_delete(
    staff_api_client, permission_manage_orders, order_with_lines
):
    order = order_with_lines
    query = """
        mutation draftDelete($id: ID!) {
            draftOrderDelete(id: $id) {
                order {
                    id
                }
            }
        }
        """
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    with pytest.raises(order._meta.model.DoesNotExist):
        order.refresh_from_db()


ORDER_CAN_FINALIZE_QUERY = """
    query OrderQuery($id: ID!){
        order(id: $id){
            canFinalize
        }
    }
"""


def test_can_finalize_order(staff_api_client, permission_manage_orders, draft_order):
    order_id = graphene.Node.to_global_id("Order", draft_order.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_CAN_FINALIZE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["order"]["canFinalize"] is True


def test_can_finalize_order_no_order_lines(
    staff_api_client, permission_manage_orders, order
):
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(ORDER_CAN_FINALIZE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["order"]["canFinalize"] is False


def test_validate_draft_order(draft_order):
    # should not raise any errors
    assert validate_draft_order(draft_order, "US") is None


def test_validate_draft_order_wrong_shipping(draft_order):
    order = draft_order
    shipping_zone = order.shipping_method.shipping_zone
    shipping_zone.countries = ["DE"]
    shipping_zone.save()
    assert order.shipping_address.country.code not in shipping_zone.countries
    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US")
    msg = "Shipping method is not valid for chosen shipping address"
    assert e.value.error_dict["shipping"][0].message == msg


def test_validate_draft_order_no_order_lines(order):
    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US")
    msg = "Could not create order without any products."
    assert e.value.error_dict["lines"][0].message == msg


def test_validate_draft_order_non_existing_variant(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    variant.delete()
    line.refresh_from_db()
    assert line.variant is None

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US")
    msg = "Could not create orders with non-existing products."
    assert e.value.error_dict["lines"][0].message == msg


def test_validate_draft_order_out_of_stock_variant(draft_order):
    order = draft_order
    line = order.lines.first()
    variant = line.variant

    stock = variant.stocks.get()
    stock.quantity = 0
    stock.save(update_fields=["quantity"])

    with pytest.raises(ValidationError) as e:
        validate_draft_order(order, "US")
    msg = "Insufficient product stock: SKU_A"
    assert e.value.error_dict["lines"][0].message == msg


DRAFT_ORDER_COMPLETE_MUTATION = """
    mutation draftComplete($id: ID!) {
        draftOrderComplete(id: $id) {
            orderErrors {
                field
                code
            }
            order {
                status
            }
        }
    }
"""


def test_draft_order_complete(
    staff_api_client, permission_manage_orders, staff_user, draft_order,
):
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    draft_placed_event = OrderEvent.objects.get()

    for line in order:
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    assert draft_placed_event.user == staff_user
    assert draft_placed_event.type == order_events.OrderEvents.PLACED_FROM_DRAFT
    assert draft_placed_event.parameters == {}


def test_draft_order_complete_product_without_inventory_tracking(
    staff_api_client,
    permission_manage_orders,
    staff_user,
    draft_order_without_inventory_tracking,
):
    order = draft_order_without_inventory_tracking

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]

    assert not content["data"]["draftOrderComplete"]["orderErrors"]

    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    draft_placed_event = OrderEvent.objects.get()

    assert not Allocation.objects.filter(order_line__order=order).exists()

    assert draft_placed_event.user == staff_user
    assert draft_placed_event.type == order_events.OrderEvents.PLACED_FROM_DRAFT
    assert draft_placed_event.parameters == {}


def test_draft_order_complete_out_of_stock_variant(
    staff_api_client, permission_manage_orders, staff_user, draft_order
):
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    line_1, _ = order.lines.order_by("-quantity").all()
    stock_1 = Stock.objects.get(product_variant=line_1.variant)
    line_1.quantity = get_available_quantity_for_stock(stock_1) + 1
    line_1.save(update_fields=["quantity"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["orderErrors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.INSUFFICIENT_STOCK.name


def test_draft_order_complete_existing_user_email_updates_user_field(
    staff_api_client, draft_order, customer_user, permission_manage_orders
):
    order = draft_order
    order.user_email = customer_user.email
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert "errors" not in content
    order.refresh_from_db()
    assert order.user == customer_user


def test_draft_order_complete_anonymous_user_email_sets_user_field_null(
    staff_api_client, draft_order, permission_manage_orders
):
    order = draft_order
    order.user_email = "anonymous@example.com"
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert "errors" not in content
    order.refresh_from_db()
    assert order.user is None


def test_draft_order_complete_anonymous_user_no_email(
    staff_api_client, draft_order, permission_manage_orders
):
    order = draft_order
    order.user_email = ""
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    assert data["status"] == OrderStatus.UNFULFILLED.upper()


DRAFT_ORDER_LINES_CREATE_MUTATION = """
    mutation DraftOrderLinesCreate($orderId: ID!, $variantId: ID!, $quantity: Int!) {
        draftOrderLinesCreate(id: $orderId,
                input: [{variantId: $variantId, quantity: $quantity}]) {

            errors {
                field
                message
            }
            orderLines {
                id
                quantity
                productSku
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


def test_draft_order_lines_create(
    draft_order, permission_manage_orders, staff_api_client
):
    query = DRAFT_ORDER_LINES_CREATE_MUTATION
    order = draft_order
    line = order.lines.first()
    variant = line.variant
    old_quantity = line.quantity
    quantity = 1
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": quantity}

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderLinesCreate"]
    assert data["orderLines"][0]["productSku"] == variant.sku
    assert data["orderLines"][0]["quantity"] == old_quantity + quantity

    # mutation should fail when quantity is lower than 1
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderLinesCreate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"


def test_require_draft_order_when_creating_lines(
    order_with_lines, staff_api_client, permission_manage_orders
):
    query = DRAFT_ORDER_LINES_CREATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    variant = line.variant
    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {"orderId": order_id, "variantId": variant_id, "quantity": 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderLinesCreate"]
    assert data["errors"]


DRAFT_ORDER_LINE_UPDATE_MUTATION = """
    mutation DraftOrderLineUpdate($lineId: ID!, $quantity: Int!) {
        draftOrderLineUpdate(id: $lineId, input: {quantity: $quantity}) {
            errors {
                field
                message
            }
            orderLine {
                id
                quantity
            }
            order {
                total {
                    gross {
                        amount
                    }
                }
            }
        }
    }
"""


def test_draft_order_line_update(
    draft_order, permission_manage_orders, staff_api_client, staff_user
):
    query = DRAFT_ORDER_LINE_UPDATE_MUTATION
    order = draft_order
    line = order.lines.first()
    new_quantity = 1
    removed_quantity = 2
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": new_quantity}

    # Ensure the line has the expected quantity
    assert line.quantity == 3

    # No event should exist yet
    assert not OrderEvent.objects.exists()

    # mutation should fail without proper permissions
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    # assign permissions
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderLineUpdate"]
    assert data["orderLine"]["quantity"] == new_quantity

    removed_items_event = OrderEvent.objects.last()  # type: OrderEvent
    assert removed_items_event.type == order_events.OrderEvents.DRAFT_REMOVED_PRODUCTS
    assert removed_items_event.user == staff_user
    assert removed_items_event.parameters == {
        "lines": [{"quantity": removed_quantity, "line_pk": line.pk, "item": str(line)}]
    }

    # mutation should fail when quantity is lower than 1
    variables = {"lineId": line_id, "quantity": 0}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderLineUpdate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "quantity"


def test_require_draft_order_when_updating_lines(
    order_with_lines, staff_api_client, permission_manage_orders
):
    query = DRAFT_ORDER_LINE_UPDATE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"lineId": line_id, "quantity": 1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderLineUpdate"]
    assert data["errors"]


QUERY_GET_FIRST_EVENT = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        events {
                            lines {
                                quantity
                                orderLine {
                                    id
                                }
                            }
                        }
                    }
                }
            }
        }
    """


def test_retrieving_event_lines_with_deleted_line(
    staff_api_client, order_with_lines, staff_user, permission_manage_orders
):
    order = order_with_lines
    lines = order_with_lines.lines.all()
    quantities_per_lines = [(line.quantity, line) for line in lines]

    # Create the test event
    order_events.draft_order_added_products_event(
        order=order, user=staff_user, order_lines=quantities_per_lines
    )

    # Delete a line
    deleted_line = lines.first()
    deleted_line.delete()

    # Prepare the query
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # Send the query and retrieve the data
    content = get_graphql_content(staff_api_client.post_graphql(QUERY_GET_FIRST_EVENT))
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    # Check every line is returned and the one deleted is None
    assert len(data["lines"]) == len(quantities_per_lines)
    for expected_data, received_line in zip(quantities_per_lines, data["lines"]):
        quantity, line = expected_data

        if line is deleted_line:
            assert received_line["orderLine"] is None
        else:
            assert received_line["orderLine"] is not None
            assert received_line["orderLine"]["id"] == graphene.Node.to_global_id(
                "OrderLine", line.pk
            )

        assert received_line["quantity"] == quantity


def test_retrieving_event_lines_with_missing_line_pk_in_data(
    staff_api_client, order_with_lines, staff_user, permission_manage_orders
):
    order = order_with_lines
    line = order_with_lines.lines.first()
    quantities_per_lines = [(line.quantity, line)]

    # Create the test event
    event = order_events.draft_order_added_products_event(
        order=order, user=staff_user, order_lines=quantities_per_lines
    )
    del event.parameters["lines"][0]["line_pk"]
    event.save(update_fields=["parameters"])

    # Prepare the query
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # Send the query and retrieve the data
    content = get_graphql_content(staff_api_client.post_graphql(QUERY_GET_FIRST_EVENT))
    data = content["data"]["orders"]["edges"][0]["node"]["events"][0]

    # Check every line is returned and the one deleted is None
    received_line = data["lines"][0]
    assert len(data["lines"]) == 1
    assert received_line["quantity"] == line.quantity
    assert received_line["orderLine"] is None


DRAFT_ORDER_LINE_DELETE_MUTATION = """
    mutation DraftOrderLineDelete($id: ID!) {
        draftOrderLineDelete(id: $id) {
            errors {
                field
                message
            }
            orderLine {
                id
            }
            order {
                id
            }
        }
    }
"""


def test_draft_order_line_remove(
    draft_order, permission_manage_orders, staff_api_client
):
    query = DRAFT_ORDER_LINE_DELETE_MUTATION
    order = draft_order
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderLineDelete"]
    assert data["orderLine"]["id"] == line_id
    assert line not in order.lines.all()


def test_require_draft_order_when_removing_lines(
    staff_api_client, order_with_lines, permission_manage_orders
):
    query = DRAFT_ORDER_LINE_DELETE_MUTATION
    order = order_with_lines
    line = order.lines.first()
    line_id = graphene.Node.to_global_id("OrderLine", line.id)
    variables = {"id": line_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["draftOrderLineDelete"]
    assert data["errors"]


def test_order_update(
    staff_api_client, permission_manage_orders, order_with_lines, graphql_address_data
):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
        mutation orderUpdate(
        $id: ID!, $email: String, $address: AddressInput) {
            orderUpdate(
                id: $id, input: {
                    userEmail: $email,
                    shippingAddress: $address,
                    billingAddress: $address}) {
                errors {
                    field
                    message
                }
                order {
                    userEmail
                }
            }
        }
        """
    email = "not_default@example.com"
    assert not order.user_email == email
    assert not order.shipping_address.first_name == graphql_address_data["firstName"]
    assert not order.billing_address.last_name == graphql_address_data["lastName"]
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "email": email, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user is None
    assert order.status == OrderStatus.UNFULFILLED


def test_order_update_anonymous_user_no_user_email(
    staff_api_client, order_with_lines, permission_manage_orders, graphql_address_data
):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
            mutation orderUpdate(
            $id: ID!, $address: AddressInput) {
                orderUpdate(
                    id: $id, input: {
                        shippingAddress: $address,
                        billingAddress: $address}) {
                    errors {
                        field
                        message
                    }
                    order {
                        id
                    }
                }
            }
            """
    first_name = "Test fname"
    last_name = "Test lname"
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "address": graphql_address_data}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    get_graphql_content(response)
    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name != first_name
    assert order.billing_address.last_name != last_name
    assert order.status == OrderStatus.UNFULFILLED


def test_order_update_user_email_existing_user(
    staff_api_client,
    order_with_lines,
    customer_user,
    permission_manage_orders,
    graphql_address_data,
):
    order = order_with_lines
    order.user = None
    order.save()
    query = """
        mutation orderUpdate(
        $id: ID!, $email: String, $address: AddressInput) {
            orderUpdate(
                id: $id, input: {
                    userEmail: $email, shippingAddress: $address,
                    billingAddress: $address}) {
                errors {
                    field
                    message
                }
                order {
                    userEmail
                }
            }
        }
        """
    email = customer_user.email
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "address": graphql_address_data, "email": email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert not content["data"]["orderUpdate"]["errors"]
    data = content["data"]["orderUpdate"]["order"]
    assert data["userEmail"] == email

    order.refresh_from_db()
    order.shipping_address.refresh_from_db()
    order.billing_address.refresh_from_db()
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.billing_address.last_name == graphql_address_data["lastName"]
    assert order.user_email == email
    assert order.user == customer_user


ORDER_ADD_NOTE_MUTATION = """
    mutation addNote($id: ID!, $message: String!) {
        orderAddNote(order: $id, input: {message: $message}) {
            orderErrors {
                field
                message
                code
            }
            order {
                id
            }
            event {
                user {
                    email
                }
                message
            }
        }
    }
"""


def test_order_add_note_as_staff_user(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    """We are testing that adding a note to an order as a staff user is doing the
    expected behaviors."""
    order = order_with_lines
    assert not order.events.all()
    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}
    response = staff_api_client.post_graphql(
        ORDER_ADD_NOTE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderAddNote"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["message"] == message

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED

    # Ensure the correct order event was created
    event = order.events.get()
    assert event.type == order_events.OrderEvents.NOTE_ADDED
    assert event.user == staff_user
    assert event.parameters == {"message": message}

    # Ensure not customer events were created as it was a staff action
    assert not CustomerEvent.objects.exists()


@pytest.mark.parametrize("message", ("", "   ",))
def test_order_add_note_fail_on_empty_message(
    staff_api_client, permission_manage_orders, order_with_lines, message
):
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id, "message": message}
    response = staff_api_client.post_graphql(
        ORDER_ADD_NOTE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderAddNote"]
    assert data["orderErrors"][0]["field"] == "message"
    assert data["orderErrors"][0]["code"] == OrderErrorCode.REQUIRED.name


@patch("saleor.graphql.order.mutations.orders.cancel_order")
@patch("saleor.graphql.order.mutations.orders.clean_order_cancel")
def test_order_cancel(
    mock_clean_order_cancel,
    mock_cancel_order,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
):
    order = order_with_lines
    query = """
        mutation cancelOrder($id: ID!) {
            orderCancel(id: $id) {
                order {
                    status
                }
                orderErrors{
                    field
                    code
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["orderErrors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(order=order, user=staff_api_client.user)


def test_order_capture(
    staff_api_client, permission_manage_orders, payment_txn_preauth, staff_user
):
    order = payment_txn_preauth.order
    query = """
        mutation captureOrder($id: ID!, $amount: Decimal!) {
            orderCapture(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    paymentStatusDisplay
                    isPaid
                    totalCaptured {
                        amount
                    }
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_preauth.total)
    variables = {"id": order_id, "amount": amount}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCapture"]["order"]
    order.refresh_from_db()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"]
    assert data["totalCaptured"]["amount"] == float(amount)

    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_FULLY_PAID
    assert event_order_paid.user is None

    event_email_sent, event_captured = list(order.events.all())[-2:]
    assert event_email_sent.user is None
    assert event_email_sent.parameters == {
        "email": order.user_email,
        "email_type": order_events.OrderEventsEmails.PAYMENT,
    }
    assert event_captured.type == order_events.OrderEvents.PAYMENT_CAPTURED
    assert event_captured.user == staff_user
    assert event_captured.parameters == {
        "amount": str(amount),
        "payment_gateway": "mirumee.payments.dummy",
        "payment_id": "",
    }


def test_paid_order_mark_as_paid(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    order = payment_txn_preauth.order
    query = """
            mutation markPaid($id: ID!) {
                orderMarkAsPaid(id: $id) {
                    errors {
                        field
                        message
                    }
                    orderErrors {
                        field
                        message
                        code
                    }
                    order {
                        isPaid
                    }
                }
            }
        """
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderMarkAsPaid"]["errors"]
    msg = "Orders with payments can not be manually marked as paid."
    assert errors[0]["message"] == msg
    assert errors[0]["field"] == "payment"

    order_errors = content["data"]["orderMarkAsPaid"]["orderErrors"]
    assert order_errors[0]["code"] == OrderErrorCode.PAYMENT_ERROR.name


def test_order_mark_as_paid(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    order = order_with_lines
    query = """
            mutation markPaid($id: ID!) {
                orderMarkAsPaid(id: $id) {
                    errors {
                        field
                        message
                    }
                    order {
                        isPaid
                    }
                }
            }
        """
    assert not order.is_fully_paid()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderMarkAsPaid"]["order"]
    order.refresh_from_db()
    assert data["isPaid"] is True is order.is_fully_paid()

    event_order_paid = order.events.first()
    assert event_order_paid.type == order_events.OrderEvents.ORDER_MARKED_AS_PAID
    assert event_order_paid.user == staff_user


def test_order_mark_as_paid_no_billing_address(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    order = order_with_lines
    order_with_lines.billing_address = None
    order_with_lines.save()

    query = """
            mutation markPaid($id: ID!) {
                orderMarkAsPaid(id: $id) {
                    orderErrors {
                        code
                    }
                }
            }
        """
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderMarkAsPaid"]["orderErrors"]
    assert data[0]["code"] == OrderErrorCode.BILLING_ADDRESS_NOT_SET.name


ORDER_VOID = """
    mutation voidOrder($id: ID!) {
        orderVoid(id: $id) {
            order {
                paymentStatus
                paymentStatusDisplay
            }
            errors {
                field
                message
            }
            orderErrors {
                field
                message
                code
            }
        }
    }
"""


def test_order_void(
    staff_api_client, permission_manage_orders, payment_txn_preauth, staff_user
):
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderVoid"]["order"]
    assert data["paymentStatus"] == PaymentChargeStatusEnum.NOT_CHARGED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.NOT_CHARGED)
    assert data["paymentStatusDisplay"] == payment_status_display
    event_payment_voided = order.events.last()
    assert event_payment_voided.type == order_events.OrderEvents.PAYMENT_VOIDED
    assert event_payment_voided.user == staff_user


def test_order_void_payment_error(
    mock_get_manager, staff_api_client, permission_manage_orders, payment_txn_preauth
):
    msg = "Oops! Something went wrong."
    order = payment_txn_preauth.order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    mock_get_manager.void_payment.side_effect = ValueError(msg)
    response = staff_api_client.post_graphql(
        ORDER_VOID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderVoid"]["errors"]
    assert errors[0]["field"] == "payment"
    assert errors[0]["message"] == msg

    order_errors = content["data"]["orderVoid"]["orderErrors"]
    assert order_errors[0]["code"] == OrderErrorCode.PAYMENT_ERROR.name


def test_order_refund(staff_api_client, permission_manage_orders, payment_txn_captured):
    order = payment_txn_captured.order
    query = """
        mutation refundOrder($id: ID!, $amount: Decimal!) {
            orderRefund(id: $id, amount: $amount) {
                order {
                    paymentStatus
                    paymentStatusDisplay
                    isPaid
                    status
                }
            }
        }
    """
    order_id = graphene.Node.to_global_id("Order", order.id)
    amount = float(payment_txn_captured.total)
    variables = {"id": order_id, "amount": amount}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderRefund"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_REFUNDED.name
    payment_status_display = dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_REFUNDED)
    assert data["paymentStatusDisplay"] == payment_status_display
    assert data["isPaid"] is False

    order_event = order.events.last()
    assert order_event.parameters["amount"] == str(amount)
    assert order_event.type == order_events.OrderEvents.PAYMENT_REFUNDED


@pytest.mark.parametrize(
    "requires_amount, mutation_name",
    ((True, "orderRefund"), (False, "orderVoid"), (True, "orderCapture")),
)
def test_clean_payment_without_payment_associated_to_order(
    staff_api_client, permission_manage_orders, order, requires_amount, mutation_name
):

    assert not OrderEvent.objects.exists()

    additional_arguments = ", amount: 2" if requires_amount else ""
    query = """
        mutation %(mutationName)s($id: ID!) {
          %(mutationName)s(id: $id %(args)s) {
            errors {
              field
              message
            }
          }
        }
    """ % {
        "mutationName": mutation_name,
        "args": additional_arguments,
    }

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    errors = get_graphql_content(response)["data"][mutation_name].get("errors")

    message = "There's no payment associated with the order."

    assert errors, "expected an error"
    assert errors == [{"field": "payment", "message": message}]
    assert not OrderEvent.objects.exists()


def test_try_payment_action_generates_event(order, staff_user, payment_dummy):
    message = "The payment did a oopsie!"
    assert not OrderEvent.objects.exists()

    def _test_operation():
        raise PaymentError(message)

    with pytest.raises(ValidationError) as exc:
        try_payment_action(
            order=order, user=staff_user, payment=payment_dummy, func=_test_operation
        )

    assert exc.value.args[0]["payment"].message == message

    error_event = OrderEvent.objects.get()  # type: OrderEvent
    assert error_event.type == order_events.OrderEvents.PAYMENT_FAILED
    assert error_event.user == staff_user
    assert error_event.parameters == {
        "message": message,
        "gateway": payment_dummy.gateway,
        "payment_id": payment_dummy.token,
    }


def test_clean_order_refund_payment():
    payment = MagicMock(spec=Payment)
    payment.gateway = CustomPaymentChoices.MANUAL
    Mock(spec="string")
    with pytest.raises(ValidationError) as e:
        clean_refund_payment(payment)
    msg = "Manual payments can not be refunded."
    assert e.value.error_dict["payment"][0].message == msg


def test_clean_order_capture():
    with pytest.raises(ValidationError) as e:
        clean_order_capture(None)
    msg = "There's no payment associated with the order."
    assert e.value.error_dict["payment"][0].message == msg


def test_clean_order_cancel(fulfilled_order_with_all_cancelled_fulfillments):
    order = fulfilled_order_with_all_cancelled_fulfillments
    # Shouldn't raise any errors
    assert clean_order_cancel(order) is None


def test_clean_order_cancel_draft_order(
    fulfilled_order_with_all_cancelled_fulfillments,
):
    order = fulfilled_order_with_all_cancelled_fulfillments

    order.status = OrderStatus.DRAFT
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER


def test_clean_order_cancel_canceled_order(
    fulfilled_order_with_all_cancelled_fulfillments,
):
    order = fulfilled_order_with_all_cancelled_fulfillments

    order.status = OrderStatus.CANCELED
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER


def test_clean_order_cancel_order_with_fulfillment(
    fulfilled_order_with_cancelled_fulfillment,
):
    order = fulfilled_order_with_cancelled_fulfillment

    order.status = OrderStatus.CANCELED
    order.save()

    with pytest.raises(ValidationError) as e:
        clean_order_cancel(order)
    assert e.value.error_dict["order"][0].code == OrderErrorCode.CANNOT_CANCEL_ORDER


ORDER_UPDATE_SHIPPING_QUERY = """
    mutation orderUpdateShipping($order: ID!, $shippingMethod: ID) {
        orderUpdateShipping(
                order: $order, input: {shippingMethod: $shippingMethod}) {
            errors {
                field
                message
            }
            order {
                id
            }
        }
    }
"""


def test_order_update_shipping(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
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
    shipping_total = shipping_method.get_total()
    shipping_price = TaxedMoney(shipping_total, shipping_total)
    assert order.status == OrderStatus.UNFULFILLED
    assert order.shipping_method == shipping_method
    assert order.shipping_price_net == shipping_price.net
    assert order.shipping_price_gross == shipping_price.gross
    assert order.shipping_method_name == shipping_method.name


def test_order_update_shipping_clear_shipping_method(
    staff_api_client, permission_manage_orders, order, staff_user, shipping_method
):
    order.shipping_method = shipping_method
    shipping_total = shipping_method.get_total()
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
    assert order.shipping_price == zero_taxed_money()
    assert order.shipping_method_name is None


def test_order_update_shipping_shipping_required(
    staff_api_client, permission_manage_orders, order_with_lines, staff_user
):
    order = order_with_lines
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


def test_order_update_shipping_no_shipping_address(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    shipping_method,
    staff_user,
):
    order = order_with_lines
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


def test_draft_order_clear_shipping_method(
    staff_api_client, draft_order, permission_manage_orders
):
    assert draft_order.shipping_method
    query = ORDER_UPDATE_SHIPPING_QUERY
    order_id = graphene.Node.to_global_id("Order", draft_order.id)
    variables = {"order": order_id, "shippingMethod": None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    assert data["order"]["id"] == order_id
    draft_order.refresh_from_db()
    assert draft_order.shipping_method is None
    assert draft_order.shipping_price == zero_taxed_money()
    assert draft_order.shipping_method_name is None


def test_orders_total(staff_api_client, permission_manage_orders, order_with_lines):
    query = """
    query Orders($period: ReportingPeriod) {
        ordersTotal(period: $period) {
            gross {
                amount
                currency
            }
            net {
                currency
                amount
            }
        }
    }
    """
    variables = {"period": ReportingPeriod.TODAY.name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, "USD") == order_with_lines.total.gross


def test_order_by_token_query(api_client, order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            id
        }
    }
    """
    order_id = graphene.Node.to_global_id("Order", order.id)
    response = api_client.post_graphql(query, {"token": order.token})
    content = get_graphql_content(response)
    assert content["data"]["orderByToken"]["id"] == order_id


def test_order_by_token_user_restriction(api_client, order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            user {
                id
            }
        }
    }
    """
    response = api_client.post_graphql(query, {"token": order.token})
    assert_no_permission(response)


def test_order_by_token_events_restriction(api_client, order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            events {
                id
            }
        }
    }
    """
    response = api_client.post_graphql(query, {"token": order.token})
    assert_no_permission(response)


def test_authorized_access_to_order_by_token(
    user_api_client, staff_api_client, customer_user, order, permission_manage_users
):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            user {
                id
            }
        }
    }
    """
    variables = {"token": order.token}
    customer_user_id = graphene.Node.to_global_id("User", customer_user.id)

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["orderByToken"]["user"]["id"] == customer_user_id

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    assert content["data"]["orderByToken"]["user"]["id"] == customer_user_id


def test_query_draft_order_by_token_with_requester_as_customer(
    user_api_client, draft_order
):
    draft_order.user = user_api_client.user
    draft_order.save(update_fields=["user"])
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            id
        }
    }
    """
    response = user_api_client.post_graphql(query, {"token": draft_order.token})
    content = get_graphql_content(response)
    assert not content["data"]["orderByToken"]


def test_query_draft_order_by_token_as_anonymous_customer(api_client, draft_order):
    query = """
    query OrderByToken($token: UUID!) {
        orderByToken(token: $token) {
            id
        }
    }
    """
    response = api_client.post_graphql(query, {"token": draft_order.token})
    content = get_graphql_content(response)
    assert not content["data"]["orderByToken"]


@patch("saleor.graphql.order.bulk_mutations.orders.cancel_order")
def test_order_bulk_cancel(
    mock_cancel_order,
    staff_api_client,
    order_list,
    fulfilled_order_with_all_cancelled_fulfillments,
    permission_manage_orders,
    address,
):
    query = """
        mutation CancelManyOrders($ids: [ID]!) {
            orderBulkCancel(ids: $ids) {
                count
                orderErrors{
                    field
                    code
                }
            }
        }
    """
    orders = order_list
    orders.append(fulfilled_order_with_all_cancelled_fulfillments)
    expected_count = sum(order.can_cancel() for order in orders)
    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in orders],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderBulkCancel"]
    assert data["count"] == expected_count
    assert not data["orderErrors"]

    calls = [call(order=order, user=staff_api_client.user) for order in orders]

    mock_cancel_order.assert_has_calls(calls, any_order=True)
    mock_cancel_order.call_count == expected_count


@pytest.mark.parametrize(
    "orders_filter, count",
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            1,
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"lte": str(date.today())}}, 2),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, 0),
    ],
)
def test_order_query_with_filter_created(
    orders_filter,
    count,
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
):
    Order.objects.create()
    with freeze_time("2012-01-14"):
        Order.objects.create()
    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "orders_filter, count, payment_status",
    [
        ({"paymentStatus": "FULLY_CHARGED"}, 1, ChargeStatus.FULLY_CHARGED),
        ({"paymentStatus": "NOT_CHARGED"}, 2, ChargeStatus.NOT_CHARGED),
        ({"paymentStatus": "PARTIALLY_CHARGED"}, 1, ChargeStatus.PARTIALLY_CHARGED),
        ({"paymentStatus": "PARTIALLY_REFUNDED"}, 1, ChargeStatus.PARTIALLY_REFUNDED),
        ({"paymentStatus": "FULLY_REFUNDED"}, 1, ChargeStatus.FULLY_REFUNDED),
        ({"paymentStatus": "FULLY_CHARGED"}, 0, ChargeStatus.FULLY_REFUNDED),
        ({"paymentStatus": "NOT_CHARGED"}, 1, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_order_query_with_filter_payment_status(
    orders_filter,
    count,
    payment_status,
    orders_query_with_filter,
    staff_api_client,
    payment_dummy,
    permission_manage_orders,
):
    payment_dummy.charge_status = payment_status
    payment_dummy.save()

    payment_dummy.id = None
    payment_dummy.order = Order.objects.create()
    payment_dummy.charge_status = ChargeStatus.NOT_CHARGED
    payment_dummy.save()

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "orders_filter, count, status",
    [
        ({"status": "UNFULFILLED"}, 2, OrderStatus.UNFULFILLED),
        ({"status": "PARTIALLY_FULFILLED"}, 1, OrderStatus.PARTIALLY_FULFILLED),
        ({"status": "FULFILLED"}, 1, OrderStatus.FULFILLED),
        ({"status": "CANCELED"}, 1, OrderStatus.CANCELED),
    ],
)
def test_order_query_with_filter_status(
    orders_filter,
    count,
    status,
    orders_query_with_filter,
    staff_api_client,
    payment_dummy,
    permission_manage_orders,
    order,
):
    order.status = status
    order.save()

    Order.objects.create()

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    orders_ids_from_response = [o["node"]["id"] for o in orders]
    assert len(orders) == count
    assert order_id in orders_ids_from_response


@pytest.mark.parametrize(
    "orders_filter, user_field, user_value",
    [
        ({"customer": "admin"}, "email", "admin@example.com"),
        ({"customer": "John"}, "first_name", "johnny"),
        ({"customer": "Snow"}, "last_name", "snow"),
    ],
)
def test_order_query_with_filter_customer_fields(
    orders_filter,
    user_field,
    user_value,
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(user=customer_user, token=str(uuid.uuid4()))
    Order.objects.bulk_create([order, Order(token=str(uuid.uuid4()))])

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    assert len(orders) == 1
    assert orders[0]["node"]["id"] == order_id


@pytest.mark.parametrize(
    "orders_filter, user_field, user_value",
    [
        ({"customer": "admin"}, "email", "admin@example.com"),
        ({"customer": "John"}, "first_name", "johnny"),
        ({"customer": "Snow"}, "last_name", "snow"),
    ],
)
def test_draft_order_query_with_filter_customer_fields(
    orders_filter,
    user_field,
    user_value,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(status=OrderStatus.DRAFT, user=customer_user, token=str(uuid.uuid4()))
    Order.objects.bulk_create(
        [order, Order(token=str(uuid.uuid4()), status=OrderStatus.DRAFT)]
    )

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    assert len(orders) == 1
    assert orders[0]["node"]["id"] == order_id


@pytest.mark.parametrize(
    "orders_filter, count",
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            1,
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"lte": str(date.today())}}, 2),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, 0),
    ],
)
def test_draft_order_query_with_filter_created_(
    orders_filter,
    count,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
):
    Order.objects.create(status=OrderStatus.DRAFT)
    with freeze_time("2012-01-14"):
        Order.objects.create(status=OrderStatus.DRAFT)
    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]

    assert len(orders) == count


QUERY_ORDER_WITH_SORT = """
    query ($sort_by: OrderSortingInput!) {
        orders(first:5, sortBy: $sort_by) {
            edges{
                node{
                    number
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "order_sort, result_order",
    [
        ({"field": "NUMBER", "direction": "ASC"}, [0, 1, 2]),
        ({"field": "NUMBER", "direction": "DESC"}, [2, 1, 0]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, [1, 0, 2]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "ASC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "DESC"}, [1, 0, 2]),
        ({"field": "FULFILLMENT_STATUS", "direction": "ASC"}, [2, 1, 0]),
        ({"field": "FULFILLMENT_STATUS", "direction": "DESC"}, [0, 1, 2]),
        ({"field": "TOTAL", "direction": "ASC"}, [0, 2, 1]),
        ({"field": "TOTAL", "direction": "DESC"}, [1, 2, 0]),
    ],
)
def test_query_orders_with_sort(
    order_sort, result_order, staff_api_client, permission_manage_orders, address
):
    created_orders = []
    with freeze_time("2017-01-14"):
        created_orders.append(
            Order.objects.create(
                token=str(uuid.uuid4()),
                billing_address=address,
                status=OrderStatus.PARTIALLY_FULFILLED,
                total=TaxedMoney(net=Money(10, "USD"), gross=Money(13, "USD")),
            )
        )
    with freeze_time("2012-01-14"):
        address2 = address.get_copy()
        address2.first_name = "Walter"
        address2.save()
        created_orders.append(
            Order.objects.create(
                token=str(uuid.uuid4()),
                billing_address=address2,
                status=OrderStatus.FULFILLED,
                total=TaxedMoney(net=Money(100, "USD"), gross=Money(130, "USD")),
            )
        )
    address3 = address.get_copy()
    address3.last_name = "Alice"
    address3.save()
    created_orders.append(
        Order.objects.create(
            token=str(uuid.uuid4()),
            billing_address=address3,
            status=OrderStatus.CANCELED,
            total=TaxedMoney(net=Money(20, "USD"), gross=Money(26, "USD")),
        )
    )
    variables = {"sort_by": order_sort}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDER_WITH_SORT, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    for order, order_number in enumerate(result_order):
        assert orders[order]["node"]["number"] == str(created_orders[order_number].pk)


QUERY_DRAFT_ORDER_WITH_SORT = """
    query ($sort_by: OrderSortingInput!) {
        draftOrders(first:5, sortBy: $sort_by) {
            edges{
                node{
                    number
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "draft_order_sort, result_order",
    [
        ({"field": "NUMBER", "direction": "ASC"}, [0, 1, 2]),
        ({"field": "NUMBER", "direction": "DESC"}, [2, 1, 0]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, [1, 0, 2]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "ASC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "DESC"}, [1, 0, 2]),
        ({"field": "TOTAL", "direction": "ASC"}, [0, 2, 1]),
        ({"field": "TOTAL", "direction": "DESC"}, [1, 2, 0]),
    ],
)
def test_query_draft_orders_with_sort(
    draft_order_sort, result_order, staff_api_client, permission_manage_orders, address
):
    created_orders = []
    with freeze_time("2017-01-14"):
        created_orders.append(
            Order.objects.create(
                token=str(uuid.uuid4()),
                billing_address=address,
                status=OrderStatus.DRAFT,
                total=TaxedMoney(net=Money(10, "USD"), gross=Money(13, "USD")),
            )
        )
    with freeze_time("2012-01-14"):
        address2 = address.get_copy()
        address2.first_name = "Walter"
        address2.save()
        created_orders.append(
            Order.objects.create(
                token=str(uuid.uuid4()),
                billing_address=address2,
                status=OrderStatus.DRAFT,
                total=TaxedMoney(net=Money(100, "USD"), gross=Money(130, "USD")),
            )
        )
    address3 = address.get_copy()
    address3.last_name = "Alice"
    address3.save()
    created_orders.append(
        Order.objects.create(
            token=str(uuid.uuid4()),
            billing_address=address3,
            status=OrderStatus.DRAFT,
            total=TaxedMoney(net=Money(20, "USD"), gross=Money(26, "USD")),
        )
    )
    variables = {"sort_by": draft_order_sort}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_DRAFT_ORDER_WITH_SORT, variables)
    content = get_graphql_content(response)
    draft_orders = content["data"]["draftOrders"]["edges"]

    for order, order_number in enumerate(result_order):
        assert draft_orders[order]["node"]["number"] == str(
            created_orders[order_number].pk
        )


@pytest.mark.parametrize(
    "orders_filter, count",
    [
        ({"search": "test_discount"}, 2),
        ({"search": "test_discount1"}, 1),
        ({"search": "translated_discount1_name"}, 1),
        ({"search": "user"}, 2),
        ({"search": "user1@example.com"}, 1),
        ({"search": "test@example.com"}, 1),
        ({"search": "Leslie"}, 1),
        ({"search": "Wade"}, 1),
        ({"search": ""}, 3),
    ],
)
def test_orders_query_with_filter_search(
    orders_filter,
    count,
    orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
):
    Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                token=str(uuid.uuid4()),
                discount_name="test_discount1",
                user_email="test@example.com",
                translated_discount_name="translated_discount1_name",
            ),
            Order(token=str(uuid.uuid4()), user_email="user1@example.com"),
            Order(
                token=str(uuid.uuid4()),
                user_email="user2@example.com",
                discount_name="test_discount2",
                translated_discount_name="translated_discount2_name",
            ),
        ]
    )
    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == count


def test_orders_query_with_filter_search_by_id(
    orders_query_with_filter, order, staff_api_client, permission_manage_orders
):
    variables = {"filter": {"search": order.pk}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


@pytest.mark.parametrize(
    "draft_orders_filter, count",
    [
        ({"search": "test_discount"}, 2),
        ({"search": "test_discount1"}, 1),
        ({"search": "translated_discount1_name"}, 1),
        ({"search": "user"}, 2),
        ({"search": "user1@example.com"}, 1),
        ({"search": "test@example.com"}, 1),
        ({"search": "Leslie"}, 1),
        ({"search": "Wade"}, 1),
        ({"search": ""}, 3),
    ],
)
def test_draft_orders_query_with_filter_search(
    draft_orders_filter,
    count,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
):
    Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                token=str(uuid.uuid4()),
                discount_name="test_discount1",
                user_email="test@example.com",
                translated_discount_name="translated_discount1_name",
                status=OrderStatus.DRAFT,
            ),
            Order(
                token=str(uuid.uuid4()),
                user_email="user1@example.com",
                status=OrderStatus.DRAFT,
            ),
            Order(
                token=str(uuid.uuid4()),
                user_email="user2@example.com",
                discount_name="test_discount2",
                translated_discount_name="translated_discount2_name",
                status=OrderStatus.DRAFT,
            ),
        ]
    )
    variables = {"filter": draft_orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == count


def test_draft_orders_query_with_filter_search_by_id(
    draft_orders_query_with_filter,
    draft_order,
    staff_api_client,
    permission_manage_orders,
):
    variables = {"filter": {"search": draft_order.pk}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == 1


@pytest.fixture
def update_order_meta():
    return """
    mutation orderUpdateMeta($token: UUID!, $input: MetaInput!) {
        orderUpdateMeta(token: $token, input: $input){
            errors {
                message
            }
        }
    }
    """


@pytest.fixture
def update_order_private_meta():
    return """
    mutation orderUpdatePrivateMeta($id: ID!, $input: MetaInput!) {
        orderUpdatePrivateMeta(id: $id, input: $input){
            errors {
                message
            }
        }
    }
    """


@pytest.fixture
def order_meta_update_variables(order):
    return {
        "token": order.token,
        "input": {
            "namespace": "test",
            "clientName": "client1",
            "key": "foo",
            "value": "bar",
        },
    }


@pytest.fixture
def order_private_meta_update_variables(order):
    order_id = graphene.Node.to_global_id("Order", order.id)
    return {
        "id": order_id,
        "input": {
            "namespace": "test",
            "clientName": "client1",
            "key": "foo",
            "value": "bar",
        },
    }


def test_user_without_permission_cannot_update_private_meta(
    staff_api_client,
    staff_user,
    update_order_private_meta,
    order_private_meta_update_variables,
):
    assert not staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    response = staff_api_client.post_graphql(
        update_order_private_meta, order_private_meta_update_variables
    )
    assert_no_permission(response)


def test_user_does_not_need_permission_to_update_meta(
    staff_api_client, update_order_meta, order_meta_update_variables, order
):
    response = staff_api_client.post_graphql(
        update_order_meta, order_meta_update_variables, permissions=[]
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderUpdateMeta"]["errors"]
    assert len(errors) == 0
    order.refresh_from_db()
    assert order.get_value_from_metadata("foo") == "bar"


def test_user_with_permission_can_update_private_meta(
    permission_manage_orders,
    staff_api_client,
    staff_user,
    update_order_private_meta,
    order_private_meta_update_variables,
    order,
):
    staff_user.user_permissions.add(permission_manage_orders)
    assert staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    response = staff_api_client.post_graphql(
        update_order_private_meta, order_private_meta_update_variables
    )
    content = get_graphql_content(response)
    errors = content["data"]["orderUpdatePrivateMeta"]["errors"]
    assert len(errors) == 0
    order.refresh_from_db()
    assert order.get_value_from_private_metadata("foo") == "bar"


@pytest.fixture
def clear_order_meta():
    return """
        mutation orderClearMeta($token: UUID!, $input: MetaPath!) {
            orderClearMeta(token: $token, input: $input) {
                errors {
                    message
                }
            }
        }
    """


@pytest.fixture
def clear_order_private_meta():
    return """
        mutation orderClearPrivateMeta($id: ID!, $input: MetaPath!) {
            orderClearPrivateMeta(id: $id, input: $input) {
                errors {
                    message
                }
            }
        }
    """


@pytest.fixture
def clear_meta_variables(order):
    return {
        "token": order.token,
        "input": {"namespace": "test", "clientName": "client1", "key": "foo"},
    }


@pytest.fixture
def clear_meta_private_variables(order):
    order_id = graphene.Node.to_global_id("Order", order.id)
    return {
        "id": order_id,
        "input": {
            "namespace": "testPrivate",
            "clientName": "clientPrivate1",
            "key": "foofoo",
        },
    }


@pytest.fixture
def order_with_meta(order):
    order.store_value_in_metadata(items={"foo": "bar"})
    order.store_value_in_private_metadata(items={"foofoo": "barbar"})
    order.save()
    return order


def test_user_without_permission_cannot_clear_meta(
    staff_user, staff_api_client, clear_order_meta, clear_meta_variables
):
    assert not staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    response = staff_api_client.post_graphql(clear_order_meta, clear_meta_variables)
    assert_no_permission(response)


def test_user_without_permission_cannot_clear_private_meta(
    staff_user, staff_api_client, clear_order_private_meta, clear_meta_private_variables
):
    assert not staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    response = staff_api_client.post_graphql(
        clear_order_private_meta, clear_meta_private_variables
    )
    assert_no_permission(response)


def test_user_with_permission_can_clear_meta(
    staff_user,
    staff_api_client,
    clear_order_meta,
    clear_meta_variables,
    order_with_meta,
    permission_manage_orders,
):
    staff_user.user_permissions.add(permission_manage_orders)
    assert staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    response = staff_api_client.post_graphql(clear_order_meta, clear_meta_variables)
    assert response.status_code == 200
    content = get_graphql_content(response)
    errors = content["data"]["orderClearMeta"]["errors"]
    assert len(errors) == 0
    order_with_meta.refresh_from_db()
    assert not order_with_meta.get_value_from_metadata("foo")


def test_user_with_permission_can_clear_private_meta(
    staff_user,
    staff_api_client,
    clear_order_private_meta,
    clear_meta_private_variables,
    order_with_meta,
    permission_manage_orders,
):
    staff_user.user_permissions.add(permission_manage_orders)
    assert staff_user.has_perm(OrderPermissions.MANAGE_ORDERS)
    response = staff_api_client.post_graphql(
        clear_order_private_meta, clear_meta_private_variables
    )
    assert response.status_code == 200
    content = get_graphql_content(response)
    errors = content["data"]["orderClearPrivateMeta"]["errors"]
    assert len(errors) == 0
    order_with_meta.refresh_from_db()
    assert not order_with_meta.get_value_from_private_metadata(key="foofoo")
