import copy
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from django.utils import timezone

from .....account.models import Address
from .....core import JobStatus
from .....discount.models import OrderDiscount
from .....invoice.models import Invoice
from .....order import (
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderOrigin,
    OrderStatus,
)
from .....order.error_codes import OrderBulkCreateErrorCode
from .....order.models import (
    Fulfillment,
    FulfillmentLine,
    FulfillmentStatus,
    Order,
    OrderEvent,
    OrderLine,
)
from .....payment import TransactionEventType
from .....payment.models import TransactionEvent, TransactionItem
from .....warehouse.models import Stock
from ....core.enums import ErrorPolicyEnum
from ....discount.enums import DiscountValueTypeEnum, OrderDiscountTypeEnum
from ....payment.enums import TransactionActionEnum
from ....tests.utils import assert_no_permission, get_graphql_content
from ...bulk_mutations.order_bulk_create import MAX_NOTE_LENGTH, MINUTES_DIFF
from ...enums import OrderStatusEnum, StockUpdatePolicyEnum

ORDER_BULK_CREATE = """
    mutation OrderBulkCreate(
        $orders: [OrderBulkCreateInput!]!,
        $errorPolicy: ErrorPolicyEnum,
        $stockUpdatePolicy: StockUpdatePolicyEnum
    ) {
        orderBulkCreate(
            orders: $orders,
            errorPolicy: $errorPolicy,
            stockUpdatePolicy: $stockUpdatePolicy
        ) {
            count
            results {
                order {
                    id
                    user {
                        id
                        email
                    }
                    metadata {
                        key
                        value
                    }
                    privateMetadata {
                        key
                        value
                    }
                    lines {
                        id
                        variant {
                            id
                        }
                        productName
                        variantName
                        translatedVariantName
                        translatedProductName
                        productVariantId
                        isShippingRequired
                        quantity
                        quantityFulfilled
                        unitPrice {
                            gross {
                                amount
                            }
                            net {
                                amount
                            }
                        }
                        unitDiscount {
                            amount
                        }
                        totalPrice {
                            gross {
                                amount
                            }
                            net {
                                amount
                            }
                        }
                        undiscountedUnitPrice{
                            gross {
                                amount
                            }
                            net {
                                amount
                            }
                        }
                        metadata {
                            key
                            value
                        }
                        privateMetadata {
                            key
                            value
                        }
                        taxClass {
                            id
                        }
                        taxClassName
                        taxRate
                        taxClassMetadata {
                            key
                            value
                        }
                        taxClassPrivateMetadata {
                            key
                            value
                        }
                    }
                    billingAddress{
                        postalCode
                        metadata{
                            key
                            value
                        }
                    }
                    shippingAddress{
                        postalCode
                        metadata{
                            key
                            value
                        }
                    }
                    shippingMethodName
                    shippingTaxClass{
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
                    shippingPrice {
                        gross {
                            amount
                        }
                        net {
                            amount
                        }
                    }
                    total{
                        gross {
                            amount
                        }
                        net {
                            amount
                        }
                    }
                    undiscountedTotal{
                        gross {
                            amount
                        }
                        net {
                            amount
                        }
                    }
                    events {
                        message
                        user {
                            id
                        }
                        app {
                            id
                        }
                    }
                    weight {
                        value
                    }
                    externalReference
                    trackingClientId
                    displayGrossPrices
                    channel {
                        slug
                    }
                    status
                    created
                    languageCode
                    collectionPointName
                    redirectUrl
                    origin
                    fulfillments {
                        lines {
                            id
                            quantity
                            orderLine {
                                id
                            }
                        }
                        trackingNumber
                        fulfillmentOrder
                        status
                    }
                    transactions {
                        id
                        pspReference
                        message
                        name
                        authorizedAmount {
                            amount
                            currency
                        }
                        canceledAmount{
                            currency
                            amount
                        }
                        chargedAmount{
                            currency
                            amount
                        }
                        refundedAmount{
                            currency
                            amount
                        }
                        events {
                            amount {
                                amount
                            }
                            type
                        }
                    }
                    invoices {
                        number
                        url
                    }
                    discounts {
                        type
                        valueType
                        value
                        reason
                    }
                    voucher {
                        id
                        code
                    }
                    voucherCode
                }
                errors {
                    path
                    message
                    code
                }
            }
            errors {
                message
                code
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
    gift_card,
    voucher_without_channel,
):
    shipping_method = shipping_method_channel_PLN
    user = {
        "id": graphene.Node.to_global_id("User", customer_user.id),
        "email": None,
    }
    delivery_method = {
        "shippingMethodId": graphene.Node.to_global_id(
            "ShippingMethod", shipping_method.id
        ),
        "shippingMethodName": "Denormalized name",
        "shippingTaxClassId": graphene.Node.to_global_id(
            "TaxClass", default_tax_class.id
        ),
        "shippingTaxClassName": "Denormalized name",
        "shippingPrice": {
            "gross": 120,
            "net": 100,
        },
        "shippingTaxRate": 0.2,
        "shippingTaxClassMetadata": [
            {
                "key": "md key",
                "value": "md value",
            }
        ],
        "shippingTaxClassPrivateMetadata": [
            {
                "key": "pmd key",
                "value": "pmd value",
            }
        ],
    }
    line = {
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.id),
        "createdAt": timezone.now(),
        "productName": "Product Name",
        "variantName": "Variant Name",
        "translatedProductName": "Nazwa Produktu",
        "translatedVariantName": "Nazwa Wariantu",
        "isShippingRequired": True,
        "isGiftCard": False,
        "quantity": 5,
        "totalPrice": {
            "gross": 120,
            "net": 100,
        },
        "undiscountedTotalPrice": {
            "gross": 120,
            "net": 100,
        },
        "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
        "metadata": [{"key": "md key", "value": "md value"}],
        "privateMetadata": [{"key": "pmd key", "value": "pmd value"}],
        "taxRate": 0.2,
        "taxClassId": graphene.Node.to_global_id("TaxClass", default_tax_class.id),
        "taxClassName": "Line Tax Class Name",
        "taxClassMetadata": [{"key": "md key", "value": "md value"}],
        "taxClassPrivateMetadata": [{"key": "pmd key", "value": "pmd value"}],
    }
    note = {
        "message": "Test message",
        "date": timezone.now(),
        "userId": graphene.Node.to_global_id("User", customer_user.id),
    }
    fulfillment_line = {
        "variantId": graphene.Node.to_global_id("ProductVariant", variant.id),
        "quantity": 5,
        "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.id),
        "orderLineIndex": 0,
    }
    fulfillment = {"trackingCode": "abc-123", "lines": [fulfillment_line]}

    transaction = {
        "name": "Authorized for 10$",
        "message": "Credit Card",
        "pspReference": "PSP reference - 123",
        "availableActions": [
            TransactionActionEnum.CHARGE.name,
            TransactionActionEnum.CANCEL.name,
        ],
        "amountAuthorized": {
            "amount": Decimal("10"),
            "currency": "PLN",
        },
        "metadata": [{"key": "test-1", "value": "123"}],
        "privateMetadata": [{"key": "test-2", "value": "321"}],
    }

    invoice = {
        "number": "01/12/2020/TEST",
        "url": "http://www.example.com",
        "createdAt": timezone.now(),
        "metadata": [{"key": "md key", "value": "md value"}],
        "privateMetadata": [{"key": "pmd key", "value": "pmd value"}],
    }

    discount = {
        "valueType": DiscountValueTypeEnum.FIXED.name,
        "value": 10,
        "reason": "birthday",
    }

    return {
        "channel": channel_PLN.slug,
        "createdAt": timezone.now(),
        "status": OrderStatusEnum.DRAFT.name,
        "user": user,
        "billingAddress": graphql_address_data,
        "shippingAddress": graphql_address_data,
        "currency": "PLN",
        "languageCode": "PL",
        "deliveryMethod": delivery_method,
        "lines": [line],
        "notes": [note],
        "fulfillments": [fulfillment],
        "weight": "10.15",
        "redirectUrl": "https://www.example.com",
        "transactions": [transaction],
        "invoices": [invoice],
        "discounts": [discount],
        "giftCards": ["never_expiry"],
        "voucherCode": "mirumee",
        "metadata": [{"key": "md key", "value": "md value"}],
        "privateMetadata": [{"key": "pmd key", "value": "pmd value"}],
    }


@pytest.fixture
def order_bulk_input_with_multiple_order_lines_and_fulfillments(
    order_bulk_input,
    product_variant_list,
    warehouses,
):
    order = order_bulk_input
    order_line_1 = order["lines"][0]
    order_line_2 = copy.deepcopy(order["lines"][0])
    order_line_3 = copy.deepcopy(order["lines"][0])

    warehouse_1_id = graphene.Node.to_global_id("Warehouse", warehouses[0].id)
    warehouse_2_id = graphene.Node.to_global_id("Warehouse", warehouses[1].id)
    variant_1_id = graphene.Node.to_global_id(
        "ProductVariant", product_variant_list[0].id
    )
    variant_2_id = graphene.Node.to_global_id(
        "ProductVariant", product_variant_list[1].id
    )

    order_line_1["variantId"] = variant_1_id
    order_line_1["warehouse"] = warehouse_1_id
    order_line_1["quantity"] = 10

    order_line_2["variantId"] = variant_2_id
    order_line_2["warehouse"] = warehouse_1_id
    order_line_2["quantity"] = 50

    order_line_3["variantId"] = variant_2_id
    order_line_3["warehouse"] = warehouse_2_id
    order_line_3["quantity"] = 20

    fulfillment_1_line_1 = {
        "variantId": variant_1_id,
        "orderLineIndex": 0,
        "quantity": 5,
        "warehouse": warehouse_1_id,
    }
    fulfillment_1 = {"trackingCode": "abc-1", "lines": [fulfillment_1_line_1]}

    fulfillment_2_line_1 = {
        "variantId": variant_1_id,
        "orderLineIndex": 0,
        "quantity": 5,
        "warehouse": warehouse_1_id,
    }
    fulfillment_2_line_2 = {
        "variantId": variant_2_id,
        "orderLineIndex": 1,
        "quantity": 33,
        "warehouse": warehouse_1_id,
    }
    fulfillment_2_line_3 = {
        "variantId": variant_2_id,
        "orderLineIndex": 2,
        "quantity": 17,
        "warehouse": warehouse_2_id,
    }
    fulfillment_2 = {
        "trackingCode": "abc-2",
        "lines": [fulfillment_2_line_1, fulfillment_2_line_2, fulfillment_2_line_3],
    }

    order["lines"] = [order_line_1, order_line_2, order_line_3]
    order["fulfillments"] = [fulfillment_1, fulfillment_2]

    return order


def test_order_bulk_create(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input,
    app,
    channel_PLN,
    customer_user,
    default_tax_class,
    graphql_address_data,
    shipping_method_channel_PLN,
    variant,
    voucher,
):
    # given
    orders_count = Order.objects.count()
    order_lines_count = OrderLine.objects.count()
    order_events_count = OrderEvent.objects.count()
    address_count = Address.objects.count()
    fulfillments_count = Fulfillment.objects.count()
    fulfillment_lines_count = FulfillmentLine.objects.count()
    transactions_count = TransactionItem.objects.count()
    transaction_events_count = TransactionEvent.objects.count()
    invoice_count = Invoice.objects.count()
    discount_count = OrderDiscount.objects.count()
    voucher_code = "mirumee"

    order = order_bulk_input
    order["externalReference"] = "ext-ref-1"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]

    order = data[0]["order"]
    assert order["externalReference"] == "ext-ref-1"
    assert order["channel"]["slug"] == channel_PLN.slug
    assert order["created"]
    assert order["status"] == OrderStatus.DRAFT.upper()
    assert order["user"]["id"] == graphene.Node.to_global_id("User", customer_user.id)
    assert order["languageCode"] == "pl"
    assert order["shippingTaxClassMetadata"][0]["key"] == "md key"
    assert order["shippingTaxClassMetadata"][0]["value"] == "md value"
    assert order["shippingTaxClassPrivateMetadata"][0]["key"] == "pmd key"
    assert order["shippingTaxClassPrivateMetadata"][0]["value"] == "pmd value"
    assert order["shippingPrice"]["gross"]["amount"] == 120
    assert order["shippingPrice"]["net"]["amount"] == 100
    assert order["total"]["gross"]["amount"] == 120
    assert order["total"]["net"]["amount"] == 100
    assert order["undiscountedTotal"]["gross"]["amount"] == 120
    assert order["undiscountedTotal"]["net"]["amount"] == 100
    assert order["redirectUrl"] == "https://www.example.com"
    assert order["origin"] == OrderOrigin.BULK_CREATE.upper()
    assert order["weight"]["value"] == 10.15
    assert order["displayGrossPrices"]
    assert order["metadata"][0]["key"] == "md key"
    assert order["metadata"][0]["value"] == "md value"
    assert order["privateMetadata"][0]["key"] == "pmd key"
    assert order["privateMetadata"][0]["value"] == "pmd value"
    assert order["voucher"]["id"] == graphene.Node.to_global_id("Voucher", voucher.id)
    assert order["voucher"]["code"] == voucher_code
    assert order["voucherCode"] == voucher_code
    db_order = Order.objects.get()
    assert db_order.external_reference == "ext-ref-1"
    assert db_order.channel.slug == channel_PLN.slug
    assert db_order.created_at
    assert db_order.status == OrderStatus.DRAFT
    assert db_order.user == customer_user
    assert db_order.language_code == "pl"
    assert not db_order.collection_point
    assert not db_order.collection_point_name
    assert db_order.shipping_method == shipping_method_channel_PLN
    assert db_order.shipping_method_name == "Denormalized name"
    assert db_order.shipping_tax_class == default_tax_class
    assert db_order.shipping_tax_class_name == "Denormalized name"
    assert db_order.shipping_tax_rate == Decimal("0.2")
    assert db_order.shipping_tax_class_metadata["md key"] == "md value"
    assert db_order.shipping_tax_class_private_metadata["pmd key"] == "pmd value"
    assert db_order.shipping_price_gross_amount == 120
    assert db_order.shipping_price_net_amount == 100
    assert db_order.base_shipping_price_amount == 100
    assert db_order.total_gross_amount == 120
    assert db_order.total_net_amount == 100
    assert db_order.undiscounted_total_gross_amount == 120
    assert db_order.undiscounted_total_net_amount == 100
    assert db_order.redirect_url == "https://www.example.com"
    assert db_order.origin == OrderOrigin.BULK_CREATE
    assert db_order.weight.g == 10.15 * 1000
    assert db_order.display_gross_prices
    assert db_order.currency == "PLN"
    assert db_order.gift_cards.first().code == "never_expiry"
    assert db_order.voucher.code == voucher_code
    assert db_order.voucher_code == voucher_code
    assert db_order.metadata["md key"] == "md value"
    assert db_order.private_metadata["pmd key"] == "pmd value"
    assert db_order.total_authorized_amount == Decimal("10")
    assert db_order.authorize_status == OrderAuthorizeStatus.PARTIAL.lower()
    assert db_order.shipping_address.validation_skipped is False
    assert db_order.billing_address.validation_skipped is False

    order_line = order["lines"][0]
    assert order_line["variant"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", variant.id
    )
    assert order_line["productName"] == "Product Name"
    assert order_line["variantName"] == "Variant Name"
    assert order_line["translatedProductName"] == "Nazwa Produktu"
    assert order_line["translatedVariantName"] == "Nazwa Wariantu"
    assert order_line["isShippingRequired"]
    assert order_line["quantity"] == 5
    assert order_line["quantityFulfilled"] == 5
    assert order_line["unitPrice"]["gross"]["amount"] == Decimal(120 / 5)
    assert order_line["unitPrice"]["net"]["amount"] == Decimal(100 / 5)
    assert order_line["undiscountedUnitPrice"]["gross"]["amount"] == Decimal(120 / 5)
    assert order_line["undiscountedUnitPrice"]["net"]["amount"] == Decimal(100 / 5)
    assert order_line["unitDiscount"]["amount"] == 0
    assert order_line["totalPrice"]["gross"]["amount"] == 120
    assert order_line["totalPrice"]["net"]["amount"] == 100
    assert order_line["metadata"][0]["key"] == "md key"
    assert order_line["metadata"][0]["value"] == "md value"
    assert order_line["privateMetadata"][0]["key"] == "pmd key"
    assert order_line["privateMetadata"][0]["value"] == "pmd value"
    assert order_line["taxClass"]["id"] == graphene.Node.to_global_id(
        "TaxClass", default_tax_class.id
    )
    assert order_line["taxClassName"] == "Line Tax Class Name"
    assert order_line["taxRate"] == 0.2
    assert order_line["taxClassMetadata"][0]["key"] == "md key"
    assert order_line["taxClassMetadata"][0]["value"] == "md value"
    assert order_line["taxClassPrivateMetadata"][0]["key"] == "pmd key"
    assert order_line["taxClassPrivateMetadata"][0]["value"] == "pmd value"
    db_order_line = OrderLine.objects.get()
    assert db_order_line.variant == variant
    assert db_order_line.product_name == "Product Name"
    assert db_order_line.variant_name == "Variant Name"
    assert db_order_line.translated_product_name == "Nazwa Produktu"
    assert db_order_line.translated_variant_name == "Nazwa Wariantu"
    assert db_order_line.is_shipping_required
    assert db_order_line.quantity == 5
    assert db_order_line.quantity_fulfilled == 5
    assert db_order_line.unit_price.gross.amount == Decimal(120 / 5)
    assert db_order_line.unit_price.net.amount == Decimal(100 / 5)
    assert db_order_line.undiscounted_unit_price.gross.amount == Decimal(120 / 5)
    assert db_order_line.undiscounted_unit_price.net.amount == Decimal(100 / 5)
    assert db_order_line.unit_discount_amount == 0
    assert db_order_line.total_price.gross.amount == 120
    assert db_order_line.total_price.net.amount == 100
    assert db_order_line.undiscounted_total_price.gross.amount == 120
    assert db_order_line.undiscounted_total_price.net.amount == 100
    assert db_order_line.metadata["md key"] == "md value"
    assert db_order_line.private_metadata["pmd key"] == "pmd value"
    assert db_order_line.tax_class == default_tax_class
    assert db_order_line.tax_class_name == "Line Tax Class Name"
    assert db_order_line.tax_rate == Decimal("0.2")
    assert db_order_line.tax_class_metadata["md key"] == "md value"
    assert db_order_line.tax_class_private_metadata["pmd key"] == "pmd value"
    assert db_order_line.currency == "PLN"
    assert db_order.lines.first() == db_order_line

    assert order["billingAddress"]["postalCode"] == graphql_address_data["postalCode"]
    assert order["shippingAddress"]["postalCode"] == graphql_address_data["postalCode"]
    assert db_order.billing_address.postal_code == graphql_address_data["postalCode"]
    assert db_order.shipping_address.postal_code == graphql_address_data["postalCode"]
    assert order["billingAddress"]["metadata"] == graphql_address_data["metadata"]
    assert db_order.billing_address.metadata == {
        graphql_address_data["metadata"][0]["key"]: graphql_address_data["metadata"][0][
            "value"
        ]
    }
    assert order["shippingAddress"]["metadata"] == graphql_address_data["metadata"]
    assert db_order.shipping_address.metadata == {
        graphql_address_data["metadata"][0]["key"]: graphql_address_data["metadata"][0][
            "value"
        ]
    }
    note = order["events"][0]
    assert note["message"] == "Test message"
    assert note["user"]["id"] == graphene.Node.to_global_id("User", customer_user.id)
    assert not note["app"]
    db_event = OrderEvent.objects.get()
    assert db_event.parameters["message"] == "Test message"
    assert db_event.user == customer_user
    assert not db_event.app
    assert db_event.type == OrderEvents.NOTE_ADDED
    assert db_order.events.first() == db_event

    fulfillment = order["fulfillments"][0]
    assert fulfillment["trackingNumber"] == "abc-123"
    assert fulfillment["fulfillmentOrder"] == 1
    assert fulfillment["status"] == FulfillmentStatus.FULFILLED.upper()
    db_fulfillment = Fulfillment.objects.get()
    assert db_fulfillment.order_id == db_order.id
    assert db_fulfillment.tracking_number == "abc-123"
    assert db_fulfillment.fulfillment_order == 1
    assert db_fulfillment.status == FulfillmentStatus.FULFILLED

    fulfillment_line = fulfillment["lines"][0]
    assert fulfillment_line["quantity"] == 5
    assert fulfillment_line["orderLine"]["id"] == order_line["id"]
    db_fulfillment_line = FulfillmentLine.objects.get()
    assert db_fulfillment_line.quantity == 5
    assert db_fulfillment_line.order_line_id == db_order_line.id
    assert db_fulfillment_line.fulfillment_id == db_fulfillment.id
    assert db_fulfillment.lines.all()[0].id == db_fulfillment_line.id

    transaction = order["transactions"][0]
    assert transaction["pspReference"] == "PSP reference - 123"
    assert transaction["message"] == "Credit Card"
    assert transaction["name"] == "Authorized for 10$"
    assert transaction["authorizedAmount"]["amount"] == Decimal("10")
    assert transaction["authorizedAmount"]["currency"] == "PLN"
    db_transaction = TransactionItem.objects.get()
    assert db_transaction.authorized_value == Decimal("10")
    assert db_transaction.currency == "PLN"
    assert db_transaction.psp_reference == "PSP reference - 123"
    assert db_transaction.name == "Authorized for 10$"
    assert db_transaction.order_id == db_order.id
    assert db_transaction.message == "Credit Card"
    assert db_transaction.metadata == {"test-1": "123"}
    assert db_transaction.private_metadata == {"test-2": "321"}

    transaction_event = order["transactions"][0]["events"][0]
    assert transaction_event["amount"]["amount"] == Decimal("10")
    assert (
        transaction_event["type"] == TransactionEventType.AUTHORIZATION_SUCCESS.upper()
    )
    db_transaction_event = TransactionEvent.objects.get()
    assert db_transaction_event.amount.amount == Decimal("10")
    assert db_transaction_event.type == TransactionEventType.AUTHORIZATION_SUCCESS
    assert db_transaction_event.transaction_id == db_transaction.id

    invoice = order["invoices"][0]
    assert invoice["number"] == "01/12/2020/TEST"
    assert invoice["url"] == "http://www.example.com"
    db_invoice = Invoice.objects.get()
    assert db_invoice.number == "01/12/2020/TEST"
    assert db_invoice.external_url == "http://www.example.com"
    assert db_invoice.url == "http://www.example.com"
    assert db_invoice.private_metadata["pmd key"] == "pmd value"
    assert db_invoice.metadata["md key"] == "md value"
    assert db_invoice.order_id == db_order.id
    assert db_invoice.status == JobStatus.SUCCESS

    assert len(order["discounts"]) == 1
    discount = order["discounts"][0]
    assert discount["type"] == OrderDiscountTypeEnum.MANUAL.name
    assert discount["valueType"] == DiscountValueTypeEnum.FIXED.name
    assert discount["value"] == 10
    assert discount["reason"] == "birthday"
    db_discount = OrderDiscount.objects.get()
    assert db_discount.type == OrderDiscountTypeEnum.MANUAL.value
    assert db_discount.value_type == DiscountValueTypeEnum.FIXED.value
    assert db_discount.value == 10
    assert db_discount.reason == "birthday"
    assert db_discount.order_id == db_order.id

    assert Order.objects.count() == orders_count + 1
    assert OrderLine.objects.count() == order_lines_count + 1
    assert Address.objects.count() == address_count + 2
    assert OrderEvent.objects.count() == order_events_count + 1
    assert Fulfillment.objects.count() == fulfillments_count + 1
    assert FulfillmentLine.objects.count() == fulfillment_lines_count + 1
    assert TransactionItem.objects.count() == transactions_count + 1
    assert TransactionEvent.objects.count() == transaction_events_count + 1
    assert Invoice.objects.count() == invoice_count + 1
    assert OrderDiscount.objects.count() == discount_count + 1


def test_order_bulk_create_multiple_orders(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()
    order_lines_count = OrderLine.objects.count()

    order_1 = order_bulk_input
    order_2 = order_bulk_input

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order_1, order_2],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

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


def test_order_bulk_create_multiple_lines(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
    product_variant_list,
):
    # given
    lines_count = OrderLine.objects.count()

    order = order_bulk_input
    line_2 = copy.deepcopy(order["lines"][0])
    variant_2 = product_variant_list[2]
    line_2["variantId"] = graphene.Node.to_global_id("ProductVariant", variant_2.id)
    line_2["totalPrice"]["gross"] = 60
    line_2["totalPrice"]["net"] = 50
    order["lines"].append(line_2)

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]
    order = content["data"]["orderBulkCreate"]["results"][0]["order"]

    line_1 = order["lines"][0]
    assert line_1["unitPrice"]["gross"]["amount"] == Decimal(120 / 5)
    assert line_1["unitPrice"]["net"]["amount"] == Decimal(100 / 5)
    line_2 = order["lines"][1]
    assert line_2["unitPrice"]["gross"]["amount"] == Decimal(60 / 5)
    assert line_2["unitPrice"]["net"]["amount"] == Decimal(50 / 5)

    db_lines = OrderLine.objects.all()
    db_line_1 = db_lines[0]
    assert db_line_1.unit_price.gross.amount == Decimal(120 / 5)
    assert db_line_1.unit_price.net.amount == Decimal(100 / 5)
    db_line_2 = db_lines[1]
    assert db_line_2.unit_price.gross.amount == Decimal(60 / 5)
    assert db_line_2.unit_price.net.amount == Decimal(50 / 5)

    assert order["total"]["gross"]["amount"] == 180
    assert order["total"]["net"]["amount"] == 150
    db_order = Order.objects.get()
    assert db_order.total_gross_amount == 180
    assert db_order.total_net_amount == 150

    assert OrderLine.objects.count() == lines_count + 2


def test_order_bulk_create_line_without_variant(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    lines_count = OrderLine.objects.count()

    order = order_bulk_input
    order["lines"][0]["variantId"] = None
    order["lines"][0]["variantName"] = None
    order["fulfillments"][0]["lines"][0]["variantId"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert len(content["data"]["orderBulkCreate"]["results"][0]["errors"]) == 2

    order = content["data"]["orderBulkCreate"]["results"][0]["order"]

    line_1 = order["lines"][0]
    assert line_1["unitPrice"]["gross"]["amount"] == Decimal(120 / 5)
    assert line_1["unitPrice"]["net"]["amount"] == Decimal(100 / 5)

    db_lines = OrderLine.objects.all()
    db_line_1 = db_lines[0]
    assert db_line_1.unit_price.gross.amount == Decimal(120 / 5)
    assert db_line_1.unit_price.net.amount == Decimal(100 / 5)

    assert order["total"]["gross"]["amount"] == 120
    assert order["total"]["net"]["amount"] == 100
    db_order = Order.objects.get()
    assert db_order.total_gross_amount == 120
    assert db_order.total_net_amount == 100

    error0 = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error0["message"] == (
        "One of [variant_id, variant_external_reference, variant_sku] arguments"
        " must be provided to resolve ProductVariant instance."
    )
    assert error0["code"] == OrderBulkCreateErrorCode.REQUIRED.name
    assert error0["path"] == "lines.0"

    error1 = content["data"]["orderBulkCreate"]["results"][0]["errors"][1]
    assert error1["message"] == (
        "One of [variant_id, variant_external_reference, variant_sku] arguments"
        " must be provided to resolve ProductVariant instance."
    )
    assert error1["code"] == OrderBulkCreateErrorCode.REQUIRED.name
    assert error1["path"] == "fulfillments.0.lines.0"

    assert OrderLine.objects.count() == lines_count + 1


def test_order_bulk_create_line_without_variant_and_product_name_fails(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given

    order = order_bulk_input
    order["lines"][0]["variantId"] = None
    order["lines"][0]["productName"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert len(content["data"]["orderBulkCreate"]["results"][0]["errors"]) == 2

    error0 = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error0["message"] == (
        "One of [variant_id, variant_external_reference, variant_sku] arguments"
        " must be provided to resolve ProductVariant instance."
    )
    assert error0["code"] == OrderBulkCreateErrorCode.REQUIRED.name
    assert error0["path"] == "lines.0"

    error1 = content["data"]["orderBulkCreate"]["results"][0]["errors"][1]
    assert error1["message"] == (
        "Order line input must contain product name when no variant provided."
    )
    assert error1["code"] == OrderBulkCreateErrorCode.REQUIRED.name
    assert error1["path"] == "lines.0"


def test_order_bulk_create_multiple_notes(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    permission_manage_apps,
    order_bulk_input,
    customer_user,
    app,
):
    # given
    events_count = OrderEvent.objects.count()

    note_1 = {
        "message": "User message",
        "date": timezone.now(),
        "userId": graphene.Node.to_global_id("User", customer_user.id),
    }
    note_2 = {
        "message": "App message",
        "date": timezone.now(),
        "appId": graphene.Node.to_global_id("App", app.id),
    }
    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
        permission_manage_apps,
    )
    order_bulk_input["notes"] = [note_1, note_2]

    variables = {
        "orders": [order_bulk_input],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]

    event_1 = content["data"]["orderBulkCreate"]["results"][0]["order"]["events"][0]
    assert event_1["message"] == note_1["message"]
    assert event_1["user"]["id"] == note_1["userId"]
    event_2 = content["data"]["orderBulkCreate"]["results"][0]["order"]["events"][1]
    assert event_2["message"] == note_2["message"]
    assert event_2["app"]["id"] == note_2["appId"]

    db_events = OrderEvent.objects.all()
    db_event_1 = db_events[0]
    assert db_event_1.parameters["message"] == note_1["message"]
    assert db_event_1.user == customer_user
    db_event_2 = db_events[1]
    assert db_event_2.parameters["message"] == note_2["message"]
    assert db_event_2.app == app

    assert OrderEvent.objects.count() == events_count + 2


def test_order_bulk_create_multiple_fulfillments(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
):
    # given
    fulfillments_count = Fulfillment.objects.count()
    fulfillment_lines_count = FulfillmentLine.objects.count()

    order = order_bulk_input_with_multiple_order_lines_and_fulfillments

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]

    order = data[0]["order"]
    order_line_1, order_line_2, order_line_3 = order["lines"]
    db_order = Order.objects.get()
    db_order_line_1, db_order_line_2, db_order_line_3 = OrderLine.objects.all()

    fulfillment_1, fulfillment_2 = order["fulfillments"]
    assert fulfillment_1["trackingNumber"] == "abc-1"
    assert fulfillment_1["fulfillmentOrder"] == 1
    assert fulfillment_1["status"] == FulfillmentStatus.FULFILLED.upper()
    db_fulfillment_1, db_fulfillment_2 = Fulfillment.objects.all()
    assert db_fulfillment_1.order_id == db_order.id
    assert db_fulfillment_1.tracking_number == "abc-1"
    assert db_fulfillment_1.fulfillment_order == 1
    assert db_fulfillment_1.status == FulfillmentStatus.FULFILLED

    fulfillment_1_line_1 = fulfillment_1["lines"][0]
    assert fulfillment_1_line_1["quantity"] == 5
    assert fulfillment_1_line_1["orderLine"]["id"] == order_line_1["id"]

    (
        db_fulfillment_1_line_1,
        db_fulfillment_2_line_1,
        db_fulfillment_2_line_2,
        db_fulfillment_2_line_3,
    ) = FulfillmentLine.objects.all()
    assert db_fulfillment_1_line_1.quantity == 5
    assert db_fulfillment_1_line_1.order_line_id == db_order_line_1.id
    assert db_fulfillment_1_line_1.fulfillment_id == db_fulfillment_1.id
    assert db_fulfillment_1.lines.all()[0].id == db_fulfillment_1_line_1.id

    assert fulfillment_2["trackingNumber"] == "abc-2"
    assert fulfillment_2["fulfillmentOrder"] == 2
    assert fulfillment_2["status"] == FulfillmentStatus.FULFILLED.upper()
    assert db_fulfillment_2.order_id == db_order.id
    assert db_fulfillment_2.tracking_number == "abc-2"
    assert db_fulfillment_2.fulfillment_order == 2
    assert db_fulfillment_2.status == FulfillmentStatus.FULFILLED

    (
        fulfillment_2_line_1,
        fulfillment_2_line_2,
        fulfillment_2_line_3,
    ) = fulfillment_2["lines"]
    assert fulfillment_2_line_1["quantity"] == 5
    assert fulfillment_2_line_1["orderLine"]["id"] == order_line_1["id"]
    assert fulfillment_2_line_2["quantity"] == 33
    assert fulfillment_2_line_2["orderLine"]["id"] == order_line_2["id"]
    assert fulfillment_2_line_3["quantity"] == 17
    assert fulfillment_2_line_3["orderLine"]["id"] == order_line_3["id"]

    assert db_fulfillment_2_line_1.quantity == 5
    assert db_fulfillment_2_line_1.order_line_id == db_order_line_1.id
    assert db_fulfillment_2_line_1.fulfillment_id == db_fulfillment_2.id
    assert db_fulfillment_2.lines.all()[0].id == db_fulfillment_2_line_1.id
    assert db_fulfillment_2_line_2.quantity == 33
    assert db_fulfillment_2_line_2.order_line_id == db_order_line_2.id
    assert db_fulfillment_2_line_2.fulfillment_id == db_fulfillment_2.id
    assert db_fulfillment_2.lines.all()[1].id == db_fulfillment_2_line_2.id
    assert db_fulfillment_2_line_3.quantity == 17
    assert db_fulfillment_2_line_3.order_line_id == db_order_line_3.id
    assert db_fulfillment_2_line_3.fulfillment_id == db_fulfillment_2.id
    assert db_fulfillment_2.lines.all()[2].id == db_fulfillment_2_line_3.id

    assert Fulfillment.objects.count() == fulfillments_count + 2
    assert FulfillmentLine.objects.count() == fulfillment_lines_count + 4


def test_order_bulk_create_multiple_transactions(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    transactions_count = TransactionItem.objects.count()

    transaction_1 = {
        "name": "Authorized for 10$",
        "amountAuthorized": {
            "amount": Decimal("20"),
            "currency": "PLN",
        },
    }

    transaction_2 = {
        "message": "Credit Card",
        "amountCharged": {
            "amount": Decimal("100"),
            "currency": "PLN",
        },
    }

    transaction_3 = {
        "pspReference": "PSP reference - 123",
        "amountRefunded": {
            "amount": Decimal("15"),
            "currency": "PLN",
        },
    }

    transaction_4 = {
        "amountCanceled": {
            "amount": Decimal("20"),
            "currency": "PLN",
        },
    }

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    order_bulk_input["transactions"] = [
        transaction_1,
        transaction_2,
        transaction_3,
        transaction_4,
    ]

    variables = {
        "orders": [order_bulk_input],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]
    order = data[0]["order"]

    transaction_1, transaction_2, transaction_3, transaction_4 = order["transactions"]
    assert transaction_1["name"] == "Authorized for 10$"
    assert transaction_1["authorizedAmount"]["amount"] == Decimal("20")
    assert transaction_2["message"] == "Credit Card"
    assert transaction_2["chargedAmount"]["amount"] == Decimal("100")
    assert transaction_2["chargedAmount"]["currency"] == "PLN"
    assert transaction_3["pspReference"] == "PSP reference - 123"
    assert transaction_3["refundedAmount"]["amount"] == Decimal("15")
    assert transaction_3["refundedAmount"]["currency"] == "PLN"
    assert transaction_4["canceledAmount"]["amount"] == Decimal("20")
    assert transaction_4["canceledAmount"]["currency"] == "PLN"

    db_order = Order.objects.get()
    (
        db_transaction_1,
        db_transaction_2,
        db_transaction_3,
        db_transaction_4,
    ) = TransactionItem.objects.all()
    assert db_transaction_1.name == "Authorized for 10$"
    assert db_transaction_1.authorized_value == Decimal("20")
    assert db_transaction_2.message == "Credit Card"
    assert db_transaction_2.charged_value == Decimal("100")
    assert db_transaction_3.psp_reference == "PSP reference - 123"
    assert db_transaction_3.refunded_value == Decimal("15")
    assert db_transaction_4.canceled_value == Decimal("20")
    assert db_transaction_1.order_id == db_order.id
    assert db_transaction_2.order_id == db_order.id
    assert db_transaction_3.order_id == db_order.id
    assert db_transaction_4.order_id == db_order.id

    assert db_order.total_authorized_amount == Decimal("20")
    assert db_order.total_charged_amount == Decimal("100")
    assert db_order.authorize_status == OrderAuthorizeStatus.FULL.lower()
    assert db_order.charge_status == OrderChargeStatus.PARTIAL.lower()

    assert TransactionItem.objects.count() == transactions_count + 4


def test_order_bulk_create_transactions_with_multiple_amounts(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    transactions_count = TransactionItem.objects.count()

    transaction = {
        "amountAuthorized": {
            "amount": Decimal("10"),
            "currency": "PLN",
        },
        "amountCharged": {
            "amount": Decimal("100"),
            "currency": "PLN",
        },
        "amountRefunded": {
            "amount": Decimal("15"),
            "currency": "PLN",
        },
        "amountCanceled": {
            "amount": Decimal("20"),
            "currency": "PLN",
        },
    }

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    order_bulk_input["transactions"] = [transaction]

    variables = {
        "orders": [order_bulk_input],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]
    order = data[0]["order"]

    transaction = order["transactions"][0]
    assert transaction["authorizedAmount"]["amount"] == Decimal("10")
    assert transaction["authorizedAmount"]["currency"] == "PLN"
    assert transaction["chargedAmount"]["amount"] == Decimal("100")
    assert transaction["chargedAmount"]["currency"] == "PLN"
    assert transaction["refundedAmount"]["amount"] == Decimal("15")
    assert transaction["refundedAmount"]["currency"] == "PLN"
    assert transaction["canceledAmount"]["amount"] == Decimal("20")
    assert transaction["canceledAmount"]["currency"] == "PLN"

    db_order = Order.objects.get()
    db_transaction = TransactionItem.objects.get()
    assert db_transaction.authorized_value == Decimal("10")
    assert db_transaction.charged_value == Decimal("100")
    assert db_transaction.refunded_value == Decimal("15")
    assert db_transaction.canceled_value == Decimal("20")
    assert db_transaction.order_id == db_order.id

    assert db_order.total_authorized_amount == Decimal("10")
    assert db_order.total_charged_amount == Decimal("100")
    assert db_order.authorize_status == OrderAuthorizeStatus.PARTIAL.lower()
    assert db_order.charge_status == OrderChargeStatus.PARTIAL.lower()

    assert TransactionItem.objects.count() == transactions_count + 1


def test_order_bulk_create_multiple_invoices(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    invoices_count = Invoice.objects.count()

    invoice_1 = {
        "number": "01/12/2020/TEST",
        "createdAt": timezone.now(),
    }
    invoice_2 = {
        "url": "http://www.example2.com",
        "createdAt": timezone.now(),
    }
    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    order_bulk_input["invoices"] = [invoice_1, invoice_2]

    variables = {
        "orders": [order_bulk_input],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]

    order = data[0]["order"]
    invoice_1 = order["invoices"][0]
    assert invoice_1["number"] == "01/12/2020/TEST"
    assert invoice_1["url"] is None
    invoice_2 = order["invoices"][1]
    assert invoice_2["number"] is None
    assert invoice_2["url"] == "http://www.example2.com"

    db_order = Order.objects.get()
    db_invoice_1, db_invoice_2 = Invoice.objects.all()
    assert db_invoice_1.number == "01/12/2020/TEST"
    assert db_invoice_1.external_url is None
    assert db_invoice_1.order_id == db_order.id
    assert db_invoice_1.status == JobStatus.SUCCESS

    assert db_invoice_2.number is None
    assert db_invoice_2.external_url == "http://www.example2.com"
    assert db_invoice_2.order_id == db_order.id
    assert db_invoice_2.status == JobStatus.SUCCESS

    assert Invoice.objects.count() == invoices_count + 2


def test_order_bulk_create_multiple_discounts(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    discounts_count = OrderDiscount.objects.count()
    discount_1 = {
        "valueType": DiscountValueTypeEnum.FIXED.name,
        "value": 10,
    }
    discount_2 = {
        "valueType": DiscountValueTypeEnum.PERCENTAGE.name,
        "value": 101,
    }
    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    order_bulk_input["discounts"] = [discount_1, discount_2]

    variables = {
        "orders": [order_bulk_input],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert data[0]["errors"][0]["message"] == (
        "The percentage value (101) cannot be higher than 100."
    )

    order = data[0]["order"]
    discount_1, discount_2 = order["discounts"]
    assert discount_1["value"] == 10
    assert discount_1["valueType"] == DiscountValueTypeEnum.FIXED.name
    assert discount_2["value"] == 101
    assert discount_2["valueType"] == DiscountValueTypeEnum.PERCENTAGE.name

    db_order = Order.objects.get()
    db_discount_1, db_discount_2 = OrderDiscount.objects.all()
    assert db_discount_1.value_type == DiscountValueTypeEnum.FIXED.value
    assert db_discount_1.value == 10
    assert db_discount_1.order_id == db_order.id
    assert db_discount_2.value_type == DiscountValueTypeEnum.PERCENTAGE.value
    assert db_discount_2.value == 101
    assert db_discount_2.order_id == db_order.id

    assert OrderDiscount.objects.count() == discounts_count + 2


def test_order_bulk_create_stock_update(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    product_variant_list,
    warehouses,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments

    variant_1 = product_variant_list[0]
    variant_2 = product_variant_list[1]
    warehouse_1 = warehouses[0]
    warehouse_2 = warehouses[1]

    stock_variant_1_warehouse_1 = Stock(
        product_variant=variant_1, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_1 = Stock(
        product_variant=variant_2, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_2 = Stock(
        product_variant=variant_2, warehouse=warehouse_2, quantity=100
    )
    Stock.objects.bulk_create(
        [
            stock_variant_1_warehouse_1,
            stock_variant_2_warehouse_1,
            stock_variant_2_warehouse_2,
        ]
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]

    stock_variant_1_warehouse_1.refresh_from_db()
    stock_variant_2_warehouse_1.refresh_from_db()
    stock_variant_2_warehouse_2.refresh_from_db()

    assert stock_variant_1_warehouse_1.quantity == 90
    assert stock_variant_2_warehouse_1.quantity == 67
    assert stock_variant_2_warehouse_2.quantity == 83


def test_order_bulk_create_stock_update_insufficient_stock(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    product_variant_list,
    warehouses,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments

    variant_1 = product_variant_list[0]
    variant_2 = product_variant_list[1]
    warehouse_1 = warehouses[0]
    warehouse_2 = warehouses[1]

    stock_variant_1_warehouse_1 = Stock(
        product_variant=variant_1, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_1 = Stock(
        product_variant=variant_2, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_2 = Stock(
        product_variant=variant_2, warehouse=warehouse_2, quantity=5
    )
    Stock.objects.bulk_create(
        [
            stock_variant_1_warehouse_1,
            stock_variant_2_warehouse_1,
            stock_variant_2_warehouse_2,
        ]
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == (
        f"Insufficient stock for product variant: {variant_2.id} and warehouse: "
        f"{warehouse_2.id}."
    )
    assert error["path"] == "lines.2"
    assert error["code"] == OrderBulkCreateErrorCode.INSUFFICIENT_STOCK.name

    stock_variant_1_warehouse_1.refresh_from_db()
    stock_variant_2_warehouse_1.refresh_from_db()
    stock_variant_2_warehouse_2.refresh_from_db()

    assert stock_variant_1_warehouse_1.quantity == 100
    assert stock_variant_2_warehouse_1.quantity == 100
    assert stock_variant_2_warehouse_2.quantity == 5


def test_order_bulk_create_stock_update_insufficient_stock_with_force_update_policy(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    product_variant_list,
    warehouses,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments

    variant_1 = product_variant_list[0]
    variant_2 = product_variant_list[1]
    warehouse_1 = warehouses[0]
    warehouse_2 = warehouses[1]

    stock_variant_1_warehouse_1 = Stock(
        product_variant=variant_1, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_1 = Stock(
        product_variant=variant_2, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_2 = Stock(
        product_variant=variant_2, warehouse=warehouse_2, quantity=1
    )
    Stock.objects.bulk_create(
        [
            stock_variant_1_warehouse_1,
            stock_variant_2_warehouse_1,
            stock_variant_2_warehouse_2,
        ]
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.FORCE.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]

    stock_variant_1_warehouse_1.refresh_from_db()
    stock_variant_2_warehouse_1.refresh_from_db()
    stock_variant_2_warehouse_2.refresh_from_db()

    assert stock_variant_1_warehouse_1.quantity == 90
    assert stock_variant_2_warehouse_1.quantity == 67
    assert stock_variant_2_warehouse_2.quantity == -16


def test_order_bulk_create_stock_update_insufficient_stock_with_skip_update_policy(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    product_variant_list,
    warehouses,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments

    variant_1 = product_variant_list[0]
    variant_2 = product_variant_list[1]
    warehouse_1 = warehouses[0]
    warehouse_2 = warehouses[1]

    stock_variant_1_warehouse_1 = Stock(
        product_variant=variant_1, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_1 = Stock(
        product_variant=variant_2, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_2 = Stock(
        product_variant=variant_2, warehouse=warehouse_2, quantity=100
    )
    Stock.objects.bulk_create(
        [
            stock_variant_1_warehouse_1,
            stock_variant_2_warehouse_1,
            stock_variant_2_warehouse_2,
        ]
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["errors"]

    stock_variant_1_warehouse_1.refresh_from_db()
    stock_variant_2_warehouse_1.refresh_from_db()
    stock_variant_2_warehouse_2.refresh_from_db()

    assert stock_variant_1_warehouse_1.quantity == 100
    assert stock_variant_2_warehouse_1.quantity == 100
    assert stock_variant_2_warehouse_2.quantity == 100


def test_order_bulk_create_error_no_related_order_line_for_fulfillment(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    warehouse,
    variant,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    order["fulfillments"][0]["lines"][0]["orderLineIndex"] = 5

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["order"]

    error = data[0]["errors"][0]
    assert error["message"] == "There is no order line with index: 5."
    assert error["path"] == "fulfillments.0.lines.0.order_line_index"
    assert error["code"] == OrderBulkCreateErrorCode.NO_RELATED_ORDER_LINE.name


def test_order_bulk_create_error_warehouse_mismatch_between_order_and_fulfillment_lines(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    warehouse,
    variant,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    order["fulfillments"][0]["lines"][0]["warehouse"] = warehouse_id

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["order"]

    error = data[0]["errors"][0]
    assert error["message"] == (
        "Fulfillment line's warehouse is different then order line's warehouse."
    )
    assert error["path"] == "fulfillments.0.lines.0.warehouse"
    assert (
        error["code"]
        == OrderBulkCreateErrorCode.ORDER_LINE_FULFILLMENT_LINE_MISMATCH.name
    )


def test_order_bulk_create_error_variant_mismatch_between_order_and_fulfillment_lines(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    warehouse,
    variant,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    order["fulfillments"][0]["lines"][0]["variantId"] = variant_id

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["order"]

    error = data[0]["errors"][0]
    assert error["message"] == (
        "Fulfillment line's product variant is different "
        "then order line's product variant."
    )
    assert error["path"] == "fulfillments.0.lines.0.variant_id"
    assert (
        error["code"]
        == OrderBulkCreateErrorCode.ORDER_LINE_FULFILLMENT_LINE_MISMATCH.name
    )


def test_order_bulk_create_stock_update_error_too_many_fulfillments(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    product_variant_list,
    warehouses,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    order["fulfillments"][0]["lines"][0]["quantity"] = 500

    variant_1 = product_variant_list[0]
    variant_2 = product_variant_list[1]
    warehouse_1 = warehouses[0]
    warehouse_2 = warehouses[1]

    stock_variant_1_warehouse_1 = Stock(
        product_variant=variant_1, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_1 = Stock(
        product_variant=variant_2, warehouse=warehouse_1, quantity=100
    )
    stock_variant_2_warehouse_2 = Stock(
        product_variant=variant_2, warehouse=warehouse_2, quantity=100
    )
    Stock.objects.bulk_create(
        [
            stock_variant_1_warehouse_1,
            stock_variant_2_warehouse_1,
            stock_variant_2_warehouse_2,
        ]
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"] == f"There is more fulfillments, than ordered quantity "
        f"for order line with variant: {variant_1.id} and warehouse: {warehouse_1.id}"
    )
    assert error["path"] == "lines.0"
    assert error["code"] == OrderBulkCreateErrorCode.INVALID_QUANTITY.name


def test_order_bulk_create_update_stocks_missing_stocks(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
    product_variant_list,
    warehouses,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    variant = product_variant_list[0]
    warehouse = warehouses[0]

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.UPDATE.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"] == f"There is no stock for given product variant:"
        f" {variant.id} and warehouse: {warehouse.id}."
    )
    assert error["path"] == "lines.0"
    assert error["code"] == OrderBulkCreateErrorCode.NON_EXISTING_STOCK.name


@pytest.mark.parametrize(
    ("error_policy", "expected_order_count"),
    [
        (ErrorPolicyEnum.REJECT_EVERYTHING.name, 0),
        (ErrorPolicyEnum.REJECT_FAILED_ROWS.name, 1),
        (ErrorPolicyEnum.IGNORE_FAILED.name, 2),
    ],
)
def test_order_bulk_create_error_policy(
    error_policy,
    expected_order_count,
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
    app,
):
    # given
    orders_count = Order.objects.count()

    order_1 = order_bulk_input
    order_2 = copy.deepcopy(order_bulk_input)
    order_2["notes"][0]["appId"] = graphene.Node.to_global_id("App", app.id)

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "errorPolicy": error_policy,
        "orders": [order_1, order_2],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)

    # then
    assert Order.objects.count() == orders_count + expected_order_count


def test_order_bulk_create_no_permissions(
    staff_api_client,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()
    variables = {"orders": [order_bulk_input]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)

    # then
    assert_no_permission(response)
    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_order_future_date(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["createdAt"] = timezone.now() + timedelta(minutes=MINUTES_DIFF + 1)

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Order input contains future date."
    assert error["path"] == "created_at"
    assert error["code"] == OrderBulkCreateErrorCode.FUTURE_DATE.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_invalid_date_format(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    current_time = datetime.now() + timedelta(minutes=MINUTES_DIFF + 1)
    order["createdAt"] = current_time.strftime("%Y-%m-%dT%H:%M:%S")

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["orderBulkCreate"]["errors"][0]
    assert (
        error["message"] == "Input 'date' must be timezone-aware. "
        "Expected format: 'YYYY-MM-DD HH:MM:SS TZ'."
    )
    assert error["code"] == OrderBulkCreateErrorCode.INVALID.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_order_line_future_date(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["lines"][0]["createdAt"] = timezone.now() + timedelta(
        minutes=MINUTES_DIFF + 1
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Order line input contains future date."
    assert error["path"] == "lines.0.created_at"
    assert error["code"] == OrderBulkCreateErrorCode.FUTURE_DATE.name

    assert Order.objects.count() == orders_count + 1


def test_order_bulk_create_error_invalid_redirect_url(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["redirectUrl"] = "www.invalid-url.com"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"] == "Invalid redirect url: Invalid URL. "
        "Please check if URL is in RFC 1808 format.."
    )
    assert error["path"] == "redirect_url"
    assert error["code"] == OrderBulkCreateErrorCode.INVALID.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_negative_weight(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["weight"] = -5

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Order can't have negative weight."
    assert error["path"] == "weight"
    assert error["code"] == OrderBulkCreateErrorCode.INVALID.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_invalid_address(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["billingAddress"] = {"firstName": "John"}
    order["shippingAddress"] = {"postalCode": "abc-123"}

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error_1 = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error_1["message"] == "Invalid billing address."
    assert error_1["path"] == "billing_address"
    assert error_1["code"] == OrderBulkCreateErrorCode.INVALID.name

    error_2 = content["data"]["orderBulkCreate"]["results"][0]["errors"][1]
    assert error_2["message"] == "Invalid shipping address."
    assert error_2["path"] == "shipping_address"
    assert error_2["code"] == OrderBulkCreateErrorCode.INVALID.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_no_shipping_method_price(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["deliveryMethod"]["shippingPrice"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]

    db_order = Order.objects.get()
    assert db_order.shipping_price_net_amount == 10
    assert db_order.shipping_price_gross_amount == 12

    assert Order.objects.count() == orders_count + 1


def test_order_bulk_create_error_delivery_with_both_shipping_method_and_warehouse(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
    warehouse,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["deliveryMethod"]["warehouseId"] = graphene.Node.to_global_id(
        "Warehouse", warehouse.id
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Can't provide both warehouse and shipping method IDs."
    assert error["path"] == "delivery_method"
    assert error["code"] == OrderBulkCreateErrorCode.TOO_MANY_IDENTIFIERS.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_warehouse_delivery_method(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
    warehouse,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["deliveryMethod"]["warehouseId"] = graphene.Node.to_global_id(
        "Warehouse", warehouse.id
    )
    order["deliveryMethod"]["warehouseName"] = "Denormalized name"
    order["deliveryMethod"]["shippingMethodId"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]
    order = content["data"]["orderBulkCreate"]["results"][0]["order"]
    assert order["collectionPointName"] == "Denormalized name"

    db_order = Order.objects.get()
    assert db_order.collection_point == warehouse
    assert db_order.collection_point_name == "Denormalized name"
    assert not db_order.shipping_method

    assert Order.objects.count() == orders_count + 1


def test_order_bulk_create_error_no_delivery_method_provided(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["deliveryMethod"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "No delivery method provided."
    assert error["path"] == "delivery_method"
    assert error["code"] == OrderBulkCreateErrorCode.REQUIRED.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_note_with_future_date(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["notes"][0]["date"] = timezone.now() + timedelta(minutes=MINUTES_DIFF + 1)

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Note input contains future date."
    assert error["path"] == "notes.0.date"
    assert error["code"] == OrderBulkCreateErrorCode.FUTURE_DATE.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_note_exceeds_character_limit(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()
    events_count = OrderEvent.objects.count()

    order = order_bulk_input
    order["notes"][0]["message"] = "x" * (MAX_NOTE_LENGTH + 1)

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"] == f"Note message exceeds character limit: {MAX_NOTE_LENGTH}."
    )
    assert error["path"] == "notes.0.message"
    assert error["code"] == OrderBulkCreateErrorCode.NOTE_LENGTH.name

    assert Order.objects.count() == orders_count + 1
    assert OrderEvent.objects.count() == events_count


def test_order_bulk_create_error_non_existing_instance(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["lines"][0]["variantId"] = None
    order["lines"][0]["variantSku"] = "non-existing-sku"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]

    assert (
        errors[0]["message"]
        == "ProductVariant instance with sku=non-existing-sku doesn't exist."
    )
    assert errors[0]["path"] == "lines.0.variant_sku"
    assert errors[0]["code"] == OrderBulkCreateErrorCode.NOT_FOUND.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_instance_not_found(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["channel"] = "non-existing-channel"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"]
        == "Channel instance with slug=non-existing-channel doesn't exist."
    )
    assert error["path"] == "channel"
    assert error["code"] == OrderBulkCreateErrorCode.NOT_FOUND.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_get_instance_with_multiple_keys(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["user"]["email"] = "non-existing-user@example.com"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"] == "Only one of [id, email, external_reference] arguments"
        " can be provided to resolve User instance."
    )
    assert error["path"] == "user"
    assert error["code"] == OrderBulkCreateErrorCode.TOO_MANY_IDENTIFIERS.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_get_instance_with_no_keys(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["user"]["id"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"] == "One of [id, email, external_reference] arguments"
        " must be provided to resolve User instance."
    )
    assert error["path"] == "user"
    assert error["code"] == OrderBulkCreateErrorCode.REQUIRED.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_no_user_input_provided_ignore_failed_policy(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["user"]["id"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"] == "One of [id, email, external_reference] arguments"
        " must be provided to resolve User instance."
    )
    assert error["path"] == "user"
    assert error["code"] == OrderBulkCreateErrorCode.REQUIRED.name
    db_order = Order.objects.get()
    assert not db_order.user


def test_order_bulk_create_error_invalid_quantity(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["lines"][0]["quantity"] = 0.2

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]
    assert (
        errors[0]["message"] == "Invalid quantity. "
        "Must be integer greater then or equal to 1."
    )
    assert errors[0]["path"] == "lines.0.quantity"
    assert errors[0]["code"] == OrderBulkCreateErrorCode.INVALID_QUANTITY.name
    assert Order.objects.count() == orders_count


@pytest.mark.parametrize(
    (
        "quantity",
        "total_net",
        "total_gross",
        "undiscounted_net",
        "undiscounted_gross",
        "message",
        "code",
        "field",
    ),
    [
        (
            -5,
            100,
            120,
            200,
            240,
            "Invalid quantity. Must be integer greater then or equal to 1.",
            OrderBulkCreateErrorCode.INVALID_QUANTITY.name,
            "quantity",
        ),
        (
            5,
            120,
            100,
            200,
            240,
            "Net price can't be greater then gross price.",
            OrderBulkCreateErrorCode.PRICE_ERROR.name,
            "total_price",
        ),
        (
            5,
            100,
            120,
            240,
            120,
            "Net price can't be greater then gross price.",
            OrderBulkCreateErrorCode.PRICE_ERROR.name,
            "undiscounted_total_price",
        ),
        (
            5,
            200,
            240,
            100,
            120,
            "Total price can't be greater then undiscounted total price.",
            OrderBulkCreateErrorCode.PRICE_ERROR.name,
            "undiscounted_total_price",
        ),
    ],
)
def test_order_bulk_create_error_order_line_calculations(
    quantity,
    total_net,
    total_gross,
    undiscounted_net,
    undiscounted_gross,
    message,
    code,
    field,
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["lines"][0]["quantity"] = quantity
    order["lines"][0]["totalPrice"]["net"] = total_net
    order["lines"][0]["totalPrice"]["gross"] = total_gross
    order["lines"][0]["undiscountedTotalPrice"]["net"] = undiscounted_net
    order["lines"][0]["undiscountedTotalPrice"]["gross"] = undiscounted_gross

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]
    assert len(errors) == 1
    assert errors[0]["message"] == message
    assert errors[0]["path"] == f"lines.0.{field}"
    assert errors[0]["code"] == code

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_calculate_order_line_tax_rate(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["lines"][0]["taxRate"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderBulkCreate"]
    assert data["count"] == 1
    assert not data["results"][0]["errors"]
    assert data["results"][0]["order"]["lines"][0]["taxRate"] == 0.2

    db_line = OrderLine.objects.get()
    assert db_line.tax_rate == Decimal("0.2")

    assert Order.objects.count() == orders_count + 1


def test_order_bulk_create_quantize_prices(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["lines"][0]["quantity"] = 3
    order["lines"][0]["totalPrice"]["net"] = 10
    order["lines"][0]["undiscountedTotalPrice"]["net"] = 13
    order["lines"][0]["totalPrice"]["gross"] = 20
    order["lines"][0]["undiscountedTotalPrice"]["gross"] = 23

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    order = content["data"]["orderBulkCreate"]["results"][0]["order"]
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]
    assert order["lines"][0]["unitPrice"]["gross"]["amount"] == 6.67
    assert order["lines"][0]["unitPrice"]["net"]["amount"] == 3.33
    assert order["lines"][0]["undiscountedUnitPrice"]["gross"]["amount"] == 7.67
    assert order["lines"][0]["undiscountedUnitPrice"]["net"]["amount"] == 4.33
    assert order["lines"][0]["unitDiscount"]["amount"] == 1

    db_order_line = OrderLine.objects.get()
    assert db_order_line.unit_price.gross.amount == Decimal("6.67")
    assert db_order_line.unit_price.net.amount == Decimal("3.33")
    assert db_order_line.undiscounted_unit_price.gross.amount == Decimal("7.67")
    assert db_order_line.undiscounted_unit_price.net.amount == Decimal("4.33")
    assert db_order_line.unit_discount_amount == Decimal("1")


def test_order_bulk_create_error_currency_mismatch_between_transaction_and_order(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["transactions"][0]["amountAuthorized"]["currency"] = "USD"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Currency needs to be the same as for order: PLN"
    assert error["path"] == "transactions.0"
    assert error["code"] == OrderBulkCreateErrorCode.INCORRECT_CURRENCY.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_empty_transaction_metadata_key(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["transactions"][0]["metadata"] = [{"key": "", "value": "123"}]

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "metadata key cannot be empty."
    assert error["path"] == "transactions.0"
    assert error["code"] == OrderBulkCreateErrorCode.METADATA_KEY_REQUIRED.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_empty_order_line_tax_class_metadata_key(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["lines"][0]["taxClassMetadata"] = [{"key": "", "value": "123"}]
    order["lines"][0]["taxClassPrivateMetadata"] = [{"key": "", "value": "321"}]

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]
    assert errors[0]["message"] == "Metadata key cannot be empty."
    assert errors[0]["path"] == "lines.0.tax_class_metadata"
    assert errors[0]["code"] == OrderBulkCreateErrorCode.METADATA_KEY_REQUIRED.name
    assert errors[1]["message"] == "Metadata key cannot be empty."
    assert errors[1]["path"] == "lines.0.tax_class_private_metadata"
    assert errors[1]["code"] == OrderBulkCreateErrorCode.METADATA_KEY_REQUIRED.name

    db_order_line = OrderLine.objects.get()
    assert not db_order_line.tax_class_metadata
    assert not db_order_line.tax_class_private_metadata

    assert Order.objects.count() == orders_count + 1


def test_order_bulk_create_error_empty_shipping_tax_class_metadata_key(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["deliveryMethod"]["shippingTaxClassMetadata"] = [{"key": "", "value": "123"}]
    order["deliveryMethod"]["shippingTaxClassPrivateMetadata"] = [
        {"key": "", "value": "321"}
    ]

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]
    assert errors[0]["message"] == "Metadata key cannot be empty."
    assert errors[0]["path"] == "delivery_method.shipping_tax_class_metadata"
    assert errors[0]["code"] == OrderBulkCreateErrorCode.METADATA_KEY_REQUIRED.name
    assert errors[1]["message"] == "Metadata key cannot be empty."
    assert errors[1]["path"] == "delivery_method.shipping_tax_class_private_metadata"
    assert errors[1]["code"] == OrderBulkCreateErrorCode.METADATA_KEY_REQUIRED.name

    db_order = Order.objects.get()
    assert not db_order.shipping_tax_class_metadata
    assert not db_order.shipping_tax_class_private_metadata

    assert Order.objects.count() == orders_count + 1


def test_order_bulk_create_error_empty_invoice_metadata_key(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()
    invoice_count = Invoice.objects.count()

    order = order_bulk_input
    order["invoices"][0]["metadata"] = [{"key": "", "value": "123"}]
    order["invoices"][0]["privateMetadata"] = [{"key": "", "value": "321"}]

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]
    assert errors[0]["message"] == "Metadata key cannot be empty."
    assert errors[0]["path"] == "invoices.0.metadata"
    assert errors[0]["code"] == OrderBulkCreateErrorCode.METADATA_KEY_REQUIRED.name
    assert errors[1]["message"] == "Metadata key cannot be empty."
    assert errors[1]["path"] == "invoices.0.private_metadata"
    assert errors[1]["code"] == OrderBulkCreateErrorCode.METADATA_KEY_REQUIRED.name

    db_invoice = Invoice.objects.get()
    assert not db_invoice.metadata
    assert not db_invoice.private_metadata

    assert Order.objects.count() == orders_count + 1
    assert Invoice.objects.count() == invoice_count + 1


def test_order_bulk_create_error_invoice_future_date(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    invoice_count = Order.objects.count()

    order = order_bulk_input
    order["invoices"][0]["createdAt"] = timezone.now() + timedelta(
        minutes=MINUTES_DIFF + 1
    )

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Invoice input contains future date."
    assert error["path"] == "invoices.0.created_at"
    assert error["code"] == OrderBulkCreateErrorCode.FUTURE_DATE.name

    assert Invoice.objects.count() == invoice_count + 1


def test_order_bulk_create_error_invoice_invalid_url(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    invoice_count = Order.objects.count()

    order = order_bulk_input
    order["invoices"][0]["url"] = "invalid_url"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Invalid URL format."
    assert error["path"] == "invoices.0.url"
    assert error["code"] == OrderBulkCreateErrorCode.INVALID.name

    assert Invoice.objects.count() == invoice_count + 1


@pytest.mark.parametrize(
    ("value_type", "message"),
    [
        (
            DiscountValueTypeEnum.FIXED.name,
            "The value (999999) cannot be higher than 120 PLN",
        ),
        (
            DiscountValueTypeEnum.PERCENTAGE.name,
            "The percentage value (999999) cannot be higher than 100.",
        ),
    ],
)
def test_order_bulk_create_error_invalid_discount(
    value_type,
    message,
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    invoice_count = Order.objects.count()

    order = order_bulk_input
    order["discounts"][0]["valueType"] = value_type
    order["discounts"][0]["value"] = 999999

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == message
    assert error["path"] == "discounts.0"
    assert error["code"] == OrderBulkCreateErrorCode.INVALID.name

    assert Invoice.objects.count() == invoice_count + 1


def test_order_bulk_create_user_not_found_but_user_email_provided(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["user"]["id"] = None
    order["user"]["email"] = "new_email@example.com"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert content["data"]["orderBulkCreate"]["results"][0]["order"]
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]
    db_order = Order.objects.get()
    assert not db_order.user
    assert db_order.user_email == "new_email@example.com"


@pytest.mark.parametrize(
    ("status", "fulfillment_quantity", "is_invalid"),
    [
        (OrderStatusEnum.FULFILLED, 5, False),
        (OrderStatusEnum.UNFULFILLED, 0, False),
        (OrderStatusEnum.PARTIALLY_FULFILLED, 3, False),
        (OrderStatusEnum.FULFILLED, 3, True),
        (OrderStatusEnum.UNFULFILLED, 1, True),
        (OrderStatusEnum.PARTIALLY_FULFILLED, 5, True),
    ],
)
def test_order_bulk_create_validate_order_status(
    status,
    fulfillment_quantity,
    is_invalid,
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["status"] = status.name
    order["fulfillments"][0]["lines"][0]["quantity"] = fulfillment_quantity

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    if is_invalid:
        assert content["data"]["orderBulkCreate"]["count"] == 0
        error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
        assert error["code"] == OrderBulkCreateErrorCode.INVALID.name
        assert error["path"] == "status"
    else:
        assert content["data"]["orderBulkCreate"]["count"] == 1
        order = content["data"]["orderBulkCreate"]["results"][0]["order"]
        assert order["status"] == status.name.upper()


@patch("saleor.plugins.manager.PluginsManager.order_bulk_created")
def test_order_bulk_create_webhook(
    mocked_order_bulk_created,
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)

    # then
    db_order = Order.objects.get()
    mocked_order_bulk_created.assert_called_once_with([db_order])


def test_order_bulk_create_error_path_fulfillments(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    order["fulfillments"][1]["lines"][2]["warehouse"] = "dummy"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Invalid ID: dummy. Expected: Warehouse."
    assert error["path"] == "fulfillments.1.lines.2.warehouse"
    assert error["code"] == OrderBulkCreateErrorCode.INVALID.name


def test_order_bulk_create_error_path_order_lines(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    order["lines"][2]["variantId"] = "dummy"
    order["lines"][2]["variantSku"] = "dummy"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert (
        error["message"] == "Only one of [variant_id, variant_external_reference, "
        "variant_sku] arguments can be provided to resolve ProductVariant instance."
    )
    assert error["path"] == "lines.2"
    assert error["code"] == OrderBulkCreateErrorCode.TOO_MANY_IDENTIFIERS.name


def test_order_bulk_create_shipping_not_required(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    order["lines"][0]["isShippingRequired"] = False
    order["lines"][1]["isShippingRequired"] = False
    order["lines"][2]["isShippingRequired"] = False
    order["deliveryMethod"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]
    order = content["data"]["orderBulkCreate"]["results"][0]["order"]
    assert not order["shippingMethodName"]
    assert not order["collectionPointName"]
    assert order["shippingPrice"]["gross"]["amount"] == 0
    assert order["shippingPrice"]["net"]["amount"] == 0

    db_order = Order.objects.get()
    assert not db_order.shipping_method
    assert not db_order.shipping_method_name
    assert db_order.shipping_price_gross_amount == 0
    assert db_order.shipping_price_net_amount == 0


def test_order_bulk_create_error_missing_delivery_method(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input_with_multiple_order_lines_and_fulfillments,
):
    # given
    order = order_bulk_input_with_multiple_order_lines_and_fulfillments
    order["lines"][0]["isShippingRequired"] = False
    order["lines"][1]["isShippingRequired"] = False
    order["lines"][2]["isShippingRequired"] = False
    order["deliveryMethod"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]
    order = content["data"]["orderBulkCreate"]["results"][0]["order"]
    assert not order["shippingMethodName"]
    assert not order["collectionPointName"]
    assert order["shippingPrice"]["gross"]["amount"] == 0
    assert order["shippingPrice"]["net"]["amount"] == 0

    db_order = Order.objects.get()
    assert not db_order.shipping_method
    assert not db_order.shipping_method_name
    assert db_order.shipping_price_gross_amount == 0
    assert db_order.shipping_price_net_amount == 0


def test_order_bulk_create_optional_fields_set_to_none(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["notes"] = None
    order["fulfillments"] = None
    order["giftCards"] = None
    order["transactions"] = None
    order["invoices"] = None
    order["discounts"] = None
    order["customerNote"] = None
    order["weight"] = None
    order["lines"][0]["isShippingRequired"] = False
    order["deliveryMethod"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]


def test_order_bulk_create_optional_fields_set_to_none_nested_fields(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["notes"] = [{"message": "yo", "date": None}]
    order["fulfillments"][0]["trackingCode"] = None
    order["fulfillments"][0]["lines"] = None
    order["deliveryMethod"]["shippingTaxClassName"] = None
    order["deliveryMethod"]["shippingMethodName"] = None
    order["lines"][0]["productName"] = None
    order["lines"][0]["variantName"] = None
    order["lines"][0]["translatedProductName"] = None
    order["lines"][0]["translatedVariantName"] = None
    order["lines"][0]["taxClassName"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]


def test_order_bulk_create_error_external_reference_already_exist(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
    order,
):
    # given
    order.external_reference = "order-123"
    order.save(update_fields=["external_reference"])
    order_bulk_input["externalReference"] = "order-123"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order_bulk_input],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
        "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    data = content["data"]["orderBulkCreate"]["results"]
    assert not data[0]["order"]
    error = data[0]["errors"][0]
    assert (
        error["message"] == "Order with external_reference: order-123 already exists."
    )
    assert error["path"] == "external_reference"
    assert error["code"] == OrderBulkCreateErrorCode.UNIQUE.name


def test_order_bulk_create_error_currency_mismatch_between_channel_and_order(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    orders_count = Order.objects.count()

    order = order_bulk_input
    order["currency"] = "USD"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Currency from input doesn't match channel's currency."
    assert error["path"] == "currency"
    assert error["code"] == OrderBulkCreateErrorCode.INCORRECT_CURRENCY.name

    assert Order.objects.count() == orders_count


def test_order_bulk_create_error_non_existing_gift_card_code(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["giftCards"] = ["non-existing-code"]

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Gift card with code non-existing-code doesn't exist."
    assert error["path"] == "gift_cards.0"
    assert error["code"] == OrderBulkCreateErrorCode.NOT_FOUND.name


def test_order_bulk_create_error_negative_order_line_index(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["fulfillments"][0]["lines"][0]["orderLineIndex"] = -1

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Order line index can't be negative."
    assert error["path"] == "fulfillments.0.lines.0.order_line_index"
    assert error["code"] == OrderBulkCreateErrorCode.NEGATIVE_INDEX.name


@pytest.mark.parametrize(
    ("status", "order_quantity", "fulfillment_quantity"),
    [
        (OrderStatusEnum.PARTIALLY_FULFILLED.name, 5, 0),
        (OrderStatusEnum.PARTIALLY_FULFILLED.name, 5, 5),
        (OrderStatusEnum.UNFULFILLED.name, 5, 4),
        (OrderStatusEnum.UNFULFILLED.name, 5, 5),
        (OrderStatusEnum.FULFILLED.name, 5, 0),
        (OrderStatusEnum.FULFILLED.name, 5, 4),
    ],
)
def test_order_bulk_create_error_invalid_status(
    status,
    order_quantity,
    fulfillment_quantity,
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
):
    # given
    order = order_bulk_input
    order["status"] = status
    order["lines"][0]["quantity"] = order_quantity
    order["fulfillments"][0]["lines"][0]["quantity"] = fulfillment_quantity

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Invalid order status."
    assert error["path"] == "status"
    assert error["code"] == OrderBulkCreateErrorCode.INVALID.name


def test_order_bulk_create_skip_address_validation(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
    graphql_address_data_skipped_validation,
):
    # given
    order = order_bulk_input
    invalid_postal_code = "invalid_postal_code"
    address_data = graphql_address_data_skipped_validation
    address_data["postalCode"] = invalid_postal_code
    order["billingAddress"] = address_data
    order["shippingAddress"] = address_data

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {
        "orders": [order],
        "stockUpdatePolicy": StockUpdatePolicyEnum.SKIP.name,
    }

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["orderBulkCreate"]["results"][0]
    assert not data["errors"]
    assert data["order"]["shippingAddress"]["postalCode"] == invalid_postal_code
    assert data["order"]["billingAddress"]["postalCode"] == invalid_postal_code
    db_order = Order.objects.last()
    assert db_order.shipping_address.postal_code == invalid_postal_code
    assert db_order.shipping_address.validation_skipped is True
    assert db_order.billing_address.postal_code == invalid_postal_code
    assert db_order.billing_address.validation_skipped is True
