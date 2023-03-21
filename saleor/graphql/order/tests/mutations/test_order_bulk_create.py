import copy
from datetime import timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone

from .....account.models import Address
from .....order import OrderEvents, OrderOrigin, OrderStatus
from .....order.error_codes import OrderBulkCreateErrorCode
from .....order.models import Order, OrderEvent, OrderLine
from ....core.enums import ErrorPolicyEnum
from ....tests.utils import assert_no_permission, get_graphql_content
from ...bulk_mutations.order_bulk_create import MAX_NOTE_LENGTH, MINUTES_DIFF

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
                    user {
                        id
                        email
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
                    }
                    shippingAddress{
                        postalCode
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
        "shippingTaxClassId": graphene.Node.to_global_id(
            "TaxClass", default_tax_class.id
        ),
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
        "quantityFulfilled": 0,
        "totalPrice": {
            "gross": 120,
            "net": 100,
        },
        "undiscountedTotalPrice": {
            "gross": 120,
            "net": 100,
        },
        "taxRate": 0.2,
        "taxClassId": graphene.Node.to_global_id("TaxClass", default_tax_class.id),
        "taxClassName": "Line Tax Class Name",
        "taxClassMetadata": [
            {
                "key": "md key",
                "value": "md value",
            }
        ],
        "taxClassPrivateMetadata": [
            {
                "key": "pmd key",
                "value": "pmd value",
            }
        ],
    }
    note = {
        "message": "Test message",
        "date": timezone.now(),
        "userId": graphene.Node.to_global_id("User", customer_user.id),
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
        "trackingClientId": "tracking-id-123",
        "redirectUrl": "https://www.example.com",
    }


# TODO split this test
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
):
    # given
    orders_count = Order.objects.count()
    order_lines_count = OrderLine.objects.count()
    order_events_count = OrderEvent.objects.count()
    address_count = Address.objects.count()

    order = order_bulk_input
    order["externalReference"] = "ext-ref-1"

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {"orders": [order]}

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
    assert not order["collectionPointName"]
    assert order["shippingMethodName"] == shipping_method_channel_PLN.name
    assert order["shippingTaxClassName"] == default_tax_class.name
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
    assert order["trackingClientId"] == "tracking-id-123"
    assert order["displayGrossPrices"]
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
    assert db_order.shipping_method_name == shipping_method_channel_PLN.name
    assert db_order.shipping_tax_class == default_tax_class
    assert db_order.shipping_tax_class_name == default_tax_class.name
    assert db_order.shipping_tax_rate == Decimal("0.2")
    assert db_order.shipping_tax_class_metadata["md key"] == "md value"
    assert db_order.shipping_tax_class_private_metadata["pmd key"] == "pmd value"
    assert db_order.shipping_price_gross_amount == 120
    assert db_order.shipping_price_net_amount == 100
    assert db_order.total_gross_amount == 120
    assert db_order.total_net_amount == 100
    assert db_order.undiscounted_total_gross_amount == 120
    assert db_order.undiscounted_total_net_amount == 100
    assert db_order.redirect_url == "https://www.example.com"
    assert db_order.origin == OrderOrigin.BULK_CREATE
    assert db_order.weight.g == 10.15 * 1000
    assert db_order.tracking_client_id == "tracking-id-123"
    assert db_order.display_gross_prices
    assert db_order.currency == "PLN"

    line = order["lines"][0]
    assert line["variant"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", variant.id
    )
    assert line["productName"] == "Product Name"
    assert line["variantName"] == "Variant Name"
    assert line["translatedProductName"] == "Nazwa Produktu"
    assert line["translatedVariantName"] == "Nazwa Wariantu"
    assert line["isShippingRequired"]
    assert line["quantity"] == 5
    assert line["quantityFulfilled"] == 0
    assert line["unitPrice"]["gross"]["amount"] == Decimal(120 / 5)
    assert line["unitPrice"]["net"]["amount"] == Decimal(100 / 5)
    assert line["undiscountedUnitPrice"]["gross"]["amount"] == Decimal(120 / 5)
    assert line["undiscountedUnitPrice"]["net"]["amount"] == Decimal(100 / 5)
    assert line["totalPrice"]["gross"]["amount"] == 120
    assert line["totalPrice"]["net"]["amount"] == 100
    assert line["taxClass"]["id"] == graphene.Node.to_global_id(
        "TaxClass", default_tax_class.id
    )
    assert line["taxClassName"] == "Line Tax Class Name"
    assert line["taxRate"] == 0.2
    assert line["taxClassMetadata"][0]["key"] == "md key"
    assert line["taxClassMetadata"][0]["value"] == "md value"
    assert line["taxClassPrivateMetadata"][0]["key"] == "pmd key"
    assert line["taxClassPrivateMetadata"][0]["value"] == "pmd value"
    db_line = OrderLine.objects.get()
    assert db_line.variant == variant
    assert db_line.product_name == "Product Name"
    assert db_line.variant_name == "Variant Name"
    assert db_line.translated_product_name == "Nazwa Produktu"
    assert db_line.translated_variant_name == "Nazwa Wariantu"
    assert db_line.is_shipping_required
    assert db_line.quantity == 5
    assert db_line.quantity_fulfilled == 0
    assert db_line.unit_price.gross.amount == Decimal(120 / 5)
    assert db_line.unit_price.net.amount == Decimal(100 / 5)
    assert db_line.undiscounted_unit_price.gross.amount == Decimal(120 / 5)
    assert db_line.undiscounted_unit_price.net.amount == Decimal(100 / 5)
    assert db_line.total_price.gross.amount == 120
    assert db_line.total_price.net.amount == 100
    assert db_line.undiscounted_total_price.gross.amount == 120
    assert db_line.undiscounted_total_price.net.amount == 100
    assert db_line.tax_class == default_tax_class
    assert db_line.tax_class_name == "Line Tax Class Name"
    assert db_line.tax_rate == Decimal("0.2")
    assert db_line.tax_class_metadata["md key"] == "md value"
    assert db_line.tax_class_private_metadata["pmd key"] == "pmd value"
    assert db_line.currency == "PLN"
    assert db_order.lines.first() == db_line

    assert order["billingAddress"]["postalCode"] == graphql_address_data["postalCode"]
    assert order["shippingAddress"]["postalCode"] == graphql_address_data["postalCode"]
    assert db_order.billing_address.postal_code == graphql_address_data["postalCode"]
    assert db_order.shipping_address.postal_code == graphql_address_data["postalCode"]

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

    assert Order.objects.count() == orders_count + 1
    assert OrderLine.objects.count() == order_lines_count + 1
    assert Address.objects.count() == address_count + 2
    assert OrderEvent.objects.count() == order_events_count + 1


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


def test_order_bulk_create_multiple_lines(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    order_bulk_input,
    product_variant_list,
):
    # given
    orders_count = Order.objects.count()
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
    variables = {"orders": [order]}

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

    assert Order.objects.count() == orders_count + 1
    assert OrderLine.objects.count() == lines_count + 2


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
    orders_count = Order.objects.count()
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

    variables = {"orders": [order_bulk_input]}

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

    assert Order.objects.count() == orders_count + 1
    assert OrderEvent.objects.count() == events_count + 2


@pytest.mark.parametrize(
    "error_policy,expected_order_count",
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
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Order input contains future date."
    assert error["field"] == "createdAt"
    assert error["code"] == OrderBulkCreateErrorCode.FUTURE_DATE.name

    assert Order.objects.count() == orders_count


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
    variables = {"orders": [order]}

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
    assert error["field"] == "redirectUrl"
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
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error_1 = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error_1["message"] == "Invalid billing address."
    assert error_1["field"] == "billingAddress"
    assert error_1["code"] == OrderBulkCreateErrorCode.INVALID.name

    error_2 = content["data"]["orderBulkCreate"]["results"][0]["errors"][1]
    assert error_2["message"] == "Invalid shipping address."
    assert error_2["field"] == "shippingAddress"
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
    variables = {"orders": [order]}

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
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Can't provide both warehouse and shipping method IDs."
    assert error["field"] == "deliveryMethod"
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
    order["deliveryMethod"]["shippingMethodId"] = None

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
    )
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 1
    assert not content["data"]["orderBulkCreate"]["results"][0]["errors"]
    order = content["data"]["orderBulkCreate"]["results"][0]["order"]
    assert order["collectionPointName"] == warehouse.name
    assert not order["shippingMethodName"]

    db_order = Order.objects.get()
    assert db_order.collection_point == warehouse
    assert db_order.collection_point_name == warehouse.name
    assert not db_order.shipping_method
    assert not db_order.shipping_method_name

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
    order["deliveryMethod"]["shippingMethodId"] = None

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
    assert error["message"] == "No delivery method provided."
    assert error["field"] == "deliveryMethod"
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
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    error = content["data"]["orderBulkCreate"]["results"][0]["errors"][0]
    assert error["message"] == "Note input contains future date."
    assert error["field"] == "date"
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
    variables = {"orders": [order], "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name}

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
    assert error["field"] == "message"
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
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]

    assert errors[0]["message"] == "At least one order line can't be created."
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == OrderBulkCreateErrorCode.ORDER_LINE_ERROR.name

    assert (
        errors[1]["message"]
        == "ProductVariant instance with sku=non-existing-sku doesn't exist."
    )
    assert not errors[1]["field"]
    assert errors[1]["code"] == OrderBulkCreateErrorCode.NOT_FOUND.name

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
    order["user"]["email"] = "non-existing-user@example.com"
    order["user"]["id"] = None

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
    assert (
        error["message"]
        == "User instance with email=non-existing-user@example.com doesn't exist."
    )
    assert not error["field"]
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
    variables = {"orders": [order]}

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
    assert not error["field"]
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
    variables = {"orders": [order]}

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
    assert not error["field"]
    assert error["code"] == OrderBulkCreateErrorCode.REQUIRED.name

    assert Order.objects.count() == orders_count


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
    variables = {"orders": [order]}

    # when
    response = staff_api_client.post_graphql(ORDER_BULK_CREATE, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["orderBulkCreate"]["count"] == 0
    assert not content["data"]["orderBulkCreate"]["results"][0]["order"]
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]
    assert errors[1]["message"] == "Invalid quantity; must be integer greater then 1."
    assert errors[1]["field"] == "quantity"
    assert errors[1]["code"] == OrderBulkCreateErrorCode.INVALID_QUANTITY.name

    assert errors[0]["message"] == "At least one order line can't be created."
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == OrderBulkCreateErrorCode.ORDER_LINE_ERROR.name
    assert Order.objects.count() == orders_count


# 5, 0, 0.2, 100, 100
@pytest.mark.parametrize(
    "quantity,quantity_fulfilled,total_net,undiscounted_net,message,code,field",
    [
        (
            -5,
            0,
            100,
            100,
            "Invalid quantity; must be integer greater then 1.",
            OrderBulkCreateErrorCode.INVALID_QUANTITY.name,
            "quantity",
        ),
        (
            5,
            -2,
            100,
            100,
            "Invalid quantity; must be integer greater then 0.",
            OrderBulkCreateErrorCode.INVALID_QUANTITY.name,
            "quantityFulfilled",
        ),
        (
            5,
            7,
            100,
            100,
            "Quantity fulfilled can't be greater then quantity.",
            OrderBulkCreateErrorCode.INVALID_QUANTITY.name,
            "quantityFulfilled",
        ),
        (
            5,
            0,
            300,
            100,
            "Net price can't be greater then gross price.",
            OrderBulkCreateErrorCode.PRICE_ERROR.name,
            "totalPrice",
        ),
        (
            5,
            0,
            100,
            300,
            "Net price can't be greater then gross price.",
            OrderBulkCreateErrorCode.PRICE_ERROR.name,
            "undiscountedTotalPrice",
        ),
    ],
)
def test_order_bulk_create_error_order_line_calculations(
    quantity,
    quantity_fulfilled,
    total_net,
    undiscounted_net,
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
    order["lines"][0]["quantityFulfilled"] = quantity_fulfilled
    order["lines"][0]["totalPrice"]["net"] = total_net
    order["lines"][0]["undiscountedTotalPrice"]["net"] = undiscounted_net

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
    errors = content["data"]["orderBulkCreate"]["results"][0]["errors"]
    assert errors[1]["message"] == message
    assert errors[1]["field"] == field
    assert errors[1]["code"] == code

    assert errors[0]["message"] == "At least one order line can't be created."
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == OrderBulkCreateErrorCode.ORDER_LINE_ERROR.name
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
    variables = {"orders": [order]}

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
