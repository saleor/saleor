from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import graphene
import pytest
import pytz
from prices import Money

from .....checkout import AddressType
from .....core.prices import quantize_price
from .....core.taxes import TaxError, zero_taxed_money
from .....discount import DiscountType, DiscountValueType, RewardType, RewardValueType
from .....discount.models import VoucherChannelListing, VoucherCustomer
from .....order import OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....order.models import Order, OrderEvent
from .....payment.model_helpers import get_subtotal
from .....product.models import ProductVariant
from .....tax import TaxCalculationStrategy
from .....tests.utils import round_up
from ....tests.utils import assert_no_permission, get_graphql_content

DRAFT_ORDER_CREATE_MUTATION = """
    mutation draftCreate(
            $input: DraftOrderCreateInput!
        ) {
            draftOrderCreate(
                input: $input
            ) {
                errors {
                    field
                    code
                    variants
                    message
                    addressType
                }
                order {
                    id
                    discount {
                        amount
                    }
                    discountName
                    discounts {
                        amount {
                            amount
                        }
                        valueType
                        type
                        reason
                    }
                    redirectUrl
                    billingAddress{
                        city
                        streetAddress1
                        postalCode
                        metadata {
                            key
                            value
                        }
                    }
                    shippingAddress{
                        city
                        streetAddress1
                        postalCode
                        metadata {
                            key
                            value
                        }
                    }
                    status
                    voucher {
                        code
                    }
                    voucherCode
                    customerNote
                    total {
                        gross {
                            amount
                        }
                    }
                    subtotal {
                        gross {
                            amount
                        }
                    }
                    undiscountedTotal {
                        gross {
                            amount
                        }
                    }
                    shippingPrice {
                        gross {
                            amount
                        }
                    }
                    shippingMethodName
                    externalReference
                    lines {
                        productVariantId
                        quantity
                        unitDiscount {
                          amount
                        }
                        undiscountedUnitPrice {
                            gross {
                                amount
                            }
                        }
                        unitPrice {
                            gross {
                                amount
                            }
                        }
                        totalPrice {
                            gross {
                                amount
                            }
                        }
                        unitDiscountReason
                        unitDiscountType
                        unitDiscountValue
                        isGift
                        isPriceOverridden
                    }
                }
            }
        }
    """


def test_draft_order_create_with_voucher_entire_order(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    channel_listing_0 = variant_0.channel_listings.get(channel=channel_USD)
    variant_0_qty = 2

    variant_1 = product_without_shipping.variants.first()
    variant_1_qty = 1
    channel_listing_1 = variant_1.channel_listings.get(channel=channel_USD)

    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": variant_0_qty},
        {"variantId": variant_1_id, "quantity": variant_1_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    voucher_listing = voucher.channel_listings.get(channel=channel_USD)

    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"

    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
            "externalReference": external_reference,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    assert not content["data"]["draftOrderCreate"]["errors"]
    stored_metadata = {"public": "public_value"}
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["voucherCode"] == voucher.code
    assert data["customerNote"] == customer_note
    assert data["redirectUrl"] == redirect_url
    assert data["externalReference"] == external_reference
    assert (
        data["billingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert (
        data["shippingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert data["billingAddress"]["metadata"] == graphql_address_data["metadata"]
    assert data["shippingAddress"]["metadata"] == graphql_address_data["metadata"]
    shipping_total = shipping_method.channel_listings.get(
        channel=channel_USD
    ).get_total()
    order_total = (
        channel_listing_0.discounted_price_amount * variant_0_qty
        + channel_listing_1.discounted_price_amount * variant_1_qty
        + shipping_total.amount
    )
    assert data["undiscountedTotal"]["gross"]["amount"] == order_total
    assert (
        data["total"]["gross"]["amount"] == order_total - voucher_listing.discount_value
    )

    order = Order.objects.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["subtotal"]["gross"]["amount"] == subtotal.gross.amount

    assert order.voucher_code == voucher.code
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.shipping_method_name == shipping_method.name
    assert order.billing_address
    assert order.shipping_address
    assert order.billing_address.metadata == stored_metadata
    assert order.shipping_address.metadata == stored_metadata
    assert order.billing_address.validation_skipped is False
    assert order.shipping_address.validation_skipped is False
    assert order.search_vector
    assert order.external_reference == external_reference
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    assert order.base_shipping_price == shipping_total

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}

    # Ensure the order_added_products_event was created properly
    added_products_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.ADDED_PRODUCTS
    )
    event_parameters = added_products_event.parameters
    assert event_parameters
    assert len(event_parameters["lines"]) == 2

    order_lines = list(order.lines.all())
    assert event_parameters["lines"][0]["item"] == str(order_lines[0])
    assert event_parameters["lines"][0]["line_pk"] == str(order_lines[0].pk)
    assert event_parameters["lines"][0]["quantity"] == 2

    assert event_parameters["lines"][1]["item"] == str(order_lines[1])
    assert event_parameters["lines"][1]["line_pk"] == str(order_lines[1].pk)
    assert event_parameters["lines"][1]["quantity"] == 1

    # Ensure order discount object was properly created
    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.voucher == voucher
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.value == voucher_listing.discount_value
    assert order_discount.amount_value == voucher_listing.discount_value

    for line in order_lines:
        assert line.is_price_overridden is False


def test_draft_order_create_with_voucher_and_voucher_code(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_0_qty = 2
    variant_1 = product_without_shipping.variants.first()
    variant_1_qty = 1
    variant_1.quantity = variant_1_qty
    variant_1.save()

    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": variant_0_qty},
        {"variantId": variant_1_id, "quantity": variant_1_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"

    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "voucherCode": voucher.codes.first().code,
            "customerNote": customer_note,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
            "externalReference": external_reference,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["field"] == "voucher"
    assert error["code"] == OrderErrorCode.INVALID.name
    assert (
        error["message"]
        == "You cannot use both a voucher and a voucher code for the same order. "
        "Please choose one."
    )


def test_draft_order_create_with_voucher_code_in_voucher_input(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_0_qty = 2
    variant_1 = product_without_shipping.variants.first()
    variant_1_qty = 1
    variant_1.quantity = variant_1_qty
    variant_1.save()

    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": variant_0_qty},
        {"variantId": variant_1_id, "quantity": variant_1_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_code_id = graphene.Node.to_global_id(
        "VoucherCode", voucher.codes.first().pk
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"

    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_code_id,
            "customerNote": customer_note,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
            "externalReference": external_reference,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["field"] == "voucher"
    assert error["code"] == OrderErrorCode.INVALID_VOUCHER.name
    assert (
        error["message"] == "You cannot use voucherCode in the voucher input. "
        "Please use voucherCode input instead with a valid voucher code."
    )


def test_draft_order_create_with_voucher_code(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    voucher_code = voucher.codes.first()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    channel_listing_0 = variant_0.channel_listings.get(channel=channel_USD)
    variant_0_qty = 2

    variant_1 = product_without_shipping.variants.first()
    variant_1_qty = 1
    channel_listing_1 = variant_1.channel_listings.get(channel=channel_USD)

    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_0_id, "quantity": variant_0_qty},
        {"variantId": variant_1_id, "quantity": variant_1_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    voucher_listing = voucher.channel_listings.get(channel=channel_USD)

    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"

    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucherCode": voucher_code.code,
            "customerNote": customer_note,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
            "externalReference": external_reference,
        }
    }
    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    stored_metadata = {"public": "public_value"}
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["voucherCode"] == voucher.code
    assert data["customerNote"] == customer_note
    assert data["redirectUrl"] == redirect_url
    assert data["externalReference"] == external_reference
    assert (
        data["billingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert (
        data["shippingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert data["billingAddress"]["metadata"] == graphql_address_data["metadata"]
    assert data["shippingAddress"]["metadata"] == graphql_address_data["metadata"]
    shipping_total = shipping_method.channel_listings.get(
        channel=channel_USD
    ).get_total()
    order_total = (
        channel_listing_0.discounted_price_amount * variant_0_qty
        + channel_listing_1.discounted_price_amount * variant_1_qty
        + shipping_total.amount
    )
    assert data["undiscountedTotal"]["gross"]["amount"] == order_total
    assert (
        data["total"]["gross"]["amount"] == order_total - voucher_listing.discount_value
    )

    order = Order.objects.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.voucher_code == voucher.code
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.shipping_method_name == shipping_method.name
    assert order.billing_address
    assert order.shipping_address
    assert order.billing_address.metadata == stored_metadata
    assert order.shipping_address.metadata == stored_metadata
    assert order.search_vector
    assert order.external_reference == external_reference
    assert order.base_shipping_price == shipping_total

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}

    # Ensure the order_added_products_event was created properly
    added_products_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.ADDED_PRODUCTS
    )
    event_parameters = added_products_event.parameters
    assert event_parameters
    assert len(event_parameters["lines"]) == 2

    order_lines = list(order.lines.all())
    assert event_parameters["lines"][0]["item"] == str(order_lines[0])
    assert event_parameters["lines"][0]["line_pk"] == str(order_lines[0].pk)
    assert event_parameters["lines"][0]["quantity"] == 2

    assert event_parameters["lines"][1]["item"] == str(order_lines[1])
    assert event_parameters["lines"][1]["line_pk"] == str(order_lines[1].pk)
    assert event_parameters["lines"][1]["quantity"] == 1

    # Ensure order discount object was properly created
    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.voucher == voucher
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.value == voucher_listing.discount_value
    assert order_discount.amount_value == voucher_listing.discount_value


def test_draft_order_create_percentage_voucher(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    shipping_method,
    variant,
    voucher_percentage,
    channel_USD,
    graphql_address_data,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_qty = 2

    variant_list = [
        {"variantId": variant_id, "quantity": variant_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_listing = voucher_percentage.channel_listings.get(channel=channel_USD)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher_percentage.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher_percentage.code
    assert data["redirectUrl"] == redirect_url
    assert (
        data["billingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert (
        data["shippingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert data["billingAddress"]["metadata"] == graphql_address_data["metadata"]
    assert data["shippingAddress"]["metadata"] == graphql_address_data["metadata"]
    shipping_total = shipping_method.channel_listings.get(
        channel=channel_USD
    ).get_total()
    subtotal = channel_listing.discounted_price_amount * variant_qty
    assert (
        data["undiscountedTotal"]["gross"]["amount"] == subtotal + shipping_total.amount
    )
    discount_amount = subtotal * voucher_listing.discount_value / 100
    assert (
        data["total"]["gross"]["amount"]
        == subtotal - discount_amount + shipping_total.amount
    )

    order = Order.objects.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.shipping_method_name == shipping_method.name
    assert order.base_shipping_price == shipping_total

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}

    # Ensure the order_added_products_event was created properly
    added_products_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.ADDED_PRODUCTS
    )
    event_parameters = added_products_event.parameters
    assert event_parameters
    assert len(event_parameters["lines"]) == 1

    order_line = order.lines.first()
    assert event_parameters["lines"][0]["item"] == str(order_line)
    assert event_parameters["lines"][0]["line_pk"] == str(order_line.pk)
    assert event_parameters["lines"][0]["quantity"] == variant_qty

    # Ensure order discount object was properly created
    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.voucher == voucher_percentage
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.PERCENTAGE
    assert order_discount.value == voucher_listing.discount_value
    assert order_discount.amount_value == discount_amount


def test_draft_order_create_with_voucher_specific_product(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher_specific_product_type,
    channel_USD,
    graphql_address_data,
):
    # given
    discounted_variant = variant
    voucher = voucher_specific_product_type
    code = voucher.codes.first().code
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", discounted_variant.id)
    discounted_variant_listing = discounted_variant.channel_listings.get(
        channel=channel_USD
    )
    variant_0_qty = 2

    variant_1 = product_without_shipping.variants.first()
    variant_1_qty = 1
    channel_listing_1 = variant_1.channel_listings.get(channel=channel_USD)

    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_list = [
        {"variantId": variant_0_id, "quantity": variant_0_qty},
        {"variantId": variant_1_id, "quantity": variant_1_qty},
    ]
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    voucher_listing = voucher.channel_listings.get(channel=channel_USD)
    discount_value = voucher_listing.discount_value

    shipping_address = graphql_address_data
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucherCode": code,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == code
    assert data["voucherCode"] == code
    assert data["redirectUrl"] == redirect_url

    shipping_total = shipping_method.channel_listings.get(
        channel=channel_USD
    ).get_total()
    discount_amount = (
        discounted_variant_listing.discounted_price_amount
        * variant_0_qty
        * discount_value
        / 100
    )
    discounted_variant_total = (
        discounted_variant_listing.discounted_price_amount * variant_0_qty
        - discount_amount
    )
    variant_1_total = channel_listing_1.discounted_price_amount * variant_1_qty
    order_total = discounted_variant_total + variant_1_total + shipping_total.amount
    assert data["undiscountedTotal"]["gross"]["amount"] == order_total + discount_amount
    assert data["total"]["gross"]["amount"] == order_total

    order = Order.objects.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["subtotal"]["gross"]["amount"] == subtotal.gross.amount

    assert order.voucher_code == voucher.code
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.shipping_method_name == shipping_method.name
    assert order.search_vector
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    assert order.base_shipping_price == shipping_total

    lines_data = data["lines"]
    discounted_line_data, line_1_data = lines_data
    assert discounted_line_data["productVariantId"] == variant_0_id
    assert discounted_line_data["quantity"] == variant_0_qty
    assert (
        discounted_line_data["unitPrice"]["gross"]["amount"]
        == discounted_variant_total / variant_0_qty
    )
    assert (
        discounted_line_data["totalPrice"]["gross"]["amount"]
        == discounted_variant_total
    )
    assert (
        discounted_line_data["unitDiscount"]["amount"]
        == discount_amount / variant_0_qty
    )
    assert discounted_line_data["unitDiscountType"] == DiscountValueType.FIXED.upper()
    assert discounted_line_data["unitDiscountReason"] == f"Voucher code: {code}"

    assert line_1_data["productVariantId"] == variant_1_id
    assert line_1_data["quantity"] == variant_1_qty
    assert (
        line_1_data["unitPrice"]["gross"]["amount"] == variant_1_total / variant_1_qty
    )
    assert line_1_data["totalPrice"]["gross"]["amount"] == variant_1_total
    assert line_1_data["unitDiscount"]["amount"] == 0
    assert line_1_data["unitDiscountType"] is None
    assert line_1_data["unitDiscountReason"] is None

    # TODO (SHOPX-874): Order discount object shouldn't be created
    assert order.discounts.count() == 1

    discounted_line = order.lines.get(variant=discounted_variant)
    assert discounted_line.discounts.count() == 1
    order_line_discount = discounted_line.discounts.first()
    assert order_line_discount.voucher == voucher
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.value_type == DiscountValueType.FIXED
    assert order_line_discount.value == discount_amount
    assert order_line_discount.amount_value == discount_amount


def test_draft_order_create_with_voucher_apply_once_per_order(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher_percentage,
    channel_USD,
    graphql_address_data,
):
    # given
    discounted_variant = variant
    voucher = voucher_percentage
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["apply_once_per_order"])
    code = voucher.codes.first().code

    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", discounted_variant.id)
    discounted_variant_listing = discounted_variant.channel_listings.get(
        channel=channel_USD
    )
    variant_0_qty = 2

    variant_1 = product_without_shipping.variants.first()
    variant_1_qty = 1
    channel_listing_1 = variant_1.channel_listings.get(channel=channel_USD)

    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_list = [
        {"variantId": variant_0_id, "quantity": variant_0_qty},
        {"variantId": variant_1_id, "quantity": variant_1_qty},
    ]
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    voucher_listing = voucher.channel_listings.get(channel=channel_USD)
    discount_value = voucher_listing.discount_value

    shipping_address = graphql_address_data
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucherCode": code,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == code
    assert data["voucherCode"] == code
    assert data["redirectUrl"] == redirect_url

    shipping_total = shipping_method.channel_listings.get(
        channel=channel_USD
    ).get_total()
    discount_amount = (
        discounted_variant_listing.discounted_price_amount * discount_value / 100
    )
    discounted_variant_total = (
        discounted_variant_listing.discounted_price_amount * variant_0_qty
        - discount_amount
    )
    variant_1_total = channel_listing_1.discounted_price_amount * variant_1_qty
    order_total = discounted_variant_total + variant_1_total + shipping_total.amount
    assert data["undiscountedTotal"]["gross"]["amount"] == order_total + discount_amount
    assert data["total"]["gross"]["amount"] == order_total

    order = Order.objects.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["subtotal"]["gross"]["amount"] == subtotal.gross.amount

    assert order.voucher_code == voucher.code
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.shipping_method_name == shipping_method.name
    assert order.search_vector
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    assert order.base_shipping_price == shipping_total

    lines_data = data["lines"]
    discounted_line_data, line_1_data = lines_data
    assert discounted_line_data["productVariantId"] == variant_0_id
    assert discounted_line_data["quantity"] == variant_0_qty
    assert (
        discounted_line_data["unitPrice"]["gross"]["amount"]
        == discounted_variant_total / variant_0_qty
    )
    assert (
        discounted_line_data["totalPrice"]["gross"]["amount"]
        == discounted_variant_total
    )
    assert (
        discounted_line_data["unitDiscount"]["amount"]
        == discount_amount / variant_0_qty
    )
    assert discounted_line_data["unitDiscountType"] == DiscountValueType.FIXED.upper()
    assert discounted_line_data["unitDiscountReason"] == f"Voucher code: {code}"

    assert line_1_data["productVariantId"] == variant_1_id
    assert line_1_data["quantity"] == variant_1_qty
    assert (
        line_1_data["unitPrice"]["gross"]["amount"] == variant_1_total / variant_1_qty
    )
    assert line_1_data["totalPrice"]["gross"]["amount"] == variant_1_total
    assert line_1_data["unitDiscount"]["amount"] == 0
    assert line_1_data["unitDiscountType"] is None
    assert line_1_data["unitDiscountReason"] is None

    # TODO (SHOPX-874): Order discount object shouldn't be created
    assert order.discounts.count() == 1

    discounted_line = order.lines.get(variant=discounted_variant)
    assert discounted_line.discounts.count() == 1
    order_line_discount = discounted_line.discounts.first()
    assert order_line_discount.voucher == voucher
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.value_type == DiscountValueType.FIXED
    assert order_line_discount.value == discount_amount
    assert order_line_discount.amount_value == discount_amount


def test_draft_order_create_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    product_available_in_many_channels,
    voucher,
    channel_PLN,
    graphql_address_data,
    warehouse,
):
    # given
    variant = product_available_in_many_channels.variants.first()
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_draft_order_create_by_app(
    app_api_client,
    permission_manage_orders,
    customer_user,
    product_without_shipping,
    shipping_method_channel_PLN,
    product_available_in_many_channels,
    voucher,
    channel_PLN,
    graphql_address_data,
    warehouse,
):
    # given
    variant = product_available_in_many_channels.variants.first()
    query = DRAFT_ORDER_CREATE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method_channel_PLN.id
    )
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()


def test_draft_order_create_with_voucher_including_drafts_in_voucher_usage(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    channel_USD.include_draft_order_in_voucher_usage = True
    channel_USD.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher.apply_once_per_customer = True
    voucher.usage_limit = 10
    voucher.save(update_fields=["apply_once_per_customer", "usage_limit"])

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_qty = 2

    variant_list = [
        {"variantId": variant_id, "quantity": variant_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_listing = voucher.channel_listings.get(channel=channel_USD)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    shipping_total = shipping_method.channel_listings.get(
        channel=channel_USD
    ).get_total()
    order_total = (
        channel_listing.discounted_price_amount * variant_qty + shipping_total.amount
    )
    assert data["undiscountedTotal"]["gross"]["amount"] == order_total
    assert (
        data["total"]["gross"]["amount"] == order_total - voucher_listing.discount_value
    )

    order = Order.objects.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["subtotal"]["gross"]["amount"] == subtotal.gross.amount

    # Ensure order discount object was properly created
    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.voucher == voucher
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.value == voucher_listing.discount_value
    assert order_discount.amount_value == voucher_listing.discount_value

    code = voucher.codes.first()
    assert code.used == 1

    assert not VoucherCustomer.objects.filter(voucher_code=code).exists()


def test_draft_order_create_with_voucher_including_drafts_in_voucher_usage_invalid_code(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    channel_USD.include_draft_order_in_voucher_usage = True
    channel_USD.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher.single_use = True
    voucher.save(update_fields=["single_use"])

    code = voucher.codes.first()
    code.is_active = False
    code.save(update_fields=["is_active"])

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variant_qty = 2

    variant_list = [
        {"variantId": variant_id, "quantity": variant_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.INVALID_VOUCHER.name
    assert error["field"] == "voucher"


def test_draft_order_create_with_voucher_code_including_drafts_in_voucher_usage(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    channel_USD.include_draft_order_in_voucher_usage = True
    channel_USD.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher.apply_once_per_customer = True
    voucher.usage_limit = 10
    voucher.save(update_fields=["apply_once_per_customer", "usage_limit"])

    code_instance = voucher.codes.first()

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_qty = 2

    variant_list = [
        {"variantId": variant_id, "quantity": variant_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_listing = voucher.channel_listings.get(channel=channel_USD)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucherCode": code_instance.code,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    shipping_total = shipping_method.channel_listings.get(
        channel=channel_USD
    ).get_total()
    order_total = (
        channel_listing.discounted_price_amount * variant_qty + shipping_total.amount
    )
    assert data["undiscountedTotal"]["gross"]["amount"] == order_total
    assert (
        data["total"]["gross"]["amount"] == order_total - voucher_listing.discount_value
    )

    order = Order.objects.first()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["subtotal"]["gross"]["amount"] == subtotal.gross.amount

    # Ensure order discount object was properly created
    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.voucher == voucher
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.value == voucher_listing.discount_value
    assert order_discount.amount_value == voucher_listing.discount_value

    code = voucher.codes.first()
    assert code.used == 1

    assert not VoucherCustomer.objects.filter(voucher_code=code).exists()


def test_draft_order_create_voucher_code_including_drafts_in_voucher_usage_invalid_code(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    channel_USD.include_draft_order_in_voucher_usage = True
    channel_USD.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher.single_use = True
    voucher.save(update_fields=["single_use"])

    code = voucher.codes.first()
    code.is_active = False
    code.save(update_fields=["is_active"])

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variant_qty = 2

    variant_list = [
        {"variantId": variant_id, "quantity": variant_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucherCode": code.code,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.INVALID_VOUCHER_CODE.name
    assert error["field"] == "voucherCode"


def test_draft_order_create_voucher_including_drafts_in_voucher_usage_invalid_code(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    channel_USD.include_draft_order_in_voucher_usage = True
    channel_USD.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher.single_use = True
    voucher.save(update_fields=["single_use"])
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    code = voucher.codes.first()
    code.is_active = False
    code.save(update_fields=["is_active"])

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variant_qty = 2

    variant_list = [
        {"variantId": variant_id, "quantity": variant_qty},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.INVALID_VOUCHER.name
    assert error["field"] == "voucher"


def test_draft_order_create_with_same_variant_and_force_new_line(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)

    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
        {"variantId": variant_id, "quantity": 1, "forceNewLine": True},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note
    assert data["redirectUrl"] == redirect_url
    assert (
        data["billingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert (
        data["shippingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.billing_address
    assert order.shipping_address
    assert order.search_vector
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    assert order.base_shipping_price == shipping_total

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}

    # Ensure the order_added_products_event was created properly
    added_products_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.ADDED_PRODUCTS
    )
    event_parameters = added_products_event.parameters
    assert event_parameters
    assert len(event_parameters["lines"]) == 2

    order_lines = list(order.lines.all())
    assert event_parameters["lines"][0]["item"] == str(order_lines[0])
    assert event_parameters["lines"][0]["line_pk"] == str(order_lines[0].pk)
    assert event_parameters["lines"][0]["quantity"] == 1

    assert event_parameters["lines"][1]["item"] == str(order_lines[1])
    assert event_parameters["lines"][1]["line_pk"] == str(order_lines[1].pk)
    assert event_parameters["lines"][1]["quantity"] == 2


def test_draft_order_create_with_inactive_channel(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    channel_USD.is_active = False
    channel_USD.save()

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
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
            "channelId": channel_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note

    order = Order.objects.first()
    assert order.user == customer_user
    # billing address shouldn't be set
    assert not order.billing_address
    assert order.shipping_method == shipping_method
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    assert order.base_shipping_price == shipping_total

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


def test_draft_order_create_without_sku(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    ProductVariant.objects.update(sku=None)

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
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note
    assert data["redirectUrl"] == redirect_url
    assert (
        data["billingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )
    assert (
        data["shippingAddress"]["streetAddress1"]
        == graphql_address_data["streetAddress1"]
    )

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.billing_address
    assert order.shipping_address
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    assert order.base_shipping_price == shipping_total

    order_line = order.lines.get(variant=variant)
    assert order_line.product_sku is None
    assert order_line.product_variant_id == variant.get_global_id()

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


def test_draft_order_create_variant_with_0_price(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant.price = Money(0, "USD")
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()

    order = Order.objects.first()
    assert order.user == customer_user
    # billing address shouldn't be copied from user
    assert not order.billing_address
    assert order.shipping_method == shipping_method
    assert order.shipping_address.first_name == graphql_address_data["firstName"]

    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    assert order.base_shipping_price == shipping_total

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


@patch("saleor.graphql.order.mutations.draft_order_create.create_order_line")
def test_draft_order_create_tax_error(
    create_order_line_mock,
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variant_0 = variant
    err_msg = "Test error"
    create_order_line_mock.side_effect = TaxError(err_msg)
    query = DRAFT_ORDER_CREATE_MUTATION
    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
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
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
            "channelId": channel_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderCreate"]
    errors = data["errors"]
    assert not data["order"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.TAX_ERROR.name
    assert errors[0]["message"] == f"Unable to calculate taxes - {err_msg}"

    order_count = Order.objects.all().count()
    assert order_count == 0


def test_draft_order_create_with_voucher_not_assigned_to_order_channel(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher.channel_listings.all().delete()
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
            "channelId": channel_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "voucher"


def test_draft_order_create_with_product_and_variant_not_assigned_to_order_channel(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    channel_USD,
    graphql_address_data,
):
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variant.product.channel_listings.all().delete()
    variant.channel_listings.all().delete()
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "customerNote": customer_note,
            "channelId": channel_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.PRODUCT_NOT_PUBLISHED.name
    assert error["field"] == "lines"
    assert error["variants"] == [variant_id]


def test_draft_order_create_with_variant_not_assigned_to_order_channel(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    channel_USD,
    graphql_address_data,
):
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variant.channel_listings.all().delete()
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "customerNote": customer_note,
            "channelId": channel_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "lines"
    assert error["variants"] == [variant_id]


def test_draft_order_create_without_channel(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_list = [
        {"variantId": variant_0_id, "quantity": 2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.REQUIRED.name
    assert error["field"] == "channel"


def test_draft_order_create_with_negative_quantity_line(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    channel_USD,
    variant,
    voucher,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_list = [
        {"variantId": variant_0_id, "quantity": -2},
        {"variantId": variant_1_id, "quantity": 1},
    ]
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "channelId": channel_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["code"] == OrderErrorCode.ZERO_QUANTITY.name
    assert error["field"] == "quantity"


def test_draft_order_create_with_channel_with_unpublished_product(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    channel_listing = variant_1.product.channel_listings.get()
    channel_listing.is_published = False
    channel_listing.save()

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
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "channelId": channel_id,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
        }
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.PRODUCT_NOT_PUBLISHED.name
    assert error["variants"] == [variant_1_id]


def test_draft_order_create_with_channel_with_unpublished_product_by_date(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()
    next_day = datetime.now(pytz.UTC) + timedelta(days=1)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_1 = product_without_shipping.variants.first()
    channel_listing = variant_1.product.channel_listings.get()
    channel_listing.published_at = next_day
    channel_listing.save()

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
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "channelId": channel_id,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
        }
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderCreate"]["errors"][0]

    assert error["field"] == "lines"
    assert error["code"] == "PRODUCT_NOT_PUBLISHED"
    assert error["variants"] == [variant_1_id]


def test_draft_order_create_with_channel(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    graphql_address_data,
    channel_USD,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

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
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "channelId": channel_id,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.channel.id == channel_USD.id
    # billing address should be copied
    assert not order.billing_address
    assert order.shipping_method == shipping_method
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    assert order.base_shipping_price == shipping_total

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


def test_draft_order_create_product_without_shipping(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    voucher,
    graphql_address_data,
    channel_USD,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant = product_without_shipping.variants.first()

    variant.quantity = 2
    variant.save()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    discount = "10"
    customer_note = "Test note"
    variant_list = [
        {"variantId": variant_id, "quantity": 1},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "channelId": channel_id,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["voucher"]["code"] == voucher.code
    assert data["customerNote"] == customer_note

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.channel.id == channel_USD.id
    # billing address should be copied
    assert not order.billing_address
    assert order.shipping_method == shipping_method
    assert order.shipping_address.first_name == graphql_address_data["firstName"]
    assert order.base_shipping_price == Money(0, "USD")

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}


def test_draft_order_create_invalid_billing_address(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

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
    billing_address = graphql_address_data.copy()
    del billing_address["country"]
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "billingAddress": billing_address,
            "shippingAddress": graphql_address_data,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    errors = content["data"]["draftOrderCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "country"
    assert errors[0]["code"] == OrderErrorCode.REQUIRED.name
    assert errors[0]["addressType"] == AddressType.BILLING.upper()


def test_draft_order_create_invalid_shipping_address(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    voucher,
    channel_USD,
    graphql_address_data,
):
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

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
    shipping_address = graphql_address_data.copy()
    del shipping_address["country"]
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": variant_list,
            "billingAddress": graphql_address_data,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "voucher": voucher_id,
            "customerNote": customer_note,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    errors = content["data"]["draftOrderCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "country"
    assert errors[0]["code"] == OrderErrorCode.REQUIRED.name
    assert errors[0]["addressType"] == AddressType.SHIPPING.upper()


def test_draft_order_create_invalid_address_skip_validation(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    variant,
    channel_USD,
    graphql_address_data_skipped_validation,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variant_list = [{"variantId": variant_id, "quantity": 2}]

    address_data = graphql_address_data_skipped_validation
    invalid_postal_code = "invalid_postal_code"
    address_data["postalCode"] = invalid_postal_code

    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": address_data,
            "shippingAddress": address_data,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderCreate"]
    assert not data["errors"]
    assert data["order"]["shippingAddress"]["postalCode"] == invalid_postal_code
    assert data["order"]["billingAddress"]["postalCode"] == invalid_postal_code
    order = Order.objects.last()
    assert order.shipping_address.postal_code == invalid_postal_code
    assert order.shipping_address.validation_skipped is True
    assert order.billing_address.postal_code == invalid_postal_code
    assert order.billing_address.validation_skipped is True


@patch("saleor.order.calculations.fetch_order_prices_if_expired")
def test_draft_order_create_price_recalculation(
    mock_fetch_order_prices_if_expired,
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    product_available_in_many_channels,
    product_variant_list,
    channel_PLN,
    graphql_address_data,
    voucher,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    fake_order = Mock()
    fake_order.total = zero_taxed_money(channel_PLN.currency_code)
    fake_order.subtotal = zero_taxed_money(channel_PLN.currency_code)
    fake_order.undiscounted_total = zero_taxed_money(channel_PLN.currency_code)
    fake_order.shipping_price = zero_taxed_money(channel_PLN.currency_code)
    fetch_prices_response = Mock(return_value=(fake_order, None))
    mock_fetch_order_prices_if_expired.side_effect = fetch_prices_response
    query = DRAFT_ORDER_CREATE_MUTATION
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    discount = "10"
    variant_1 = product_available_in_many_channels.variants.first()
    variant_2 = product_variant_list[2]
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    variant_2_id = graphene.Node.to_global_id("ProductVariant", variant_2.id)
    quantity_1 = 3
    quantity_2 = 4
    lines = [
        {"variantId": variant_1_id, "quantity": quantity_1},
        {"variantId": variant_2_id, "quantity": quantity_2},
    ]
    address = graphql_address_data
    voucher_amount = 13
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_PLN,
        discount=Money(voucher_amount, channel_PLN.currency_code),
    )
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "input": {
            "user": user_id,
            "discount": discount,
            "lines": lines,
            "billingAddress": address,
            "shippingAddress": address,
            "voucher": voucher_id,
            "channelId": channel_id,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    assert Order.objects.count() == 1
    order = Order.objects.first()
    lines = list(order.lines.all())
    mock_fetch_order_prices_if_expired.assert_called()


def test_draft_order_create_update_display_gross_prices(
    staff_api_client,
    permission_group_manage_orders,
    variant,
    channel_USD,
    graphql_address_data,
):
    # given
    # display_gross_prices is disabled and there is no country-specific configuration
    # order.display_gross_prices should be also disabled as a result
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    tax_config = channel_USD.tax_configuration
    tax_config.display_gross_prices = False
    tax_config.save()
    tax_config.country_exceptions.all().delete()

    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION

    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    variant_list = [{"variantId": variant_0_id, "quantity": 2}]
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {
        "input": {
            "lines": variant_list,
            "billingAddress": graphql_address_data,
            "shippingAddress": graphql_address_data,
            "channelId": channel_id,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    order_id = content["data"]["draftOrderCreate"]["order"]["id"]
    _, order_pk = graphene.Node.from_global_id(order_id)

    order = Order.objects.get(id=order_pk)
    assert not order.display_gross_prices


def test_draft_order_create_with_non_unique_external_reference(
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
    order,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    ext_ref = "test-ext-ref"
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])

    variables = {"input": {"channelId": channel_id, "externalReference": ext_ref}}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["draftOrderCreate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == OrderErrorCode.UNIQUE.name
    assert error["message"] == "Order with this External reference already exists."


@pytest.mark.parametrize("force_new_line", [True, False])
def test_draft_order_create_with_custom_price_in_order_line(
    force_new_line,
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    product_without_shipping,
    shipping_method,
    variant,
    graphql_address_data,
    channel_USD,
):
    # given
    variant_0 = variant
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_0_id = graphene.Node.to_global_id("ProductVariant", variant_0.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variant_1 = product_without_shipping.variants.first()
    variant_1.quantity = 2
    variant_1.save()
    variant_1_id = graphene.Node.to_global_id("ProductVariant", variant_1.id)
    expected_price_variant_0 = 10
    expected_price_variant_1 = 20
    variant_list = [
        {
            "variantId": variant_0_id,
            "quantity": 2,
            "price": expected_price_variant_0,
            "forceNewLine": force_new_line,
        },
        {
            "variantId": variant_1_id,
            "quantity": 1,
            "price": expected_price_variant_1,
            "forceNewLine": force_new_line,
        },
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()

    order = Order.objects.first()

    order_line_0 = order.lines.get(variant=variant_0)
    assert order_line_0.base_unit_price_amount == expected_price_variant_0
    assert order_line_0.undiscounted_base_unit_price_amount == expected_price_variant_0
    assert order_line_0.is_price_overridden is True

    order_line_1 = order.lines.get(variant=variant_1)
    assert order_line_1.base_unit_price_amount == expected_price_variant_1
    assert order_line_1.undiscounted_base_unit_price_amount == expected_price_variant_1
    assert order_line_1.is_price_overridden is True


def test_draft_order_create_with_custom_price_and_catalogue_promotion(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    variant_on_promotion,
    channel_USD,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variant = variant_on_promotion

    variant_listing = variant.channel_listings.get(channel=channel_USD)
    variant_price = variant_listing.price_amount
    promotion_rule = variant_listing.promotion_rules.first()
    reward_value = promotion_rule.reward_value

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    custom_price = 18
    quantity = 2
    variant_list = [
        {
            "variantId": variant_id,
            "quantity": quantity,
            "price": custom_price,
            "forceNewLine": False,
        },
        {
            "variantId": variant_id,
            "quantity": quantity,
            "forceNewLine": True,
        },
    ]
    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "channelId": channel_id,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert len(data["lines"]) == 2

    line_1_unit_discount = custom_price * reward_value / 100
    promotion_id = graphene.Node.to_global_id("Promotion", promotion_rule.promotion_id)
    line_data_1 = {
        "productVariantId": variant_id,
        "quantity": quantity,
        "unitDiscount": {
            "amount": float(line_1_unit_discount),
        },
        "unitPrice": {
            "gross": {
                "amount": float(custom_price - line_1_unit_discount),
            },
        },
        "undiscountedUnitPrice": {
            "gross": {
                "amount": float(custom_price),
            },
        },
        "totalPrice": {
            "gross": {
                "amount": float((custom_price - line_1_unit_discount) * quantity),
            },
        },
        "unitDiscountReason": f"Promotion: {promotion_id}",
        "unitDiscountType": RewardValueType.PERCENTAGE.upper(),
        "unitDiscountValue": reward_value,
        "isPriceOverridden": True,
        "isGift": False,
    }
    assert line_data_1 in data["lines"]
    line_2_unit_discount = variant_price * reward_value / 100
    line_data_2 = {
        "productVariantId": variant_id,
        "quantity": quantity,
        "unitDiscount": {
            "amount": float(line_2_unit_discount),
        },
        "unitPrice": {
            "gross": {
                "amount": float(variant_price - line_2_unit_discount),
            },
        },
        "undiscountedUnitPrice": {
            "gross": {
                "amount": float(variant_price),
            },
        },
        "totalPrice": {
            "gross": {
                "amount": float((variant_price - line_2_unit_discount) * quantity),
            },
        },
        "unitDiscountReason": f"Promotion: {promotion_id}",
        "unitDiscountType": RewardValueType.PERCENTAGE.upper(),
        "unitDiscountValue": reward_value,
        "isPriceOverridden": False,
        "isGift": False,
    }
    assert line_data_2 in data["lines"]


def test_draft_order_create_product_catalogue_promotion(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    shipping_method,
    variant,
    catalogue_promotion,
    channel_USD,
    graphql_address_data,
):
    # given
    promotion = catalogue_promotion
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    reward_value = Decimal("1.0")
    rule = promotion.rules.first()
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel_USD.currency_code,
    )

    quantity = 2
    variant_list = [
        {"variantId": variant_id, "quantity": quantity},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)

    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["shippingMethodName"] == shipping_method.name
    assert data["shippingAddress"]
    assert data["billingAddress"]

    order = Order.objects.first()
    shipping_total = (
        shipping_method.channel_listings.get(channel_id=order.channel_id)
        .get_total()
        .amount
    )
    assert data["shippingPrice"]["gross"]["amount"] == shipping_total

    assert order.search_vector

    assert len(data["lines"]) == 1
    line_data = data["lines"][0]
    assert line_data["unitDiscount"]["amount"] == reward_value
    assert (
        line_data["unitPrice"]["gross"]["amount"]
        == variant_channel_listing.discounted_price_amount
    )
    assert (
        line_data["undiscountedUnitPrice"]["gross"]["amount"]
        == variant_channel_listing.price_amount
    )
    line_total = variant_channel_listing.discounted_price_amount * quantity
    assert line_data["totalPrice"]["gross"]["amount"] == line_total
    assert line_data["unitDiscountReason"]
    assert line_data["unitDiscountType"]

    line = order.lines.first()
    assert line.discounts.count() == 1
    assert line.sale_id

    assert data["total"]["gross"]["amount"] == shipping_total + line_total
    assert (
        data["undiscountedTotal"]["gross"]["amount"]
        == shipping_total + variant_channel_listing.price_amount * quantity
    )

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}

    # Ensure the order_added_products_event was created properly
    added_products_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.ADDED_PRODUCTS
    )
    event_parameters = added_products_event.parameters
    assert event_parameters
    assert len(event_parameters["lines"]) == 1

    order_lines = list(order.lines.all())
    assert event_parameters["lines"][0]["item"] == str(order_lines[0])
    assert event_parameters["lines"][0]["line_pk"] == str(order_lines[0].pk)
    assert event_parameters["lines"][0]["quantity"] == quantity


def test_draft_order_create_product_catalogue_promotion_flat_taxes(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    customer_user,
    shipping_method,
    variant,
    catalogue_promotion,
    channel_USD,
    graphql_address_data,
):
    # given
    promotion = catalogue_promotion
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    tc = channel_USD.tax_configuration
    tc.country_exceptions.all().delete()
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

    # Ensure no events were created yet
    assert not OrderEvent.objects.exists()

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    reward_value = Decimal("1.0")
    rule = promotion.rules.first()
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel_USD.currency_code,
    )

    quantity = 2
    variant_list = [
        {"variantId": variant_id, "quantity": quantity},
    ]
    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)

    assert not content["data"]["draftOrderCreate"]["errors"]
    data = content["data"]["draftOrderCreate"]["order"]
    assert data["status"] == OrderStatus.DRAFT.upper()
    assert data["shippingMethodName"] == shipping_method.name
    assert data["shippingAddress"]
    assert data["billingAddress"]

    order = Order.objects.first()
    shipping_total = (
        shipping_method.channel_listings.get(channel_id=order.channel_id)
        .get_total()
        .amount
    )
    assert data["shippingPrice"]["gross"]["amount"] == shipping_total

    assert order.search_vector

    assert len(data["lines"]) == 1
    line_data = data["lines"][0]
    assert line_data["unitDiscount"]["amount"] == reward_value
    assert (
        line_data["unitPrice"]["gross"]["amount"]
        == variant_channel_listing.discounted_price_amount
    )
    assert (
        line_data["undiscountedUnitPrice"]["gross"]["amount"]
        == variant_channel_listing.price_amount
    )
    line_total = variant_channel_listing.discounted_price_amount * quantity
    assert line_data["totalPrice"]["gross"]["amount"] == line_total
    assert line_data["unitDiscountReason"]
    assert line_data["unitDiscountType"]

    line = order.lines.first()
    assert line.discounts.count() == 1
    assert line.sale_id

    assert data["total"]["gross"]["amount"] == shipping_total + line_total
    assert (
        data["undiscountedTotal"]["gross"]["amount"]
        == shipping_total + variant_channel_listing.price_amount * quantity
    )

    # Ensure the correct event was created
    created_draft_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.DRAFT_CREATED
    )
    assert created_draft_event.user == staff_user
    assert created_draft_event.parameters == {}

    # Ensure the order_added_products_event was created properly
    added_products_event = OrderEvent.objects.get(
        type=order_events.OrderEvents.ADDED_PRODUCTS
    )
    event_parameters = added_products_event.parameters
    assert event_parameters
    assert len(event_parameters["lines"]) == 1

    order_lines = list(order.lines.all())
    assert event_parameters["lines"][0]["item"] == str(order_lines[0])
    assert event_parameters["lines"][0]["line_pk"] == str(order_lines[0].pk)
    assert event_parameters["lines"][0]["quantity"] == quantity


def test_draft_order_create_order_promotion_flat_rates(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    graphql_address_data,
    order_promotion_rule,
    variant_with_many_stocks,
    channel_USD,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    currency = channel_USD.currency_code

    tc = channel_USD.tax_configuration
    tc.country_exceptions.all().delete()
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.prices_entered_with_tax = False
    tc.save()
    tax_rate = Decimal("1.23")

    rule = order_promotion_rule
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    assert rule.reward_value_type == RewardValueType.PERCENTAGE
    reward_value = rule.reward_value
    assert rule.reward_value == Decimal("25")

    variant = variant_with_many_stocks
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    quantity = 4
    variant_list = [
        {"variantId": variant_id, "quantity": quantity},
    ]

    # calculate expected values
    variant_price = variant.channel_listings.get(
        channel=channel_USD
    ).discounted_price_amount
    undiscounted_subtotal_net = Decimal(quantity * variant_price)
    discount_amount = quantize_price(
        reward_value / 100 * undiscounted_subtotal_net, currency
    )
    subtotal_net = undiscounted_subtotal_net - discount_amount
    subtotal_gross = quantize_price(tax_rate * subtotal_net, currency)
    shipping_price_net = shipping_method.channel_listings.get(
        channel=channel_USD
    ).price_amount
    shipping_price_gross = quantize_price(tax_rate * shipping_price_net, currency)
    total_gross = quantize_price(subtotal_gross + shipping_price_gross, currency)

    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    order = content["data"]["draftOrderCreate"]["order"]
    assert order["status"] == OrderStatus.DRAFT.upper()
    assert order["subtotal"]["gross"]["amount"] == float(subtotal_gross)
    assert order["total"]["gross"]["amount"] == float(total_gross)
    assert order["shippingPrice"]["gross"]["amount"] == float(shipping_price_gross)

    assert len(order["discounts"]) == 1
    assert order["discounts"][0]["amount"]["amount"] == discount_amount
    assert order["discounts"][0]["reason"] == f"Promotion: {promotion_id}"
    assert order["discounts"][0]["type"] == DiscountType.ORDER_PROMOTION.upper()
    assert order["discounts"][0]["valueType"] == RewardValueType.PERCENTAGE.upper()

    assert len(order["lines"]) == 1
    assert order["lines"][0]["quantity"] == quantity
    assert order["lines"][0]["totalPrice"]["gross"]["amount"] == float(subtotal_gross)
    assert order["lines"][0]["undiscountedUnitPrice"]["gross"]["amount"] == float(
        quantize_price(undiscounted_subtotal_net * tax_rate / quantity, currency)
    )
    assert order["lines"][0]["unitPrice"]["gross"]["amount"] == float(
        round_up(subtotal_gross / quantity)
    )

    order_db = Order.objects.get()
    assert order_db.total_gross_amount == total_gross
    assert order_db.subtotal_gross_amount == subtotal_gross
    assert order_db.shipping_price_gross_amount == shipping_price_gross

    line_db = order_db.lines.get()
    assert line_db.total_price_gross_amount == subtotal_gross
    assert line_db.undiscounted_unit_price_gross_amount == quantize_price(
        undiscounted_subtotal_net * tax_rate / quantity, currency
    )
    assert line_db.unit_price_net_amount == quantize_price(
        subtotal_net / quantity, currency
    )
    assert line_db.unit_price_gross_amount == round_up(subtotal_gross / quantity)

    discount_db = order_db.discounts.get()
    assert discount_db.amount_value == discount_amount
    assert discount_db.reason == f"Promotion: {promotion_id}"
    assert discount_db.value == reward_value
    assert discount_db.value_type == RewardValueType.PERCENTAGE


def test_draft_order_create_gift_promotion_flat_rates(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    graphql_address_data,
    gift_promotion_rule,
    variant_with_many_stocks,
    channel_USD,
):
    # given
    query = DRAFT_ORDER_CREATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    currency = channel_USD.currency_code

    tc = channel_USD.tax_configuration
    tc.country_exceptions.all().delete()
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.prices_entered_with_tax = False
    tc.save()
    tax_rate = Decimal("1.23")

    rule = gift_promotion_rule
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    assert rule.reward_type == RewardType.GIFT

    variant = variant_with_many_stocks
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    quantity = 4
    variant_list = [
        {"variantId": variant_id, "quantity": quantity},
    ]

    # calculate expected values
    variant_price = variant.channel_listings.get(
        channel=channel_USD
    ).discounted_price_amount
    subtotal_net = quantity * variant_price
    subtotal_gross = quantize_price(tax_rate * subtotal_net, currency)
    shipping_price_net = shipping_method.channel_listings.get(
        channel=channel_USD
    ).price_amount
    shipping_price_gross = quantize_price(tax_rate * shipping_price_net, currency)
    total_gross = quantize_price(subtotal_gross + shipping_price_gross, currency)

    shipping_address = graphql_address_data
    shipping_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    redirect_url = "https://www.example.com"

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": shipping_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderCreate"]["errors"]
    order = content["data"]["draftOrderCreate"]["order"]

    assert order["status"] == OrderStatus.DRAFT.upper()
    assert order["subtotal"]["gross"]["amount"] == float(subtotal_gross)
    assert Decimal(order["total"]["gross"]["amount"]) == float(total_gross)
    assert Decimal(order["shippingPrice"]["gross"]["amount"]) == float(
        shipping_price_gross
    )

    assert not order["discounts"]

    assert len(order["lines"]) == 2
    line = [line for line in order["lines"] if line["quantity"] == 4][0]
    gift_line = [line for line in order["lines"] if line["isGift"]][0]

    assert line["totalPrice"]["gross"]["amount"] == float(subtotal_gross)
    assert line["undiscountedUnitPrice"]["gross"]["amount"] == float(
        subtotal_gross / quantity
    )
    assert line["unitPrice"]["gross"]["amount"] == float(subtotal_gross / quantity)
    assert line["unitDiscount"]["amount"] == 0.00

    order_db = Order.objects.get()
    assert order_db.total_gross_amount == total_gross
    assert order_db.subtotal_gross_amount == subtotal_gross
    assert order_db.shipping_price_gross_amount == shipping_price_gross

    lines_db = order_db.lines.all()
    assert len(lines_db) == 2
    gift_line_db = [line for line in lines_db if line.is_gift][0]
    gift_price = gift_line_db.variant.channel_listings.get(
        channel=channel_USD
    ).price_amount

    assert gift_line_db.total_price_gross_amount == Decimal(0)
    assert gift_line_db.undiscounted_unit_price_gross_amount == Decimal(0)
    assert gift_line_db.unit_price_gross_amount == Decimal(0)
    assert gift_line_db.base_unit_price_amount == Decimal(0)
    assert gift_line_db.unit_discount_value == gift_price

    assert gift_line["totalPrice"]["gross"]["amount"] == 0.00
    assert gift_line["undiscountedUnitPrice"]["gross"]["amount"] == 0.00
    assert gift_line["unitPrice"]["gross"]["amount"] == 0.00
    assert gift_line["unitDiscount"]["amount"] == gift_price
    assert gift_line["unitDiscountReason"] == f"Promotion: {promotion_id}"
    assert gift_line["unitDiscountType"] == RewardValueType.FIXED.upper()
    assert gift_line["unitDiscountValue"] == gift_price

    discount_db = gift_line_db.discounts.get()
    assert discount_db.amount_value == gift_price
    assert discount_db.reason == f"Promotion: {promotion_id}"
    assert discount_db.type == DiscountType.ORDER_PROMOTION


def test_draft_order_create_with_cc_warehouse_as_shipping_method(
    app_api_client,
    permission_manage_orders,
    customer_user,
    product_available_in_many_channels,
    channel_PLN,
    graphql_address_data,
    warehouse_for_cc,
):
    # given
    variant = product_available_in_many_channels.variants.first()
    query = DRAFT_ORDER_CREATE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    redirect_url = "https://www.example.com"
    cc_warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse_for_cc.id)

    variables = {
        "input": {
            "user": user_id,
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "shippingMethod": cc_warehouse_id,
            "channelId": channel_id,
            "redirectUrl": redirect_url,
        }
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderCreate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert errors[0]["field"] == "shippingMethod"


def test_draft_order_create_with_voucher_without_user(
    voucher_percentage,
    app_api_client,
    permission_manage_orders,
    product_available_in_many_channels,
    graphql_address_data,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.first()
    query = DRAFT_ORDER_CREATE_MUTATION
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variant_list = [
        {"variantId": variant_id, "quantity": 2},
    ]
    shipping_address = graphql_address_data
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "input": {
            "lines": variant_list,
            "billingAddress": shipping_address,
            "shippingAddress": shipping_address,
            "channelId": channel_id,
            "voucherCode": voucher_percentage.code,
        }
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderCreate"]
    assert len(data["errors"]) == 0
    order = Order.objects.get(id=graphene.Node.from_global_id(data["order"]["id"])[1])
    assert order.user is None
    assert data["order"]["voucherCode"] == voucher_percentage.code == order.voucher_code
    assert data["order"]["status"] == OrderStatus.DRAFT.upper() == order.status.upper()
