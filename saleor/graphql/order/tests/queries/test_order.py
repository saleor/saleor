from decimal import Decimal

import graphene
import pytest
from prices import Money, TaxedMoney

from .....checkout.utils import PRIVATE_META_APP_SHIPPING_ID
from .....core.prices import quantize_price
from .....core.taxes import zero_taxed_money
from .....order import OrderStatus
from .....order.events import transaction_event
from .....order.models import Order, OrderGrantedRefund
from .....order.utils import (
    get_order_country,
    update_order_authorize_data,
    update_order_authorize_status,
    update_order_charge_data,
    update_order_charge_status,
)
from .....payment import ChargeStatus, TransactionAction
from .....payment.models import TransactionEvent, TransactionItem
from .....shipping.models import ShippingMethod, ShippingMethodChannelListing
from .....warehouse.models import Warehouse
from ....order.enums import OrderAuthorizeStatusEnum, OrderChargeStatusEnum
from ....payment.types import PaymentChargeStatusEnum
from ....tests.utils import (
    assert_graphql_error_with_message,
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

ORDERS_FULL_QUERY = """
query OrdersQuery {
    orders(first: 1) {
        edges {
            node {
                number
                canFinalize
                status
                channel {
                    slug
                }
                languageCodeEnum
                statusDisplay
                paymentStatus
                paymentStatusDisplay
                userEmail
                isPaid
                actions
                totalAuthorized{
                    amount
                    currency
                }
                totalCharged{
                    amount
                    currency
                }
                totalCaptured{
                    amount
                    currency
                }
                totalCanceled{
                    amount
                    currency
                }
                totalBalance{
                    amount
                    currency
                }
                shippingPrice {
                    gross {
                        amount
                    }
                }
                shippingTaxRate
                shippingTaxClass {
                    name
                }
                shippingTaxClassName
                shippingTaxClassMetadata {
                    key
                    value
                }
                shippingTaxClassPrivateMetadata {
                    key
                    value
                }
                lines {
                    id
                    isPriceOverridden
                    unitPrice{
                        gross{
                            amount
                        }
                    }
                    unitDiscount{
                        amount
                    }
                    undiscountedUnitPrice{
                        gross{
                            amount
                        }
                        net{
                            amount
                        }
                    }
                }
                discounts{
                    id
                    valueType
                    value
                    reason
                    amount{
                        amount
                    }
                }
                fulfillments {
                    fulfillmentOrder
                }
                payments{
                    id
                    actions
                    total{
                        currency
                        amount
                    }
                }
                transactions{
                    id
                    events{
                       pspReference
                       message
                    }
                }
                authorizeStatus
                chargeStatus
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
                    name
                    description
                    price{
                      amount
                    }
                    minimumOrderPrice {
                      amount
                    }
                    maximumOrderPrice{
                      amount
                    }
                    maximumDeliveryDays
                    minimumDeliveryDays
                    metadata{
                      key
                      value
                    }
                    privateMetadata{
                      key
                      value
                    }
                }
                shippingMethods{
                  id
                  name
                  description
                  price{
                    amount
                  }
                  maximumOrderPrice{
                    amount
                  }
                  minimumOrderPrice{
                    amount
                  }
                  maximumDeliveryDays
                  minimumDeliveryDays
                  metadata{
                    key
                    value
                  }
                  privateMetadata{
                    key
                    value
                  }
                }
                shippingMethod{
                    id
                    name
                    description
                    active
                    message
                    price{
                        amount
                    }
                    maximumOrderPrice{
                        amount
                    }
                    minimumOrderPrice{
                        amount
                    }
                    maximumDeliveryDays
                    minimumDeliveryDays
                    metadata{
                        key
                        value
                    }
                    privateMetadata{
                        key
                        value
                    }
                }
                availableCollectionPoints {
                    id
                    name
                }
                shippingMethod{
                    id
                    name
                    price {
                        amount
                        currency
                    }

                }
                deliveryMethod {
                    __typename
                    ... on ShippingMethod {
                        id
                    }
                    ... on Warehouse {
                        id
                    }
                }
                checkoutId
                events {
                    id
                    date
                    type
                    user {
                        id
                    }
                    app {
                        id
                    }
                    message
                    email
                    reference
                    discount {
                        value
                    }
                }
            }
        }
    }
}
"""


def test_order_query(
    staff_api_client,
    fulfilled_order,
    checkout,
    shipping_zone,
    permission_group_manage_orders,
    permission_group_manage_shipping,
):
    # given
    order = fulfilled_order
    net = Money(amount=Decimal("10"), currency="USD")
    gross = Money(amount=net.amount * Decimal(1.23), currency="USD").quantize()
    shipping_price = TaxedMoney(net=net, gross=gross)
    order.shipping_price = shipping_price
    shipping_tax_rate = Decimal("0.23")
    order.shipping_tax_rate = shipping_tax_rate
    private_value = "abc123"
    public_value = "123abc"
    order.checkout_token = checkout.token
    order.shipping_method.store_value_in_metadata({"test": public_value})
    order.shipping_method.store_value_in_private_metadata({"test": private_value})
    order.shipping_method.save()
    order.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["number"] == str(order.number)
    assert order_data["channel"]["slug"] == order.channel.slug
    assert order_data["canFinalize"] is True
    assert order_data["status"] == order.status.upper()
    assert order_data["statusDisplay"] == order.get_status_display()
    payment_charge_status = PaymentChargeStatusEnum.NOT_CHARGED
    assert order_data["paymentStatus"] == payment_charge_status.name
    assert (
        order_data["paymentStatusDisplay"]
        == dict(ChargeStatus.CHOICES)[payment_charge_status.value]
    )
    assert order_data["isPaid"] == order.is_fully_paid()
    assert order_data["userEmail"] == order.user_email
    assert order_data["languageCodeEnum"] == order.language_code.upper()
    expected_price = Money(
        amount=str(order_data["shippingPrice"]["gross"]["amount"]), currency="USD"
    )
    assert expected_price == shipping_price.gross
    assert order_data["shippingTaxRate"] == float(shipping_tax_rate)
    shipping_tax_class = order.shipping_method.tax_class
    assert order_data["shippingTaxClass"]["name"] == shipping_tax_class.name
    assert order_data["shippingTaxClassName"] == shipping_tax_class.name
    assert (
        order_data["shippingTaxClassMetadata"][0]["key"]
        == list(shipping_tax_class.metadata.keys())[0]
    )
    assert (
        order_data["shippingTaxClassMetadata"][0]["value"]
        == list(shipping_tax_class.metadata.values())[0]
    )
    assert (
        order_data["shippingTaxClassPrivateMetadata"][0]["key"]
        == list(shipping_tax_class.private_metadata.keys())[0]
    )
    assert (
        order_data["shippingTaxClassPrivateMetadata"][0]["value"]
        == list(shipping_tax_class.private_metadata.values())[0]
    )
    assert order_data["shippingMethod"]["active"] is True
    assert order_data["shippingMethod"]["message"] == ""
    assert public_value == order_data["shippingMethod"]["metadata"][0]["value"]
    assert private_value == order_data["shippingMethod"]["privateMetadata"][0]["value"]
    assert len(order_data["lines"]) == order.lines.count()
    fulfillment = order.fulfillments.first().fulfillment_order
    fulfillment_order = order_data["fulfillments"][0]["fulfillmentOrder"]

    assert fulfillment_order == fulfillment
    assert len(order_data["payments"]) == order.payments.count()

    expected_methods = ShippingMethod.objects.applicable_shipping_methods(
        price=order.subtotal.gross,
        weight=order.weight,
        country_code=order.shipping_address.country.code,
        channel_id=order.channel_id,
    )
    expected_collection_points = Warehouse.objects.applicable_for_click_and_collect(
        lines_qs=order.lines, channel_id=order.channel.id
    )

    assert len(order_data["availableShippingMethods"]) == (expected_methods.count())
    assert len(order_data["availableCollectionPoints"]) == (
        expected_collection_points.count()
    )

    method = order_data["availableShippingMethods"][0]
    expected_method = expected_methods.first()
    expected_shipping_price = expected_method.channel_listings.get(
        channel_id=order.channel_id
    )

    assert float(expected_shipping_price.price.amount) == method["price"]["amount"]
    assert (
        float(expected_shipping_price.minimum_order_price.amount)
        == (method["minimumOrderPrice"]["amount"])
    )
    assert order_data["deliveryMethod"]["id"] == order_data["shippingMethod"]["id"]
    assert order_data["checkoutId"] == (
        graphene.Node.to_global_id("Checkout", checkout.token)
    )


def test_order_query_denormalized_shipping_tax_class_data(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)
    shipping_tax_class = order.shipping_method.tax_class
    assert shipping_tax_class

    # when
    shipping_tax_class.delete()
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["shippingTaxClass"] is None
    assert order_data["shippingTaxClassName"] == shipping_tax_class.name
    assert (
        order_data["shippingTaxClassMetadata"][0]["key"]
        == list(shipping_tax_class.metadata.keys())[0]
    )
    assert (
        order_data["shippingTaxClassMetadata"][0]["value"]
        == list(shipping_tax_class.metadata.values())[0]
    )
    assert (
        order_data["shippingTaxClassPrivateMetadata"][0]["key"]
        == list(shipping_tax_class.private_metadata.keys())[0]
    )
    assert (
        order_data["shippingTaxClassPrivateMetadata"][0]["value"]
        == list(shipping_tax_class.private_metadata.values())[0]
    )


def test_order_query_price_overridden(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    fulfilled_order,
):
    # given
    order = fulfilled_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)
    line = order.lines.first()
    line.is_price_overridden = True
    line.save(update_fields=["is_price_overridden"])

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    order_line = order_data["lines"][0]
    assert order_line["isPriceOverridden"] is True


def test_order_query_total_price_is_0(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    price = zero_taxed_money(order.currency)
    order.shipping_price = price
    order.total = price
    shipping_tax_rate = Decimal("0")
    order.shipping_tax_rate = shipping_tax_rate
    private_value = "abc123"
    public_value = "123abc"
    order.shipping_method.store_value_in_metadata({"test": public_value})
    order.shipping_method.store_value_in_private_metadata({"test": private_value})
    order.shipping_method.save()
    order.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["number"] == str(order.number)
    assert order_data["channel"]["slug"] == order.channel.slug
    assert order_data["canFinalize"] is True
    assert order_data["status"] == order.status.upper()
    assert order_data["statusDisplay"] == order.get_status_display()
    payment_charge_status = PaymentChargeStatusEnum.FULLY_CHARGED
    assert order_data["paymentStatus"] == payment_charge_status.name
    assert (
        order_data["paymentStatusDisplay"]
        == dict(ChargeStatus.CHOICES)[payment_charge_status.value]
    )


def test_order_query_shows_non_draft_orders(
    staff_api_client, permission_group_manage_orders, orders
):
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

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query)
    edges = get_graphql_content(response)["data"]["orders"]["edges"]

    assert len(edges) == Order.objects.non_draft().count()


QUERY_ORDERS_WITH_CHANNEL = """
    query OrdersQuery($channel: String) {
        orders(first: 10, channel: $channel) {
            edges {
                node {
                    id
                }
            }
        }
    }
"""


def test_orders_with_channel(
    staff_api_client, permission_group_manage_orders, orders, channel_USD
):
    # given
    query = QUERY_ORDERS_WITH_CHANNEL

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    edges = get_graphql_content(response)["data"]["orders"]["edges"]

    assert len(edges) == 3


def test_orders_with_channel_no_access_to_channel(
    staff_api_client, permission_group_all_perms_channel_USD_only, orders, channel_JPY
):
    # given
    query = QUERY_ORDERS_WITH_CHANNEL

    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    variables = {"channel": channel_JPY.slug}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_orders_without_channel(
    staff_api_client, permission_group_manage_orders, orders
):
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

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query)
    edges = get_graphql_content(response)["data"]["orders"]["edges"]

    assert len(edges) == Order.objects.non_draft().count()


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


@pytest.mark.parametrize(
    ("total_authorized", "total_charged", "expected_status"),
    [
        (Decimal("98.40"), Decimal("0"), OrderAuthorizeStatusEnum.FULL.name),
        (Decimal("0"), Decimal("98.40"), OrderAuthorizeStatusEnum.FULL.name),
        (Decimal("10"), Decimal("88.40"), OrderAuthorizeStatusEnum.FULL.name),
        (Decimal("0"), Decimal("0"), OrderAuthorizeStatusEnum.NONE.name),
        (Decimal("11"), Decimal("0"), OrderAuthorizeStatusEnum.PARTIAL.name),
        (Decimal("0"), Decimal("50.00"), OrderAuthorizeStatusEnum.PARTIAL.name),
        (Decimal("10"), Decimal("40.40"), OrderAuthorizeStatusEnum.PARTIAL.name),
    ],
)
def test_order_query_authorize_status(
    total_authorized,
    total_charged,
    expected_status,
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    fulfilled_order,
):
    # given
    assert fulfilled_order.total.gross.amount == Decimal("98.40")
    fulfilled_order.total_authorized_amount = total_authorized
    fulfilled_order.total_charged_amount = total_charged
    update_order_authorize_status(fulfilled_order, Decimal(0))
    fulfilled_order.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["authorizeStatus"] == expected_status


@pytest.mark.parametrize(
    ("total_authorized", "total_charged", "expected_status"),
    [
        (Decimal("10.40"), Decimal("0"), OrderChargeStatusEnum.NONE.name),
        (Decimal("98.40"), Decimal("0"), OrderChargeStatusEnum.NONE.name),
        (Decimal("0"), Decimal("0"), OrderChargeStatusEnum.NONE.name),
        (Decimal("0"), Decimal("11.00"), OrderChargeStatusEnum.PARTIAL.name),
        (Decimal("88.40"), Decimal("10.00"), OrderChargeStatusEnum.PARTIAL.name),
        (Decimal("0"), Decimal("98.40"), OrderChargeStatusEnum.FULL.name),
    ],
)
def test_order_query_charge_status(
    total_authorized,
    total_charged,
    expected_status,
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    fulfilled_order,
):
    # given
    assert fulfilled_order.total.gross.amount == Decimal("98.40")
    fulfilled_order.total_authorized_amount = total_authorized
    fulfilled_order.total_charged_amount = total_charged
    update_order_charge_status(fulfilled_order, Decimal(0))
    fulfilled_order.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["chargeStatus"] == expected_status


def test_order_query_payment_status_with_total_fulfillment_refund_equal_to_order_total(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    fulfilled_order,
):
    # given
    fulfilled_order.fulfillments.create(
        tracking_number="123", total_refund_amount=fulfilled_order.total.gross.amount
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["paymentStatus"] == PaymentChargeStatusEnum.FULLY_REFUNDED.name


def test_order_query_with_transactions_details(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    fulfilled_order,
    shipping_zone,
):
    # given
    order = fulfilled_order
    net = Money(amount=Decimal("100"), currency="USD")
    gross = Money(amount=net.amount * Decimal(1.23), currency="USD").quantize()
    shipping_price = TaxedMoney(net=net, gross=gross)
    order.shipping_price = shipping_price
    shipping_tax_rate = Decimal("0.23")
    order.shipping_tax_rate = shipping_tax_rate
    private_value = "abc123"
    public_value = "123abc"
    order.shipping_method.store_value_in_metadata({"test": public_value})
    order.shipping_method.store_value_in_private_metadata({"test": private_value})
    order.shipping_method.save()
    order.save()
    transaction_event(
        order=order,
        user=None,
        app=None,
        reference="ref-123",
        message="Message",
    )
    transactions = TransactionItem.objects.bulk_create(
        [
            TransactionItem(
                order_id=order.id,
                message="Authorized",
                name="Credit card",
                psp_reference="123",
                currency="USD",
                authorized_value=Decimal("15"),
                available_actions=[TransactionAction.CHARGE, TransactionAction.CANCEL],
            ),
            TransactionItem(
                order_id=order.id,
                message="Authorized second credit card",
                name="Credit card",
                psp_reference="321",
                currency="USD",
                authorized_value=Decimal("10"),
                available_actions=[TransactionAction.CHARGE, TransactionAction.CANCEL],
            ),
            TransactionItem(
                order_id=order.id,
                message="Captured",
                name="Credit card",
                psp_reference="111",
                currency="USD",
                charged_value=Decimal("15"),
                available_actions=[TransactionAction.REFUND],
            ),
            TransactionItem(
                order_id=order.id,
                message="Captured",
                name="Credit card",
                psp_reference="111",
                currency="USD",
                canceled_value=Decimal("19"),
                available_actions=[],
            ),
        ]
    )
    update_order_authorize_data(order)
    update_order_charge_data(order)
    event_reference = "PSP-ref"
    event_message = "Failed authorization"
    TransactionEvent.objects.bulk_create(
        [
            TransactionEvent(
                message=event_message,
                psp_reference=f"{event_reference}{transaction.token}",
                transaction=transaction,
                currency=transaction.currency,
            )
            for transaction in transactions
        ]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]

    payment_charge_status = PaymentChargeStatusEnum.PARTIALLY_CHARGED
    assert order_data["paymentStatus"] == payment_charge_status.name
    assert (
        order_data["paymentStatusDisplay"]
        == dict(ChargeStatus.CHOICES)[payment_charge_status.value]
    )
    assert order_data["isPaid"] == order.is_fully_paid()

    assert len(order_data["payments"]) == order.payments.count()
    assert Decimal(order_data["totalAuthorized"]["amount"]) == Decimal("25")
    assert Decimal(order_data["totalCaptured"]["amount"]) == Decimal("15")
    assert Decimal(order_data["totalCharged"]["amount"]) == Decimal("15")
    assert Decimal(order_data["totalCanceled"]["amount"]) == Decimal("19")

    assert Decimal(str(order_data["totalBalance"]["amount"])) == Decimal("-83.4")

    for transaction in order_data["transactions"]:
        assert len(transaction["events"]) == 1
        event = transaction["events"][0]
        assert event["message"] == event_message
        _, expected_uuid = graphene.Node.from_global_id(transaction.get("id"))
        assert event["pspReference"] == f"{event_reference}{expected_uuid}"


def test_order_query_shipping_method_channel_listing_does_not_exist(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    order_with_lines,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNFULFILLED
    order.save()

    shipping_method = order.shipping_method
    ShippingMethodChannelListing.objects.filter(
        shipping_method=shipping_method, channel=order.channel
    ).delete()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["shippingMethod"] is None


def test_order_query_external_shipping_method(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    order_with_lines,
):
    external_shipping_method_id = graphene.Node.to_global_id("app", "1:external123")

    # given
    order = order_with_lines
    order.shipping_method = None
    order.private_metadata = {PRIVATE_META_APP_SHIPPING_ID: external_shipping_method_id}
    order.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["shippingMethod"]["id"] == external_shipping_method_id
    assert order_data["shippingMethod"]["name"] == order.shipping_method_name
    assert order_data["shippingMethod"]["price"]["amount"] == float(
        order.shipping_price_gross.amount
    )


def test_order_discounts_query(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    draft_order_with_fixed_discount_order,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.UNFULFILLED
    order.save()

    discount = order.discounts.get()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    discounts_data = order_data.get("discounts")
    assert len(discounts_data) == 1
    discount_data = discounts_data[0]
    _, discount_id = graphene.Node.from_global_id(discount_data["id"])
    assert discount_id == str(discount.id)
    assert discount_data["valueType"] == discount.value_type.upper()
    assert discount_data["value"] == discount.value
    assert discount_data["amount"]["amount"] == discount.amount_value
    assert discount_data["reason"] == discount.reason


def test_order_line_discount_query(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    draft_order_with_fixed_discount_order,
):
    # given
    order = draft_order_with_fixed_discount_order
    order.status = OrderStatus.UNFULFILLED
    order.save()

    unit_discount_value = Decimal("5.0")
    line = order.lines.first()
    line.unit_discount = Money(unit_discount_value, currency=order.currency)
    line.unit_price -= line.unit_discount
    line.save()

    line_with_discount_id = graphene.Node.to_global_id("OrderLine", line.pk)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    lines_data = order_data.get("lines")
    line_with_discount = [
        line for line in lines_data if line["id"] == line_with_discount_id
    ][0]

    unit_gross_amount = quantize_price(
        Decimal(line_with_discount["unitPrice"]["gross"]["amount"]),
        currency=order.currency,
    )
    unit_discount_amount = quantize_price(
        Decimal(line_with_discount["unitDiscount"]["amount"]), currency=order.currency
    )

    undiscounted_unit_price_gross = quantize_price(
        Decimal(line_with_discount["undiscountedUnitPrice"]["gross"]["amount"]),
        currency=order.currency,
    )
    undiscounted_unit_price_net = quantize_price(
        Decimal(line_with_discount["undiscountedUnitPrice"]["net"]["amount"]),
        currency=order.currency,
    )

    expected_unit_price_gross_amount = quantize_price(
        line.unit_price.gross.amount, currency=order.currency
    )
    expected_unit_discount_amount = quantize_price(
        line.unit_discount.amount, currency=order.currency
    )
    expected_undiscounted_unit_price_gross = quantize_price(
        line.undiscounted_unit_price.gross.amount, currency=order.currency
    )
    expected_calculated_gross = quantize_price(
        line.undiscounted_unit_price.net.amount * (line.tax_rate + 1), line.currency
    )
    expected_undiscounted_unit_price_net = quantize_price(
        line.undiscounted_unit_price.net.amount, currency=order.currency
    )

    assert unit_gross_amount == expected_unit_price_gross_amount
    assert unit_discount_amount == expected_unit_discount_amount
    assert undiscounted_unit_price_gross == expected_undiscounted_unit_price_gross
    assert undiscounted_unit_price_net == expected_undiscounted_unit_price_net
    assert undiscounted_unit_price_gross == expected_calculated_gross


def test_order_query_in_pln_channel(
    staff_api_client,
    permission_group_manage_orders,
    permission_group_manage_shipping,
    order_with_lines_channel_PLN,
    shipping_zone,
    channel_PLN,
):
    # given
    shipping_zone.channels.add(channel_PLN)
    order = order_with_lines_channel_PLN
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    permission_group_manage_shipping.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(ORDERS_FULL_QUERY)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert order_data["number"] == str(order.number)
    assert order_data["channel"]["slug"] == order.channel.slug
    assert order_data["canFinalize"] is True
    assert order_data["status"] == order.status.upper()
    assert order_data["statusDisplay"] == order.get_status_display()
    payment_charge_status = PaymentChargeStatusEnum.NOT_CHARGED
    assert order_data["paymentStatus"] == payment_charge_status.name
    assert (
        order_data["paymentStatusDisplay"]
        == dict(ChargeStatus.CHOICES)[payment_charge_status.value]
    )
    assert order_data["isPaid"] == order.is_fully_paid()
    assert order_data["userEmail"] == order.user_email
    expected_price = Money(
        amount=str(order_data["shippingPrice"]["gross"]["amount"]),
        currency=channel_PLN.currency_code,
    )
    assert expected_price == order.shipping_price.gross
    assert len(order_data["lines"]) == order.lines.count()
    assert len(order_data["payments"]) == order.payments.count()

    expected_methods = ShippingMethod.objects.applicable_shipping_methods(
        price=order.subtotal.gross,
        weight=order.weight,
        country_code=order.shipping_address.country.code,
        channel_id=order.channel_id,
    )
    assert len(order_data["availableShippingMethods"]) == (expected_methods.count())

    method = order_data["availableShippingMethods"][0]
    expected_method = expected_methods.first()
    expected_shipping_price = expected_method.channel_listings.get(
        channel_id=order.channel_id
    )
    assert float(expected_shipping_price.price.amount) == method["price"]["amount"]
    assert (
        float(expected_shipping_price.minimum_order_price.amount)
        == (method["minimumOrderPrice"]["amount"])
    )


QUERY_ORDER_BY_ID = """
    query OrderQuery($id: ID) {
        order(id: $id) {
            id
            number
            status
        }
    }
"""


def test_non_staff_user_can_see_his_order(user_api_client, order):
    # given
    query = QUERY_ORDER_BY_ID
    ID = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": ID}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    assert order_data["number"] == str(order.number)


def test_query_order_as_app(app_api_client, order):
    # given
    ID = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": ID}

    # when
    response = app_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content(response)

    # then
    order_data = content["data"]["order"]
    assert order_data["id"] == graphene.Node.to_global_id("Order", order.id)


def test_staff_query_order_by_old_id(staff_api_client, order):
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])
    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content_from_response(response)

    # then
    assert content["data"]["order"]["number"] == str(order.number)


def test_staff_query_order_by_old_id_for_order_with_use_old_id_set_to_false(
    staff_api_client, order
):
    # given
    assert not order.use_old_id
    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content_from_response(response)

    # then
    assert content["data"]["order"] is None


def test_staff_query_order_by_invalid_id(staff_api_client, order):
    # given
    id = "bh/"
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content_from_response(response)

    # then
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Order."
    assert content["data"]["order"] is None


def test_staff_query_order_with_invalid_object_type(staff_api_client, order):
    # given
    variables = {"id": graphene.Node.to_global_id("Checkout", order.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_BY_ID, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["order"] is None


QUERY_ORDER_BY_EXTERNAL_REFERENCE = """
    query OrderQuery($externalReference: String, $id: ID) {
        order(externalReference: $externalReference, id: $id) {
            number
            id
            externalReference
        }
    }
"""


def test_query_order_by_external_reference_missing_permission(user_api_client, order):
    # given
    query = QUERY_ORDER_BY_EXTERNAL_REFERENCE
    ext_ref = "test-ext-ref"
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_query_order_by_external_reference(
    staff_api_client, order, permission_manage_orders
):
    # given
    query = QUERY_ORDER_BY_EXTERNAL_REFERENCE
    ext_ref = "test-ext-ref"
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_orders,
        ],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["order"]
    assert data["number"] == str(order.number)
    assert data["externalReference"] == ext_ref
    assert data["id"] == graphene.Node.to_global_id("Order", order.id)


@pytest.mark.parametrize("external_reference", ['" "', "not-existing"])
def test_query_order_by_not_existing_external_reference(
    external_reference, staff_api_client, order, permission_manage_orders
):
    # given
    query = QUERY_ORDER_BY_EXTERNAL_REFERENCE
    order.external_reference = "test-ext-ref"
    order.save(update_fields=["external_reference"])
    variables = {"externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_orders,
        ],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["order"] is None


def test_query_order_by_external_reference_and_id(user_api_client, order):
    # given
    query = QUERY_ORDER_BY_EXTERNAL_REFERENCE
    ext_ref = "test-ext-ref"
    id = "test-id"
    variables = {"externalReference": ext_ref, "id": id}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_graphql_error_with_message(
        response, "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_query_order_without_external_reference_or_id(user_api_client, order):
    # given
    query = QUERY_ORDER_BY_EXTERNAL_REFERENCE

    # when
    response = user_api_client.post_graphql(query)

    # then
    assert_graphql_error_with_message(
        response, "At least one of arguments is required: 'id', 'external_reference'."
    )


QUERY_ORDER_FIELDS_BY_ID = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            number
            billingAddress{
                city
                streetAddress1
                postalCode
            }
            shippingAddress{
                city
                streetAddress1
                postalCode
            }
            userEmail
            invoices {
                number
            }
        }
    }
"""


def test_query_order_fields_order_with_new_id_by_staff_no_perm(order, staff_api_client):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_order_with_new_id_by_anonymous_user(order, api_client):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_by_old_id_staff_no_perms(order, staff_api_client):
    """Test that old order IDs require proper user permissions to access sensitive fields."""
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    assert_no_permission(response)


def test_query_order_fields_by_old_id_by_order_owner(order, user_api_client):
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_by_old_id_staff_with_perm(
    order, staff_api_client, permission_manage_orders
):
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_FIELDS_BY_ID, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_by_old_id_app_with_perm(
    order, app_api_client, permission_manage_orders
):
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_FIELDS_BY_ID, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_order_with_old_id_staff_with_perm(
    order, app_api_client, permission_manage_orders
):
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.id)}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_FIELDS_BY_ID, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["order"]
    assert (
        content["data"]["order"]["billingAddress"]["streetAddress1"]
        == order.billing_address.street_address_1
    )
    assert (
        content["data"]["order"]["shippingAddress"]["streetAddress1"]
        == order.shipping_address.street_address_1
    )
    assert content["data"]["order"]["userEmail"] == order.user_email


def test_query_order_fields_by_old_id_app_no_perm(order, app_api_client):
    """Test that old order IDs require proper app permissions to access sensitive fields."""
    # given
    order.use_old_id = True
    order.save(update_fields=["use_old_id"])

    variables = {"id": graphene.Node.to_global_id("Order", order.number)}

    # when
    response = app_api_client.post_graphql(QUERY_ORDER_FIELDS_BY_ID, variables)

    # then
    assert_no_permission(response)


def test_order_query_gift_cards(
    staff_api_client, permission_group_manage_orders, order_with_lines, gift_card
):
    query = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            giftCards {
                last4CodeChars
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    gift_card_data = content["data"]["order"]["giftCards"][0]

    assert gift_card.display_code == gift_card_data["last4CodeChars"]
    assert (
        gift_card.current_balance.amount == gift_card_data["currentBalance"]["amount"]
    )


QUERY_ORDER_PRICES = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            displayGrossPrices
        }
    }
"""


def test_order_display_gross_prices_use_default(user_api_client, order_with_lines):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.id)}
    tax_config = order_with_lines.channel.tax_configuration
    tax_config.country_exceptions.all().delete()

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_PRICES, variables)
    content = get_graphql_content(response)
    data = content["data"]["order"]

    # then
    assert data["displayGrossPrices"] == tax_config.display_gross_prices


def test_order_display_gross_prices_use_country_exception(
    user_api_client, order_with_lines
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.id)}
    tax_config = order_with_lines.channel.tax_configuration
    tax_config.country_exceptions.all().delete()
    country_code = get_order_country(order_with_lines)
    tax_country_config = tax_config.country_exceptions.create(
        country=country_code, display_gross_prices=False
    )

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_PRICES, variables)
    content = get_graphql_content(response)
    data = content["data"]["order"]

    # then
    assert data["displayGrossPrices"] == tax_country_config.display_gross_prices


QUERY_ORDERS = """
    query OrdersQuery {
        orders(first: 10) {
            edges {
                node {
                    number
                }
            }
        }
    }
"""


def test_query_orders_by_user_with_access_to_all_channels(
    order_list,
    staff_api_client,
    permission_group_all_perms_all_channels,
    channel_PLN,
    channel_JPY,
    channel_USD,
):
    # given
    user = staff_api_client.user
    permission_group_all_perms_all_channels.user_set.add(user)

    order_list[0].channel = channel_PLN
    order_list[1].channel = channel_JPY
    order_list[2].channel = channel_USD

    Order.objects.bulk_update(order_list, ["channel"])

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS)
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["orders"]["edges"]) == len(order_list)


def test_query_orders_by_user_with_restricted_access_to_channels(
    order_list,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_PLN,
    channel_JPY,
    channel_USD,
):
    # given
    user = staff_api_client.user
    permission_group_all_perms_channel_USD_only.user_set.add(user)

    order_list[0].channel = channel_PLN
    order_list[1].channel = channel_JPY
    order_list[2].channel = channel_USD

    Order.objects.bulk_update(order_list, ["channel"])

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS)
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["orders"]["edges"]) == 1
    assert content["data"]["orders"]["edges"][0]["node"]["number"] == str(
        order_list[2].number
    )


def test_query_orders_by_user_with_restricted_access_to_channels_no_acc_channels(
    order_list,
    staff_api_client,
    permission_group_all_perms_without_any_channel,
    channel_PLN,
    channel_JPY,
    channel_USD,
):
    """Ensure that query returns no orders when user has no accessible channels."""
    # given
    user = staff_api_client.user
    permission_group_all_perms_without_any_channel.user_set.add(user)

    order_list[0].channel = channel_PLN
    order_list[1].channel = channel_JPY
    order_list[2].channel = channel_USD

    Order.objects.bulk_update(order_list, ["channel"])

    # when
    response = staff_api_client.post_graphql(QUERY_ORDERS)
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["orders"]["edges"]) == 0


def test_query_orders_by_app(
    order_list,
    app_api_client,
    permission_manage_orders,
    channel_PLN,
    channel_JPY,
    channel_USD,
):
    # given
    order_list[0].channel = channel_PLN
    order_list[1].channel = channel_JPY
    order_list[2].channel = channel_USD

    Order.objects.bulk_update(order_list, ["channel"])

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDERS, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["orders"]["edges"]) == len(order_list)


def test_query_orders_by_customer(
    order_list,
    user_api_client,
    channel_PLN,
    channel_JPY,
    channel_USD,
):
    # given
    order_list[0].channel = channel_PLN
    order_list[1].channel = channel_JPY
    order_list[2].channel = channel_USD

    Order.objects.bulk_update(order_list, ["channel"])

    # when
    response = user_api_client.post_graphql(QUERY_ORDERS)

    # then
    assert_no_permission(response)


QUERY_ORDER_PAYMENT_STATUSES = """
    query OrderQuery($id: ID!) {
        order(id: $id) {
            paymentStatus
            paymentStatusDisplay
        }
    }
"""


@pytest.mark.parametrize(
    (
        "order_total",
        "granted_refund_amount",
        "total_charged",
        "expected_payment_status",
    ),
    [
        (Decimal(100), Decimal(0), Decimal(0), PaymentChargeStatusEnum.NOT_CHARGED),
        (Decimal(100), Decimal(50), Decimal(0), PaymentChargeStatusEnum.NOT_CHARGED),
        # order total - total granted refund is bigger than total charged
        (
            Decimal(100),
            Decimal(25),
            Decimal(50),
            PaymentChargeStatusEnum.PARTIALLY_CHARGED,
        ),
        # order total is bigger than total charged
        (
            Decimal(100),
            Decimal(0),
            Decimal(50),
            PaymentChargeStatusEnum.PARTIALLY_CHARGED,
        ),
        # order total - total granted refund is 0, total charged is 100, order is
        # marked as fully charged
        (
            Decimal(100),
            Decimal(100),
            Decimal(100),
            PaymentChargeStatusEnum.FULLY_CHARGED,
        ),
        # order total is 0, total charged is 0, order is fully charged
        (Decimal(0), Decimal(0), Decimal(0), PaymentChargeStatusEnum.FULLY_CHARGED),
        # order total - total granted refund is equal to total charged = 0
        (Decimal(100), Decimal(100), Decimal(0), PaymentChargeStatusEnum.FULLY_CHARGED),
        # order total - total granted refund is equal to total charged = 50
        (Decimal(100), Decimal(50), Decimal(50), PaymentChargeStatusEnum.FULLY_CHARGED),
        # order total - total granted refund is equal to total charged = 100
        (Decimal(100), Decimal(0), Decimal(100), PaymentChargeStatusEnum.FULLY_CHARGED),
    ],
)
def test_order_payment_status_with_transaction_and_granted_refunds(
    order_total,
    granted_refund_amount,
    total_charged,
    expected_payment_status,
    user_api_client,
    order_with_lines,
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.id)}
    order_with_lines.payment_transactions.create(
        charged_value=total_charged, currency=order_with_lines.currency
    )
    order_with_lines.total_gross_amount = order_total
    order_with_lines.total_net_amount = order_total
    OrderGrantedRefund.objects.bulk_create(
        [
            OrderGrantedRefund(
                order=order_with_lines,
                amount_value=Decimal(0),
                currency=order_with_lines.currency,
            ),
            OrderGrantedRefund(
                order=order_with_lines,
                amount_value=granted_refund_amount,
                currency=order_with_lines.currency,
            ),
        ]
    )
    order_with_lines.total_charged_amount = total_charged
    order_with_lines.save()
    # when
    response = user_api_client.post_graphql(QUERY_ORDER_PAYMENT_STATUSES, variables)
    content = get_graphql_content(response)
    data = content["data"]["order"]

    # then
    assert data["paymentStatus"] == expected_payment_status.name
    assert data["paymentStatusDisplay"] == dict(ChargeStatus.CHOICES).get(
        expected_payment_status.value
    )


@pytest.mark.parametrize(
    ("order_total", "total_charged", "expected_payment_status"),
    [
        (Decimal(100), Decimal(0), PaymentChargeStatusEnum.NOT_CHARGED),
        # order total is bigger than total charged
        (
            Decimal(100),
            Decimal(50),
            PaymentChargeStatusEnum.PARTIALLY_CHARGED,
        ),
        # order total is 100, total charged is 100, order is fully charged
        (
            Decimal(100),
            Decimal(100),
            PaymentChargeStatusEnum.FULLY_CHARGED,
        ),
        # order total is 0, total charged is 0, order is fully charged
        (Decimal(0), Decimal(0), PaymentChargeStatusEnum.FULLY_CHARGED),
    ],
)
def test_order_payment_status_with_transaction_and_without_granted_refunds(
    order_total,
    total_charged,
    expected_payment_status,
    user_api_client,
    order_with_lines,
):
    # given
    order_with_lines.payment_transactions.create(
        charged_value=total_charged, currency=order_with_lines.currency
    )
    variables = {"id": graphene.Node.to_global_id("Order", order_with_lines.id)}
    order_with_lines.total_gross_amount = order_total
    order_with_lines.total_net_amount = order_total
    order_with_lines.total_charged_amount = total_charged
    order_with_lines.save()
    # when
    response = user_api_client.post_graphql(QUERY_ORDER_PAYMENT_STATUSES, variables)
    content = get_graphql_content(response)
    data = content["data"]["order"]

    # then
    assert data["paymentStatus"] == expected_payment_status.name
    assert data["paymentStatusDisplay"] == dict(ChargeStatus.CHOICES).get(
        expected_payment_status.value
    )
