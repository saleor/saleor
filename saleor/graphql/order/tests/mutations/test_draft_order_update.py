from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
import pytest
from django.test import override_settings
from prices import TaxedMoney

from .....core.models import EventDelivery
from .....core.prices import quantize_price
from .....core.taxes import zero_money
from .....discount import DiscountType, DiscountValueType, RewardValueType, VoucherType
from .....discount.models import OrderDiscount, Voucher
from .....discount.utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
)
from .....order import OrderStatus
from .....order.actions import call_order_event
from .....order.calculations import fetch_order_prices_if_expired
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent
from .....order.utils import update_discount_for_order_line
from .....payment.model_helpers import get_subtotal
from .....shipping.models import ShippingMethod
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....core.utils import snake_to_camel_case
from ....tests.utils import assert_no_permission, get_graphql_content
from ...mutations.draft_order_create import DraftOrderInput

DRAFT_ORDER_UPDATE_MUTATION = """
        mutation draftUpdate(
        $id: ID!,
        $input: DraftOrderInput!,
        ) {
            draftOrderUpdate(
                id: $id,
                input: $input
            ) {
                errors {
                    field
                    code
                    message
                }
                order {
                    metadata {
                      key
                      value
                    }
                    privateMetadata {
                      key
                      value
                    }
                    userEmail
                    externalReference
                    channel {
                        id
                    }
                    total {
                        net {
                            amount
                        }
                    }
                    undiscountedTotal {
                        net {
                            amount
                        }
                    }
                    billingAddress{
                        city
                        streetAddress1
                        postalCode
                        metadata {
                            key
                            value
                        }
                    }
                    voucher {
                        code
                    }
                    voucherCode
                    shippingAddress{
                        city
                        streetAddress1
                        postalCode
                        metadata {
                            key
                            value
                        }
                    }
                    total {
                        gross {
                            amount
                        }
                        net {
                            amount
                        }
                    }
                    subtotal {
                        gross {
                            amount
                        }
                        net {
                            amount
                        }
                    }
                    undiscountedTotal {
                        gross {
                            amount
                        }
                        net {
                            amount
                        }
                    }
                    discounts {
                        total {
                            amount
                            currency
                        }
                        amount {
                            amount
                            currency
                        }
                        valueType
                        type
                        reason
                    }
                    lines {
                        quantity
                        unitDiscount {
                          amount
                        }
                        undiscountedUnitPrice {
                            net {
                                amount
                            }
                        }
                        unitPrice {
                            net {
                                amount
                            }
                        }
                        totalPrice {
                            net {
                                amount
                            }
                        }
                        unitDiscountReason
                        unitDiscountType
                        unitDiscountValue
                        isGift
                        discounts{
                            valueType
                            value
                            reason
                            unit{
                                amount
                            }
                            total{
                                amount
                            }
                        }
                    }
                    shippingPrice {
                        gross {
                            amount
                        }
                        net {
                            amount
                        }
                    }
                }
            }
        }
        """


def test_draft_order_update_existing_channel_id(
    staff_api_client, permission_group_manage_orders, order_with_lines, channel_PLN
):
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {
        "id": order_id,
        "input": {
            "channelId": channel_id,
        },
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]

    assert error["code"] == OrderErrorCode.NOT_EDITABLE.name
    assert error["field"] == "channelId"


def test_draft_order_update_voucher_not_available(
    staff_api_client, permission_group_manage_orders, order_with_lines, voucher
):
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()
    assert order.voucher is None
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    voucher.channel_listings.all().delete()
    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
        },
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]

    assert error["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert error["field"] == "voucher"


def test_draft_order_update_with_voucher_entire_order(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
):
    # given
    order = draft_order
    currency = order.currency
    assert not order.voucher
    assert not order.voucher_code
    assert not order.customer_note
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    customer_note = "Test customer note"
    external_reference = "test-ext-ref"
    order_total = order.total_net_amount

    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
            "customerNote": customer_note,
            "externalReference": external_reference,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert data["order"]["voucher"]["code"] == voucher.code
    assert data["order"]["voucherCode"] == voucher.code
    stored_metadata = {"public": "public_value"}

    assert (
        data["order"]["billingAddress"]["metadata"] == graphql_address_data["metadata"]
    )
    assert (
        data["order"]["shippingAddress"]["metadata"] == graphql_address_data["metadata"]
    )
    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert (
        data["order"]["total"]["net"]["amount"]
        == order_total - voucher_listing.discount_value
    )

    assert len(data["order"]["discounts"]) == 1
    discount = data["order"]["discounts"][0]
    assert discount["amount"]["amount"] == voucher_listing.discount_value
    assert discount["amount"]["currency"] == currency

    assert discount["total"]["amount"] == voucher_listing.discount_value
    assert discount["total"]["currency"] == currency

    assert not data["errors"]
    order.refresh_from_db()
    assert order.billing_address.metadata == stored_metadata
    assert order.shipping_address.metadata == stored_metadata
    assert order.billing_address.validation_skipped is False
    assert order.shipping_address.validation_skipped is False
    assert order.voucher_code == voucher.code
    assert order.customer_note == customer_note
    assert order.search_vector
    assert (
        data["order"]["externalReference"]
        == external_reference
        == order.external_reference
    )
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount

    # Ensure order discount object was properly created
    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.voucher == voucher
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.value == voucher_listing.discount_value
    assert order_discount.amount_value == voucher_listing.discount_value


def test_draft_order_update_with_voucher_specific_product(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher_specific_product_type,
    graphql_address_data,
):
    # given
    voucher = voucher_specific_product_type
    code = voucher.codes.first().code

    order = draft_order
    assert not order.voucher
    assert not order.voucher_code
    assert not order.customer_note
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    order_total = order.total_net_amount

    discounted_line, line_1 = order.lines.all()
    voucher.variants.add(discounted_line.variant)
    discount_amount = (
        discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * voucher_listing.discount_value
        / 100
    )

    variables = {
        "id": order_id,
        "input": {
            "voucherCode": code,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["voucher"]["code"] == voucher.code
    assert data["order"]["voucherCode"] == voucher.code

    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert data["order"]["total"]["net"]["amount"] == order_total - discount_amount

    discounted_variant_total = (
        discounted_line.undiscounted_base_unit_price_amount * discounted_line.quantity
        - discount_amount
    )
    lines_data = data["order"]["lines"]
    discounted_line_data, line_1_data = lines_data

    expected_discount_reason = f"Voucher code: {code}"
    expected_unit_discount = discount_amount / discounted_line.quantity
    expected_total_discount = discount_amount
    assert (
        discounted_line_data["unitPrice"]["net"]["amount"]
        == discounted_variant_total / discounted_line.quantity
    )
    assert (
        discounted_line_data["totalPrice"]["net"]["amount"] == discounted_variant_total
    )
    assert discounted_line_data["unitDiscount"]["amount"] == expected_unit_discount
    assert (
        discounted_line_data["unitDiscountType"] == voucher.discount_value_type.upper()
    )
    assert discounted_line_data["unitDiscountReason"] == expected_discount_reason

    assigned_discount_objects = discounted_line_data["discounts"]
    assert len(assigned_discount_objects) == 1
    assigned_discount = assigned_discount_objects[0]
    assert assigned_discount["reason"] == expected_discount_reason
    assert assigned_discount["valueType"] == voucher.discount_value_type.upper()
    assert assigned_discount["unit"]["amount"] == expected_unit_discount
    assert assigned_discount["total"]["amount"] == expected_total_discount
    assert assigned_discount["value"] == voucher.channel_listings.get().discount_value

    line_1_total = line_1.undiscounted_base_unit_price_amount * line_1.quantity
    assert line_1_data["unitPrice"]["net"]["amount"] == line_1_total / line_1.quantity
    assert line_1_data["totalPrice"]["net"]["amount"] == line_1_total
    assert line_1_data["unitDiscount"]["amount"] == 0
    assert line_1_data["unitDiscountType"] is None
    assert line_1_data["unitDiscountReason"] is None
    assert len(line_1_data["discounts"]) == 0

    order.refresh_from_db()
    assert order.voucher_code == voucher.code
    assert order.search_vector

    assert order.discounts.count() == 0
    assert discounted_line.discounts.count() == 1
    order_line_discount = discounted_line.discounts.first()
    assert order_line_discount.voucher == voucher
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.value_type == voucher.discount_value_type
    assert order_line_discount.value == voucher_listing.discount_value
    assert order_line_discount.amount_value == discount_amount


def test_draft_order_update_with_voucher_apply_once_per_order(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher_percentage,
    graphql_address_data,
):
    # given
    order = draft_order
    assert not order.voucher
    assert not order.voucher_code

    voucher = voucher_percentage
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["apply_once_per_order"])
    code = voucher.codes.first().code

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    order_total = order.total_net_amount

    discounted_line, line_1 = order.lines.all()
    voucher.variants.add(discounted_line.variant)
    discount_amount = (
        discounted_line.undiscounted_base_unit_price_amount
        * voucher_listing.discount_value
        / 100
    )

    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["voucher"]["code"] == voucher.code
    assert data["order"]["voucherCode"] == voucher.code
    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert data["order"]["total"]["net"]["amount"] == order_total - discount_amount

    discounted_variant_total = (
        discounted_line.undiscounted_base_unit_price_amount * discounted_line.quantity
        - discount_amount
    )
    lines_data = data["order"]["lines"]
    discounted_line_data, line_1_data = lines_data

    expected_discount_reason = f"Voucher code: {code}"
    expected_total_discount = discount_amount
    expected_unit_discount = quantize_price(
        Decimal(discount_amount / discounted_line.quantity), order.currency
    )

    assert discounted_line_data["unitPrice"]["net"]["amount"] == float(
        round(discounted_variant_total / discounted_line.quantity, 2)
    )
    assert (
        discounted_line_data["totalPrice"]["net"]["amount"] == discounted_variant_total
    )
    assert (
        quantize_price(
            Decimal(discounted_line_data["unitDiscount"]["amount"]), order.currency
        )
        == expected_unit_discount
    )
    assert (
        discounted_line_data["unitDiscountType"] == voucher.discount_value_type.upper()
    )
    assert discounted_line_data["unitDiscountReason"] == expected_discount_reason

    assigned_discount_objects = discounted_line_data["discounts"]
    assert len(assigned_discount_objects) == 1
    assigned_discount = assigned_discount_objects[0]
    assert assigned_discount["reason"] == expected_discount_reason
    assert assigned_discount["valueType"] == voucher.discount_value_type.upper()
    assert (
        quantize_price(Decimal(assigned_discount["unit"]["amount"]), order.currency)
        == expected_unit_discount
    )
    assert assigned_discount["total"]["amount"] == expected_total_discount
    assert assigned_discount["value"] == voucher.channel_listings.get().discount_value

    line_1_total = line_1.undiscounted_base_unit_price_amount * line_1.quantity
    assert line_1_data["unitPrice"]["net"]["amount"] == line_1_total / line_1.quantity
    assert line_1_data["totalPrice"]["net"]["amount"] == line_1_total
    assert line_1_data["unitDiscount"]["amount"] == 0
    assert line_1_data["unitDiscountType"] is None
    assert line_1_data["unitDiscountReason"] is None
    assert len(line_1_data["discounts"]) == 0

    order.refresh_from_db()
    assert order.voucher_code == voucher.code
    assert order.search_vector

    assert order.discounts.count() == 0
    assert discounted_line.discounts.count() == 1
    order_line_discount = discounted_line.discounts.first()
    assert order_line_discount.voucher == voucher
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.value_type == voucher.discount_value_type
    assert order_line_discount.value == voucher_listing.discount_value
    assert order_line_discount.amount_value == discount_amount


def test_draft_order_update_clear_voucher(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    # given
    order = draft_order
    order.voucher = voucher
    code_instance = voucher.codes.first()
    order.voucher_code = code_instance.code
    order.save(update_fields=["voucher", "voucher_code"])

    code_instance.used += 1
    code_instance.save(update_fields=["used"])
    code_used = code_instance.used

    voucher.usage_limit = 5
    voucher.save(update_fields=["usage_limit"])

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = voucher_listing.discount_value
    order.discounts.create(
        voucher=voucher,
        value=discount_amount,
        type=DiscountType.VOUCHER,
    )

    order.total_gross_amount -= discount_amount
    order.total_net_amount -= discount_amount
    order.save(update_fields=["total_net_amount", "total_gross_amount"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_total = order.undiscounted_total_net_amount

    variables = {
        "id": order_id,
        "input": {
            "voucher": None,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]

    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert data["order"]["total"]["net"]["amount"] == order_total
    assert not data["order"]["voucher"]
    assert not data["order"]["voucherCode"]

    assert not data["errors"]
    order.refresh_from_db()
    assert not order.voucher
    assert order.search_vector

    assert not order.discounts.count()
    code_instance.refresh_from_db()
    assert code_instance.used == code_used


def test_draft_order_update_clear_voucher_code(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    # given
    order = draft_order
    code_instance = voucher.codes.first()
    order.voucher = voucher
    order.voucher_code = code_instance.code
    order.save(update_fields=["voucher", "voucher_code"])

    code_instance.used += 1
    code_instance.save(update_fields=["used"])
    code_used = code_instance.used

    voucher.usage_limit = 5
    voucher.save(update_fields=["usage_limit"])

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = voucher_listing.discount_value
    order.discounts.create(
        voucher=voucher,
        value=discount_amount,
        type=DiscountType.VOUCHER,
    )

    order.total_gross_amount -= discount_amount
    order.total_net_amount -= discount_amount
    order.save(update_fields=["total_net_amount", "total_gross_amount"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_total = order.undiscounted_total_net_amount

    variables = {
        "id": order_id,
        "input": {
            "voucherCode": None,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]

    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert data["order"]["total"]["net"]["amount"] == order_total
    assert not data["order"]["voucher"]
    assert not data["order"]["voucherCode"]

    assert not data["errors"]
    order.refresh_from_db()
    assert not order.voucher
    assert order.search_vector

    assert not order.discounts.count()
    code_instance.refresh_from_db()
    assert code_instance.used == code_used


def test_draft_order_update_clear_voucher_and_reduce_voucher_usage(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    # given
    order = draft_order
    order.voucher = voucher
    code_instance = voucher.codes.first()
    order.voucher_code = code_instance.code
    order.save(update_fields=["voucher", "voucher_code"])

    code_instance.used += 1
    code_instance.save(update_fields=["used"])
    code_used = code_instance.used

    voucher.usage_limit = 5
    voucher.save(update_fields=["usage_limit"])

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher_listing = voucher.channel_listings.get(channel=channel)
    discount_amount = voucher_listing.discount_value
    order.discounts.create(
        voucher=voucher,
        value=discount_amount,
        type=DiscountType.VOUCHER,
    )

    order.total_gross_amount -= discount_amount
    order.total_net_amount -= discount_amount
    order.save(update_fields=["total_net_amount", "total_gross_amount"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_total = order.undiscounted_total_net_amount

    variables = {
        "id": order_id,
        "input": {
            "voucher": None,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]

    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert data["order"]["total"]["net"]["amount"] == order_total
    assert not data["order"]["voucher"]
    assert not data["order"]["voucherCode"]

    assert not data["errors"]
    order.refresh_from_db()
    assert not order.voucher
    assert order.search_vector

    assert not order.discounts.count()
    code_instance.refresh_from_db()
    assert code_instance.used == code_used - 1


def test_draft_order_update_clear_voucher_code_and_reduce_voucher_usage(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    # given
    order = draft_order
    code_instance = voucher.codes.first()
    order.voucher = voucher
    order.voucher_code = code_instance.code
    order.save(update_fields=["voucher", "voucher_code"])

    code_instance.used += 1
    code_instance.save(update_fields=["used"])
    code_used = code_instance.used

    voucher.usage_limit = 5
    voucher.save(update_fields=["usage_limit"])

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher_listing = voucher.channel_listings.get(channel=channel)
    discount_amount = voucher_listing.discount_value
    order.discounts.create(
        voucher=voucher,
        value=discount_amount,
        type=DiscountType.VOUCHER,
    )

    order.total_gross_amount -= discount_amount
    order.total_net_amount -= discount_amount
    order.save(update_fields=["total_net_amount", "total_gross_amount"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_total = order.undiscounted_total_net_amount

    variables = {
        "id": order_id,
        "input": {
            "voucherCode": None,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]

    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert data["order"]["total"]["net"]["amount"] == order_total
    assert not data["order"]["voucher"]
    assert not data["order"]["voucherCode"]

    assert not data["errors"]
    order.refresh_from_db()
    assert not order.voucher
    assert order.search_vector

    assert not order.discounts.count()
    code_instance.refresh_from_db()
    assert code_instance.used == code_used - 1


def test_draft_order_update_with_voucher_and_voucher_code(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
):
    order = draft_order
    assert not order.voucher
    assert not order.voucher_code
    assert not order.customer_note
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    customer_note = "Test customer note"
    external_reference = "test-ext-ref"
    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
            "voucherCode": voucher.codes.first().code,
            "customerNote": customer_note,
            "externalReference": external_reference,
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
        },
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]
    assert error["field"] == "voucher"
    assert error["code"] == OrderErrorCode.INVALID.name
    assert (
        error["message"]
        == "You cannot use both a voucher and a voucher code for the same order. "
        "Please choose one."
    )


def test_draft_order_update_with_voucher_including_drafts_in_voucher_usage(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    # given
    order = draft_order
    assert not order.voucher
    assert not order.voucher_code
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    order_total = order.total_net_amount

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher.single_use = True
    voucher.save(update_fields=["single_use"])

    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert data["order"]["voucher"]["code"] == voucher.code
    assert data["order"]["voucherCode"] == voucher.code
    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert (
        data["order"]["total"]["net"]["amount"]
        == order_total - voucher_listing.discount_value
    )

    assert not data["errors"]
    order.refresh_from_db()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.voucher_code == voucher.code
    assert order.search_vector

    # Ensure order discount object was properly created
    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.voucher == voucher
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.value == voucher_listing.discount_value
    assert order_discount.amount_value == voucher_listing.discount_value

    code_instance = voucher.codes.first()
    assert code_instance.is_active is False


def test_draft_order_update_with_voucher_code_including_drafts_in_voucher_usage(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    # given
    order = draft_order
    assert not order.voucher
    assert not order.voucher_code
    assert not order.customer_note
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    order_total = order.total_net_amount

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher.single_use = True
    voucher.save(update_fields=["single_use"])

    code_instance = voucher.codes.first()

    variables = {
        "id": order_id,
        "input": {
            "voucherCode": code_instance.code,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert data["order"]["voucher"]["code"] == voucher.code
    assert data["order"]["voucherCode"] == voucher.code
    assert data["order"]["undiscountedTotal"]["net"]["amount"] == order_total
    assert (
        data["order"]["total"]["net"]["amount"]
        == order_total - voucher_listing.discount_value
    )

    assert not data["errors"]
    order.refresh_from_db()
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal.gross.amount
    assert order.voucher_code == voucher.code
    assert order.search_vector

    # Ensure order discount object was properly created
    assert order.discounts.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.voucher == voucher
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.value == voucher_listing.discount_value
    assert order_discount.amount_value == voucher_listing.discount_value

    code_instance.refresh_from_db()
    assert code_instance.is_active is False


def test_draft_order_update_voucher_including_drafts_in_voucher_usage_invalid_code(
    staff_api_client, permission_group_manage_orders, order_with_lines, voucher
):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()
    assert order.voucher is None
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    channel = order.channel
    channel.include_draft_order_in_voucher_usage = True
    channel.save(update_fields=["include_draft_order_in_voucher_usage"])

    voucher.single_use = True
    voucher.save(update_fields=["single_use"])

    code = voucher.codes.first()
    code.is_active = False
    code.save(update_fields=["is_active"])

    query = DRAFT_ORDER_UPDATE_MUTATION

    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]

    assert error["code"] == OrderErrorCode.INVALID_VOUCHER.name
    assert error["field"] == "voucher"


def test_draft_order_update_add_voucher_code_remove_order_promotion(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines_and_order_promotion,
    voucher,
):
    # given
    order = order_with_lines_and_order_promotion
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    order_discount = order.discounts.get()
    assert order_discount.type == DiscountType.ORDER_PROMOTION

    discount_amount = voucher.channel_listings.get(channel=order.channel).discount_value

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "voucherCode": voucher.codes.first().code,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    with pytest.raises(order_discount._meta.model.DoesNotExist):
        order_discount.refresh_from_db()

    order.refresh_from_db()
    voucher_discount = order.discounts.get()
    assert voucher_discount.amount_value == discount_amount
    assert voucher_discount.value == discount_amount
    assert voucher_discount.type == DiscountType.VOUCHER

    assert (
        order.total_net_amount == order.undiscounted_total_net_amount - discount_amount
    )


def test_draft_order_update_add_voucher_code_remove_gift_promotion(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines_and_gift_promotion,
    voucher,
):
    # given
    order = order_with_lines_and_gift_promotion
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    assert order.lines.count() == 3
    gift_line = order.lines.get(is_gift=True)
    gift_discount = gift_line.discounts.get()

    discount_amount = voucher.channel_listings.get(channel=order.channel).discount_value

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "voucherCode": voucher.codes.first().code,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    with pytest.raises(gift_line._meta.model.DoesNotExist):
        gift_line.refresh_from_db()

    with pytest.raises(gift_discount._meta.model.DoesNotExist):
        gift_discount.refresh_from_db()

    order.refresh_from_db()
    assert order.lines.count() == 2
    voucher_discount = order.discounts.get()
    assert voucher_discount.amount_value == discount_amount
    assert voucher_discount.value == discount_amount
    assert voucher_discount.type == DiscountType.VOUCHER

    assert (
        order.total_net_amount == order.undiscounted_total_net_amount - discount_amount
    )


def test_draft_order_update_remove_voucher_code_add_order_promotion(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
    order_promotion_rule,
):
    # given
    order = draft_order
    order.voucher = voucher
    order.save(update_fields=["voucher"])

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = voucher_listing.discount_value
    voucher_discount = order.discounts.create(
        voucher=voucher,
        value=discount_amount,
        type=DiscountType.VOUCHER,
    )

    order.total_gross_amount -= discount_amount
    order.total_net_amount -= discount_amount
    order.save(update_fields=["total_net_amount", "total_gross_amount"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "voucherCode": None,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    with pytest.raises(voucher_discount._meta.model.DoesNotExist):
        voucher_discount.refresh_from_db()

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


def test_draft_order_update_remove_voucher_code_add_gift_promotion(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
    gift_promotion_rule,
):
    # given
    order = draft_order
    order.voucher = voucher
    order.save(update_fields=["voucher"])
    assert order.lines.count() == 2

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = voucher_listing.discount_value
    voucher_discount = order.discounts.create(
        voucher=voucher,
        value=discount_amount,
        type=DiscountType.VOUCHER,
    )

    order.total_gross_amount -= discount_amount
    order.total_net_amount -= discount_amount
    order.save(update_fields=["total_net_amount", "total_gross_amount"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "voucherCode": None,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    with pytest.raises(voucher_discount._meta.model.DoesNotExist):
        voucher_discount.refresh_from_db()

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


def test_draft_order_update_with_non_draft_order(
    staff_api_client, permission_group_manage_orders, order_with_lines, voucher
):
    order = order_with_lines
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    customer_note = "Test customer note"
    variables = {
        "id": order_id,
        "input": {"voucher": voucher_id, "customerNote": customer_note},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderUpdate"]["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == OrderErrorCode.INVALID.name


def test_draft_order_update_invalid_address(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
):
    order = draft_order
    assert not order.voucher
    assert not order.customer_note
    graphql_address_data["postalCode"] = "TEST TEST invalid postal code 12345"
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    variables = {
        "id": order_id,
        "input": {
            "voucher": voucher_id,
            "shippingAddress": graphql_address_data,
        },
    }

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert len(data["errors"]) == 2
    assert not data["order"]
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.INVALID.name,
        OrderErrorCode.REQUIRED.name,
    }
    assert {error["field"] for error in data["errors"]} == {"postalCode"}


def test_draft_order_update_invalid_address_skip_validation(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    graphql_address_data_skipped_validation,
):
    # given
    order = draft_order
    address_data = graphql_address_data_skipped_validation
    invalid_postal_code = "invalid_postal_code"
    address_data["postalCode"] = invalid_postal_code
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    variables = {
        "id": order_id,
        "input": {
            "shippingAddress": address_data,
            "billingAddress": address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["shippingAddress"]["postalCode"] == invalid_postal_code
    assert data["order"]["billingAddress"]["postalCode"] == invalid_postal_code
    order.refresh_from_db()
    assert order.shipping_address.postal_code == invalid_postal_code
    assert order.shipping_address.validation_skipped is True
    assert order.billing_address.postal_code == invalid_postal_code
    assert order.billing_address.validation_skipped is True


def test_draft_order_update_by_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    draft_order,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    order = draft_order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    assert not order.customer_note

    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    customer_note = "Test customer note"
    variables = {
        "id": order_id,
        "input": {
            "customerNote": customer_note,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_draft_order_update_by_app(
    app_api_client, permission_manage_orders, draft_order, channel_PLN
):
    # given
    order = draft_order
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    assert not order.customer_note

    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    customer_note = "Test customer note"
    variables = {
        "id": order_id,
        "input": {
            "customerNote": customer_note,
        },
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    order.refresh_from_db()
    assert order.customer_note == customer_note
    assert order.search_vector


def test_draft_order_update_doing_nothing_generates_no_events(
    staff_api_client, permission_group_manage_orders, order_with_lines
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
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
    response = staff_api_client.post_graphql(query, {"id": order_id})
    get_graphql_content(response)

    # Ensure not event was created
    assert not OrderEvent.objects.exists()


def test_draft_order_update_free_shipping_voucher(
    staff_api_client, permission_group_manage_orders, draft_order, voucher_free_shipping
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    assert not order.voucher
    query = """
        mutation draftUpdate(
            $id: ID!
            $voucher: ID!
        ) {
            draftOrderUpdate(
                id: $id
                input: {
                    voucher: $voucher
                }
            ) {
                errors {
                    field
                    message
                    code
                }
                order {
                    id
                }
            }
        }
        """
    voucher = voucher_free_shipping
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "id": order_id,
        "voucher": voucher_id,
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["id"] == variables["id"]
    order.refresh_from_db()
    assert order.voucher


DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION = """
    mutation draftUpdate(
        $id: ID!
        $userEmail: String!
    ) {
        draftOrderUpdate(
            id: $id
            input: {
                userEmail: $userEmail
            }
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
        }
    }
    """


def test_draft_order_update_when_not_existing_customer_email_provided(
    staff_api_client, permission_group_manage_orders, draft_order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    assert order.user

    query = DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    email = "notexisting@example.com"
    variables = {"id": order_id, "userEmail": email}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert not order.user
    assert order.user_email == email


def test_draft_order_update_assign_user_when_existing_customer_email_provided(
    staff_api_client, permission_group_manage_orders, draft_order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    user = order.user
    user_email = user.email
    order.user = None
    order.save(update_fields=["user"])
    assert not order.user

    query = DRAFT_ORDER_UPDATE_USER_EMAIL_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "userEmail": user_email}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert order.user == user
    assert order.user_email == user_email


DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE = """
    mutation draftUpdate(
        $id: ID
        $externalReference: String
        $input: DraftOrderInput!
    ) {
        draftOrderUpdate(
            id: $id
            externalReference: $externalReference
            input: $input
        ) {
            errors {
                field
                message
                code
            }
            order {
                id
                externalReference
                voucher {
                    id
                }
            }
        }
    }
    """


def test_draft_order_update_by_external_reference(
    staff_api_client, permission_group_manage_orders, draft_order, voucher_free_shipping
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    order = draft_order
    assert not order.voucher
    voucher = voucher_free_shipping
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    ext_ref = "test-ext-ref"
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])

    variables = {
        "externalReference": ext_ref,
        "input": {"voucher": voucher_id},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["externalReference"] == ext_ref
    assert data["order"]["id"] == graphene.Node.to_global_id("Order", order.id)
    assert data["order"]["voucher"]["id"] == voucher_id
    order.refresh_from_db()
    assert order.voucher


def test_draft_order_update_by_both_id_and_external_reference(
    staff_api_client, permission_group_manage_orders, voucher_free_shipping
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    variables = {
        "id": "test-id",
        "externalReference": "test-ext-ref",
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["order"]
    assert (
        data["errors"][0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_draft_order_update_by_external_reference_not_existing(
    staff_api_client, permission_group_manage_orders, voucher_free_shipping
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {
        "externalReference": ext_ref,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["order"]
    assert data["errors"][0]["message"] == f"Couldn't resolve to a node: {ext_ref}"


def test_draft_order_update_with_non_unique_external_reference(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    order_list,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    draft_order_id = graphene.Node.to_global_id("Order", draft_order.pk)
    ext_ref = "test-ext-ref"
    order = order_list[1]
    order.external_reference = ext_ref
    order.save(update_fields=["external_reference"])

    variables = {"id": draft_order_id, "input": {"externalReference": ext_ref}}

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    error = content["data"]["draftOrderUpdate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == OrderErrorCode.UNIQUE.name
    assert error["message"] == "Order with this External reference already exists."


DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION = """
    mutation draftUpdate($id: ID!, $shippingMethod: ID){
        draftOrderUpdate(
            id: $id,
            input: {
                shippingMethod: $shippingMethod
            }) {
            errors {
                field
                message
                code
            }
            order {
                shippingMethodName
                shippingPrice {
                net {
                        amount
                    }
                    gross {
                        amount
                    }
                tax {
                    amount
                    }
                    net {
                        amount
                    }
                    gross {
                        amount
                    }
                }
            shippingTaxRate
            userEmail
            }
        }
    }
"""


def test_draft_order_update_shipping_method_from_different_channel(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    address_usa,
    shipping_method_channel_PLN,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    base_shipping_price = order.base_shipping_price
    order.shipping_address = address_usa
    order.save(update_fields=["shipping_address"])
    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method_channel_PLN.id
    )
    variables = {"id": order_id, "shippingMethod": shipping_method_id}
    # when
    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]

    # then
    assert len(data["errors"]) == 1
    assert not data["order"]
    error = data["errors"][0]
    assert error["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert error["field"] == "shippingMethod"

    order.refresh_from_db()
    assert order.undiscounted_base_shipping_price == base_shipping_price
    assert order.base_shipping_price == base_shipping_price


def test_draft_order_update_shipping_method_prices_updates(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    address_usa,
    shipping_method,
    shipping_method_weight_based,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.shipping_address = address_usa
    order.shipping_method = shipping_method
    order.save(update_fields=["shipping_address", "shipping_method"])
    assert shipping_method.channel_listings.first().price_amount == 10

    shipping_price = 15
    method_2 = shipping_method_weight_based
    m2_channel_listing = method_2.channel_listings.first()
    m2_channel_listing.price_amount = shipping_price
    m2_channel_listing.save(update_fields=["price_amount"])
    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    shipping_method_id = graphene.Node.to_global_id("ShippingMethod", method_2.id)
    variables = {"id": order_id, "shippingMethod": shipping_method_id}

    # when
    response = staff_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert data["order"]["shippingMethodName"] == method_2.name
    assert data["order"]["shippingPrice"]["net"]["amount"] == 15.0

    order.refresh_from_db()
    assert order.undiscounted_base_shipping_price_amount == shipping_price
    assert order.base_shipping_price_amount == shipping_price


def test_draft_order_update_shipping_method_clear_with_none(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    address_usa,
    shipping_method,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.shipping_address = address_usa
    order.shipping_method = shipping_method
    order.save(update_fields=["shipping_address", "shipping_method"])
    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "shippingMethod": None}
    zero_shipping_price_data = {
        "tax": {"amount": 0.0},
        "net": {"amount": 0.0},
        "gross": {"amount": 0.0},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    order.refresh_from_db()

    # then
    assert not data["errors"]
    assert data["order"]["shippingMethodName"] is None
    assert data["order"]["shippingPrice"] == zero_shipping_price_data
    assert data["order"]["shippingTaxRate"] == 0.0
    assert order.shipping_method is None

    assert order.undiscounted_base_shipping_price == zero_money(order.currency)
    assert order.base_shipping_price == zero_money(order.currency)

    assert not order.shipping_tax_class
    assert not order.shipping_tax_class_name
    assert not order.shipping_tax_class_private_metadata
    assert not order.shipping_tax_class_metadata


def test_draft_order_update_shipping_method(
    staff_api_client, permission_group_manage_orders, draft_order, shipping_method
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.shipping_method = None
    order.base_shipping_price = zero_money(order.currency)
    order.save()

    shipping_tax_class = shipping_method.tax_class
    shipping_tax_class.private_metadata = {"key": "value"}
    shipping_tax_class.metadata = {"key": "value"}
    shipping_tax_class.save()

    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {
        "id": order_id,
        "shippingMethod": method_id,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    order.refresh_from_db()

    shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).get_total()
    shipping_price = TaxedMoney(shipping_total, shipping_total)

    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    assert data["order"]["shippingMethodName"] == shipping_method.name
    assert data["order"]["shippingPrice"]["net"]["amount"] == quantize_price(
        shipping_price.net.amount, shipping_price.currency
    )
    assert data["order"]["shippingPrice"]["gross"]["amount"] == quantize_price(
        shipping_price.gross.amount, shipping_price.currency
    )

    assert order.base_shipping_price == shipping_total
    assert order.shipping_method == shipping_method
    assert order.undiscounted_base_shipping_price == shipping_total
    assert order.shipping_price_net == shipping_price.net
    assert order.shipping_price_gross == shipping_price.gross

    assert order.shipping_tax_class == shipping_tax_class
    assert order.shipping_tax_class_name == shipping_tax_class.name
    assert (
        order.shipping_tax_class_private_metadata == shipping_tax_class.private_metadata
    )
    assert order.shipping_tax_class_metadata == shipping_tax_class.metadata


def test_draft_order_update_sets_shipping_tax_details_to_none_when_default_tax_used(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    shipping_method,
    other_shipping_method,
):
    # given
    shipping_tax_class = shipping_method.tax_class
    shipping_tax_class.private_metadata = {"key": "value"}
    shipping_tax_class.metadata = {"key": "value"}
    shipping_tax_class.save()

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.shipping_method = shipping_method
    order.base_shipping_price = zero_money(order.currency)
    order.shipping_tax_class = shipping_tax_class
    order.shipping_tax_class_name = shipping_tax_class.name
    order.shipping_tax_class_private_metadata = shipping_tax_class.private_metadata
    order.shipping_tax_class_metadata = shipping_tax_class.metadata
    order.save()

    assert not other_shipping_method.tax_class

    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", other_shipping_method.id)
    variables = {
        "id": order_id,
        "shippingMethod": method_id,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["shippingMethodName"] == other_shipping_method.name

    order.refresh_from_db()
    assert order.shipping_method == other_shipping_method
    assert order.shipping_method_name == other_shipping_method.name

    assert not order.shipping_tax_class
    assert not order.shipping_tax_class_name
    assert not order.shipping_tax_class_private_metadata
    assert not order.shipping_tax_class_metadata


def test_draft_order_update_shipping_method_order_with_shipping_voucher(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    shipping_method,
    voucher_free_shipping,
    channel_USD,
):
    # given
    voucher = voucher_free_shipping
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order

    # clear shipping data
    order.shipping_method = None
    order.undiscounted_base_shipping_price_amount = 0
    order.base_shipping_price_amount = 0
    order.shipping_price_gross_amount = 0
    order.shipping_price_net_amount = 0

    order.voucher = voucher
    order.save()

    # create shipping voucher discount
    voucher_reward = 50
    voucher.channel_listings.filter(channel=channel_USD).update(
        discount_value=voucher_reward
    )
    create_or_update_voucher_discount_objects_for_order(order)

    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {
        "id": order_id,
        "shippingMethod": method_id,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    order.refresh_from_db()

    undiscounted_shipping_total = shipping_method.channel_listings.get(
        channel_id=order.channel_id
    ).price
    shipping_total = undiscounted_shipping_total * voucher_reward / 100
    shipping_price = TaxedMoney(shipping_total, shipping_total)

    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    assert data["order"]["shippingMethodName"] == shipping_method.name
    assert data["order"]["shippingPrice"]["net"]["amount"] == quantize_price(
        shipping_price.net.amount, shipping_price.currency
    )
    assert data["order"]["shippingPrice"]["gross"]["amount"] == quantize_price(
        shipping_price.gross.amount, shipping_price.currency
    )

    assert order.base_shipping_price == shipping_total
    assert order.shipping_method == shipping_method
    assert order.undiscounted_base_shipping_price == undiscounted_shipping_total
    assert order.shipping_price_net == shipping_price.net
    assert order.shipping_price_gross == shipping_price.gross


def test_draft_order_update_no_shipping_method_channel_listings(
    staff_api_client, permission_group_manage_orders, draft_order, shipping_method
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.shipping_method = None
    order.base_shipping_price = zero_money(order.currency)
    order.save()

    shipping_method.channel_listings.all().delete()

    query = DRAFT_ORDER_UPDATE_SHIPPING_METHOD_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    method_id = graphene.Node.to_global_id("ShippingMethod", shipping_method.id)
    variables = {
        "id": order_id,
        "shippingMethod": method_id,
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    assert errors[0]["field"] == "shippingMethod"


def test_draft_order_update_order_promotion(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    graphql_address_data,
    variant_with_many_stocks,
    channel_USD,
    draft_order,
    order_promotion_rule,
):
    # given
    query = DRAFT_ORDER_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    rule = order_promotion_rule
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    assert rule.reward_value_type == RewardValueType.PERCENTAGE
    reward_value = rule.reward_value

    variables = {
        "id": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {
            "billingAddress": graphql_address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderUpdate"]["errors"]
    draft_order.refresh_from_db()
    undiscounted_total = draft_order.undiscounted_total_net_amount
    shipping_price = draft_order.base_shipping_price_amount
    order = content["data"]["draftOrderUpdate"]["order"]
    assert len(order["discounts"]) == 1
    discount_amount = reward_value / 100 * (undiscounted_total - shipping_price)
    discount = order["discounts"][0]
    assert discount["amount"]["amount"] == discount_amount
    assert discount["total"]["amount"] == discount_amount
    assert discount["reason"] == f"Promotion: {promotion_id}"
    assert discount["type"] == DiscountType.ORDER_PROMOTION.upper()
    assert discount["valueType"] == RewardValueType.PERCENTAGE.upper()

    assert (
        order["subtotal"]["net"]["amount"]
        == undiscounted_total - discount_amount - shipping_price
    )
    assert order["total"]["net"]["amount"] == undiscounted_total - discount_amount
    assert order["undiscountedTotal"]["net"]["amount"] == undiscounted_total


def test_draft_order_update_gift_promotion(
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    shipping_method,
    graphql_address_data,
    variant_with_many_stocks,
    channel_USD,
    draft_order,
    gift_promotion_rule,
):
    # given
    query = DRAFT_ORDER_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    rule = gift_promotion_rule
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)

    variables = {
        "id": graphene.Node.to_global_id("Order", draft_order.pk),
        "input": {
            "billingAddress": graphql_address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderUpdate"]["errors"]

    gift_line_db = [line for line in draft_order.lines.all() if line.is_gift][0]
    gift_price = gift_line_db.variant.channel_listings.get(
        channel=draft_order.channel
    ).price_amount

    order = content["data"]["draftOrderUpdate"]["order"]
    lines = order["lines"]
    assert len(lines) == 3
    gift_line = [line for line in lines if line["isGift"]][0]

    expected_discount_reason = f"Promotion: {promotion_id}"

    assert gift_line["totalPrice"]["net"]["amount"] == 0.00
    assert gift_line["unitDiscount"]["amount"] == gift_price
    assert gift_line["unitDiscountReason"] == expected_discount_reason
    assert gift_line["unitDiscountType"] == RewardValueType.FIXED.upper()
    assert gift_line["unitDiscountValue"] == gift_price

    assigned_discount_objects = gift_line["discounts"]
    assert len(assigned_discount_objects) == 1
    assigned_discount = assigned_discount_objects[0]
    assert assigned_discount["reason"] == expected_discount_reason
    assert assigned_discount["valueType"] == RewardValueType.FIXED.upper()
    assert assigned_discount["total"]["amount"] == gift_price
    assert assigned_discount["unit"]["amount"] == gift_price
    assert assigned_discount["value"] == gift_price

    assert (
        order["subtotal"]["net"]["amount"]
        == draft_order.undiscounted_total_net_amount
        - draft_order.base_shipping_price_amount
    )
    assert order["total"]["net"]["amount"] == draft_order.undiscounted_total_net_amount
    assert (
        order["undiscountedTotal"]["net"]["amount"]
        == draft_order.undiscounted_total_net_amount
    )


def test_draft_order_update_with_cc_warehouse_as_shipping_method(
    staff_api_client, permission_group_manage_orders, order_with_lines, warehouse_for_cc
):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    cc_warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse_for_cc.id)

    variables = {
        "id": order_id,
        "input": {"shippingMethod": cc_warehouse_id},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == OrderErrorCode.INVALID.name
    assert errors[0]["field"] == "shippingMethod"


def test_draft_order_update_undiscounted_base_shipping_price_set(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {
        "id": order_id,
        "input": {
            "billingAddress": graphql_address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderUpdate"]["errors"]

    order.refresh_from_db()
    assert (
        order.undiscounted_base_shipping_price_amount
        == order.base_shipping_price_amount
    )


def test_draft_order_update_ensure_entire_order_voucher_discount_is_overridden(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
    channel_USD,
):
    # given
    query = DRAFT_ORDER_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order = draft_order
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.discount_value_type == DiscountValueType.FIXED

    # apply voucher to order
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.save(update_fields=["voucher_id", "voucher_code"])

    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in order.lines.all():
        undiscounted_subtotal += line.base_unit_price * line.quantity

    voucher_listing = voucher.channel_listings.get(channel=channel_USD)
    discount_value = voucher_listing.discount_value

    order_discount = order.discounts.create(
        voucher=voucher,
        value=discount_value,
        value_type=DiscountValueType.FIXED,
        type=DiscountType.VOUCHER,
    )

    # create new voucher
    new_discount_value = Decimal(50)
    new_code = "new_code"
    new_voucher = Voucher.objects.create(
        type=VoucherType.ENTIRE_ORDER,
        name="new voucher",
        discount_value_type=DiscountValueType.PERCENTAGE,
    )
    new_voucher.codes.create(code=new_code)
    new_voucher.channel_listings.create(
        channel=channel_USD,
        discount_value=new_discount_value,
    )

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "input": {"voucherCode": new_code}}

    # when apply new voucher to order
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["voucher"]["code"] == new_code
    assert data["order"]["voucherCode"] == new_code
    assert data["order"]["subtotal"]["gross"]["amount"] == Decimal(
        undiscounted_subtotal.amount / 2
    )

    order.refresh_from_db()
    assert order.voucher_code == new_code

    order_discount.refresh_from_db()
    assert order.discounts.count() == 1
    assert order.discounts.first() == order_discount
    assert order_discount.voucher == new_voucher
    assert order_discount.voucher_code == new_code
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.value_type == DiscountValueType.PERCENTAGE
    assert order_discount.value == new_discount_value
    assert order_discount.amount_value == Decimal(undiscounted_subtotal.amount / 2)


def test_draft_order_update_remove_entire_order_voucher(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
    graphql_address_data,
    channel_USD,
):
    # given
    query = DRAFT_ORDER_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order = draft_order
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.discount_value_type == DiscountValueType.FIXED

    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.save(update_fields=["voucher_id", "voucher_code"])

    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in order.lines.all():
        undiscounted_subtotal += line.base_unit_price * line.quantity

    voucher_listing = voucher.channel_listings.get(channel=channel_USD)
    discount_value = voucher_listing.discount_value

    order_discount = order.discounts.create(
        voucher=voucher,
        value=discount_value,
        value_type=DiscountValueType.FIXED,
        type=DiscountType.VOUCHER,
    )

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "input": {"voucherCode": None}}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert not data["order"]["voucher"]
    assert not data["order"]["voucherCode"]
    assert data["order"]["subtotal"]["gross"]["amount"] == undiscounted_subtotal.amount

    order.refresh_from_db()
    assert order.voucher_code is None
    assert order.voucher is None

    with pytest.raises(OrderDiscount.DoesNotExist):
        order_discount.refresh_from_db()


def test_draft_order_update_replace_entire_order_voucher_with_shipping_voucher(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher_percentage,
    voucher_shipping_type,
    graphql_address_data,
    channel_USD,
):
    # given
    query = DRAFT_ORDER_UPDATE_MUTATION
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order = draft_order
    voucher = voucher_percentage
    assert voucher.type == VoucherType.ENTIRE_ORDER

    order.voucher = voucher
    entire_order_code = voucher.codes.first().code
    order.voucher_code = entire_order_code
    order.save(update_fields=["voucher_id", "voucher_code"])

    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in order.lines.all():
        undiscounted_subtotal += line.base_unit_price * line.quantity

    voucher_listing = voucher.channel_listings.get(channel=channel_USD)
    discount_value = voucher_listing.discount_value

    order_discount = order.discounts.create(
        voucher=voucher,
        value=discount_value,
        value_type=DiscountValueType.FIXED,
        type=DiscountType.VOUCHER,
    )

    undiscounted_shipping_price = order.base_shipping_price
    shipping_code = voucher_shipping_type.codes.first().code
    assert shipping_code != entire_order_code
    shipping_discount = voucher_shipping_type.channel_listings.get(
        channel=channel_USD
    ).discount_value
    expected_shipping_price = undiscounted_shipping_price.amount - shipping_discount
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "input": {"voucherCode": shipping_code}}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    assert data["order"]["voucher"]["code"] == shipping_code
    assert data["order"]["voucherCode"] == shipping_code
    assert data["order"]["subtotal"]["gross"]["amount"] == undiscounted_subtotal.amount
    assert data["order"]["shippingPrice"]["gross"]["amount"] == expected_shipping_price
    assert (
        data["order"]["total"]["gross"]["amount"]
        == undiscounted_subtotal.amount + expected_shipping_price
    )

    order.refresh_from_db()
    assert order.voucher_code == shipping_code
    assert order.voucher == voucher_shipping_type

    order_discount.refresh_from_db()
    discounts = order.discounts.all()
    assert len(discounts) == 1
    assert discounts[0] == order_discount
    assert order_discount.voucher == voucher_shipping_type
    assert order_discount.value_type == voucher_shipping_type.discount_value_type
    assert order_discount.value == discount_value
    assert order_discount.amount_value == shipping_discount
    assert order_discount.reason == f"Voucher code: {shipping_code}"
    assert voucher_shipping_type.name is None
    assert order_discount.name == ""
    assert order_discount.type == DiscountType.VOUCHER
    assert order_discount.voucher_code == shipping_code


@patch(
    "saleor.graphql.order.mutations.draft_order_update.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_draft_order_update_triggers_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    voucher,
    app_api_client,
    permission_manage_orders,
    draft_order,
    settings,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        draft_order_updated_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.DRAFT_ORDER_UPDATED)

    order = draft_order
    order.voucher = voucher
    order.save(update_fields=["voucher"])

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = voucher_listing.discount_value
    order.discounts.create(
        voucher=voucher,
        value=discount_amount,
        type=DiscountType.VOUCHER,
    )

    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {
        "id": order_id,
        "input": {
            "voucher": None,
        },
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    order.refresh_from_db()

    # confirm that event delivery was generated for each async webhook.
    draft_order_updated_delivery = EventDelivery.objects.get(
        webhook_id=draft_order_updated_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": draft_order_updated_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=draft_order_updated_webhook.id
    ).exists()

    tax_delivery_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )

    assert wrapped_call_order_event.called


@patch(
    "saleor.graphql.order.mutations.draft_order_update.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_draft_order_update_triggers_webhooks_when_tax_webhook_not_needed(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    voucher,
    app_api_client,
    permission_manage_orders,
    draft_order,
    settings,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        draft_order_updated_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.DRAFT_ORDER_UPDATED)

    order = draft_order

    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {
        "id": order_id,
        "input": {
            "customerNote": "New note",
        },
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]
    order.refresh_from_db()

    assert not order.should_refresh_prices

    # confirm that event delivery was generated for each async webhook.
    draft_order_updated_delivery = EventDelivery.objects.get(
        webhook_id=draft_order_updated_webhook.id
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={
            "event_delivery_id": draft_order_updated_delivery.id,
            "telemetry_context": ANY,
        },
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    mocked_send_webhook_request_sync.assert_called_once()
    assert not EventDelivery.objects.exclude(
        webhook_id=draft_order_updated_webhook.id
    ).exists()

    filter_shipping_call = mocked_send_webhook_request_sync.mock_calls[0]

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    assert wrapped_call_order_event.called


def test_draft_order_update_address_reset_save_address_flag_to_default_value(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    graphql_address_data,
):
    order = draft_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # given draft order billing and billing address set both save billing flags
    # different than default value - set to True
    order.draft_save_billing_address = True
    order.draft_save_shipping_address = True
    order.save(
        update_fields=["draft_save_billing_address", "draft_save_shipping_address"]
    )

    # when addresses are updated without providing save address flags
    variables = {
        "id": graphene.Node.to_global_id("Order", order.id),
        "input": {
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
        },
    }

    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)

    # then the addresses are set and save address flags are set to default value
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert data["order"]

    order.refresh_from_db()
    assert order.shipping_address
    assert order.billing_address
    assert order.draft_save_billing_address is False
    assert order.draft_save_shipping_address is False


@pytest.mark.parametrize(
    ("save_shipping_address", "save_billing_address"),
    [(True, True), (True, False), (False, True), (False, False)],
)
def test_draft_order_update_address_save_addresses_setting_provided(
    save_shipping_address,
    save_billing_address,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    graphql_address_data,
):
    # given
    order = draft_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when addresses are updated with providing save address flags
    variables = {
        "id": graphene.Node.to_global_id("Order", order.id),
        "input": {
            "shippingAddress": graphql_address_data,
            "billingAddress": graphql_address_data,
            "saveShippingAddress": save_shipping_address,
            "saveBillingAddress": save_billing_address,
        },
    }
    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)

    # then the addresses with save settings are set
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert data["order"]

    order.refresh_from_db()
    assert order.shipping_address
    assert order.billing_address
    assert order.draft_save_billing_address == save_billing_address
    assert order.draft_save_shipping_address == save_shipping_address


@pytest.mark.parametrize(
    "save_shipping_address",
    [True, False],
)
def test_draft_order_update_no_shipping_address_save_addresses_raising_error(
    save_shipping_address,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
):
    # given
    order = draft_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    #  when only save address flag is provided
    variables = {
        "id": graphene.Node.to_global_id("Order", order.id),
        "input": {
            "saveShippingAddress": save_shipping_address,
        },
    }
    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)

    # then the error is raised
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["order"]
    errors = data["errors"]
    assert len(errors) == 1

    error = errors[0]
    assert error["field"] == "saveShippingAddress"
    assert error["code"] == OrderErrorCode.MISSING_ADDRESS_DATA.name


@pytest.mark.parametrize(
    "save_billing_address",
    [True, False],
)
def test_draft_order_update_no_billing_address_save_addresses_raising_error(
    save_billing_address,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
):
    # given
    order = draft_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when only save address flag is provided
    variables = {
        "id": graphene.Node.to_global_id("Order", order.id),
        "input": {
            "saveBillingAddress": save_billing_address,
        },
    }
    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)

    # then the error is raised
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["order"]
    errors = data["errors"]
    assert len(errors) == 1

    error = errors[0]
    assert error["field"] == "saveBillingAddress"
    assert error["code"] == OrderErrorCode.MISSING_ADDRESS_DATA.name


def test_draft_order_update_with_metadata(
    app_api_client, permission_manage_orders, draft_order, channel_PLN
):
    # given
    order = draft_order
    order.channel = channel_PLN
    order.metadata = []
    order.private_metadata = []

    order.save(update_fields=["channel", "private_metadata", "metadata"])

    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)

    public_metadata_key = "public metadata key"
    public_metadata_value = "public metadata value"
    private_metadata_key = "private metadata key"
    private_metadata_value = "private metadata value"

    variables = {
        "id": order_id,
        "input": {
            "metadata": [
                {
                    "key": public_metadata_key,
                    "value": public_metadata_value,
                }
            ],
            "privateMetadata": [
                {
                    "key": private_metadata_key,
                    "value": private_metadata_value,
                }
            ],
        },
    }

    # when
    response = app_api_client.post_graphql(
        query, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]

    assert not data["errors"]

    metadata_result_list: list[dict[str, str]] = data["order"]["metadata"]
    private_metadata_result_list: list[dict[str, str]] = data["order"][
        "privateMetadata"
    ]

    assert len(metadata_result_list) == 1
    assert len(private_metadata_result_list) == 1

    assert metadata_result_list[0]["key"] == public_metadata_key
    assert metadata_result_list[0]["value"] == public_metadata_value

    assert private_metadata_result_list[0]["key"] == private_metadata_key
    assert private_metadata_result_list[0]["value"] == private_metadata_value


def test_draft_order_update_with_voucher_specific_product_and_manual_line_discount(
    order_with_lines,
    voucher_specific_product_type,
    staff_api_client,
    permission_group_manage_orders,
    tax_configuration_flat_rates,
    plugins_manager,
):
    """Manual line discount takes precedence over vouchers."""
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    order_id = graphene.Node.to_global_id("Order", order.id)
    voucher = voucher_specific_product_type
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    voucher_discount_value = Decimal(2)
    voucher_listing.discount_value = voucher_discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)

    # create manual order line discount
    manual_line_discount_value = Decimal(3)
    update_discount_for_order_line(
        discounted_line,
        order=order,
        reason="Manual line discount",
        value_type=DiscountValueType.FIXED,
        value=manual_line_discount_value,
    )
    fetch_order_prices_if_expired(order, plugins_manager, None, True)

    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "id": order_id,
        "input": {
            "voucherCode": voucher.codes.first().code,
        },
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    discounted_line.refresh_from_db()
    line_1.refresh_from_db()

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


def test_draft_order_update_with_voucher_apply_once_per_order_and_manual_line_discount(
    order_with_lines,
    voucher,
    staff_api_client,
    permission_group_manage_orders,
    tax_configuration_flat_rates,
    plugins_manager,
):
    """Manual line discount takes precedence over vouchers."""
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])
    order_id = graphene.Node.to_global_id("Order", order.id)
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    voucher_discount_value = Decimal(3)
    voucher_listing.discount_value = voucher_discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    lines = order.lines.all()
    discounted_line, line_1 = lines

    # create manual order line discount
    manual_line_discount_value = Decimal(3)
    update_discount_for_order_line(
        discounted_line,
        order=order,
        reason="Manual line discount",
        value_type=DiscountValueType.FIXED,
        value=manual_line_discount_value,
    )
    fetch_order_prices_if_expired(order, plugins_manager, None, True)

    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "id": order_id,
        "input": {
            "voucherCode": voucher.codes.first().code,
        },
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    discounted_line.refresh_from_db()
    line_1.refresh_from_db()

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


@patch(
    "saleor.graphql.order.mutations.draft_order_update.update_order_search_vector",
)
@patch(
    "saleor.graphql.order.mutations.draft_order_update.call_order_event",
    wraps=call_order_event,
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_draft_order_update_nothing_changed(
    wrapped_call_order_event,
    mocked_update_order_search_vector,
    setup_order_webhooks,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    settings,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.save()

    (
        tax_webhook,
        shipping_filter_webhook,
        draft_order_updated_webhook,
    ) = setup_order_webhooks(WebhookEventAsyncType.DRAFT_ORDER_UPDATED)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {
        "id": order_id,
        "input": {
            "userEmail": order.user_email,
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    # ensure the update fields were empty
    mocked_update_order_search_vector.assert_not_called()

    # confirm that order events were not triggered
    assert not wrapped_call_order_event.called

    # confirm that event delivery was generated for each async webhook.
    assert not EventDelivery.objects.filter(webhook_id=draft_order_updated_webhook.id)


def test_draft_order_update_with_language_code(
    staff_api_client, permission_group_manage_orders, draft_order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    query = DRAFT_ORDER_UPDATE_BY_EXTERNAL_REFERENCE

    order = draft_order
    order_id = graphene.Node.to_global_id("Order", order.id)

    assert not order.language_code == "pl"

    variables = {
        "id": order_id,
        "input": {"languageCode": "PL"},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderUpdate"]
    assert not data["errors"]

    order.refresh_from_db()

    assert order.language_code == "pl"


@patch(
    "saleor.graphql.order.mutations.draft_order_update.call_order_event",
    wraps=call_order_event,
)
@patch(
    "saleor.graphql.order.mutations.draft_order_update.DraftOrderUpdate._save_order_instance"
)
def test_draft_order_update_no_changes(
    save_order_mock,
    call_event_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    voucher,
    address,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order_id = graphene.Node.to_global_id("Order", order.id)

    key = "some_key"
    value = "some_value"
    address.metadata = {key: value}
    address.save(update_fields=["metadata"])

    order.metadata = {key: value}
    order.private_metadata = {key: value}
    order.shipping_address = address
    order.billing_address = address
    order.draft_save_billing_address = True
    order.draft_save_shipping_address = True
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.customer_note = "some note"
    order.redirect_url = "https://www.example.com"
    order.external_reference = "some_reference_string"
    order.language_code = "pl"
    order.save()

    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", order.shipping_method_id
    )
    user_id = graphene.Node.to_global_id("User", order.user_id)

    address_input = {
        snake_to_camel_case(key): value for key, value in address.as_data().items()
    }
    address_input["metadata"] = [{"key": key, "value": value}]
    address_input.pop("privateMetadata")
    skip_validation = address_input.pop("validationSkipped")
    address_input["skipValidation"] = skip_validation

    input_fields = [
        snake_to_camel_case(key) for key in DraftOrderInput._meta.fields.keys()
    ]

    # `discount` field is unused and deprecated
    input_fields.remove("discount")
    # `voucher` and `voucherCode` fields can't be combined
    input_fields.remove("voucher")
    # `channel` can't be updated when is not None
    input_fields.remove("channelId")

    input = {
        "billingAddress": address_input,
        "saveBillingAddress": True,
        "shippingAddress": address_input,
        "saveShippingAddress": True,
        "shippingMethod": shipping_method_id,
        "user": user_id,
        "userEmail": order.user_email,
        "voucherCode": order.voucher_code,
        "customerNote": order.customer_note,
        "redirectUrl": order.redirect_url,
        "externalReference": order.external_reference,
        "metadata": [{"key": key, "value": value}],
        "privateMetadata": [{"key": key, "value": value}],
        "languageCode": "PL",
    }
    assert set(input_fields) == set(input.keys())

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": order_id, "input": input}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderUpdate"]["errors"]
    order.refresh_from_db()
    save_order_mock.assert_not_called()
    call_event_mock.assert_not_called()


@patch(
    "saleor.graphql.order.mutations.draft_order_update.call_order_event",
    wraps=call_order_event,
)
@patch(
    "saleor.graphql.order.mutations.draft_order_update.DraftOrderUpdate._save_order_instance"
)
def test_draft_order_update_emit_events(
    save_order_mock,
    call_event_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
    voucher,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order_id = graphene.Node.to_global_id("Order", order.id)

    key = "some_key"
    value = "some_value"
    order.metadata = {key: value}
    order.private_metadata = {key: value}
    order.draft_save_billing_address = True
    order.draft_save_shipping_address = True
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.customer_note = "some note"
    order.redirect_url = "http://localhost:8000/redirect"
    order.external_reference = "some_reference_string"
    order.language_code = "de"
    order.save()

    new_shipping_method = ShippingMethod.objects.create(
        shipping_zone=order.shipping_method.shipping_zone,
        name="new_method",
    )
    new_shipping_method.channel_listings.create(
        channel=order.channel, currency=order.currency
    )
    new_shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", new_shipping_method.id
    )

    assert order.user_id != staff_api_client.user.id
    user_id = graphene.Node.to_global_id("User", staff_api_client.user.id)

    input_fields = [
        snake_to_camel_case(key) for key in DraftOrderInput._meta.fields.keys()
    ]

    # `discount` field is unused and deprecated
    input_fields.remove("discount")
    # `voucher` and `voucherCode` fields can't be combined
    input_fields.remove("voucher")
    # `channel` can't be updated when is not None
    input_fields.remove("channelId")
    # `saveBillingAddress` can't be provided without billingAddress
    input_fields.remove("saveBillingAddress")
    # `saveShippingAddress` can't be provided without shippingAddress
    input_fields.remove("saveShippingAddress")

    assert graphql_address_data["lastName"] != order.shipping_address.last_name
    assert graphql_address_data["lastName"] != order.billing_address.last_name

    input = {
        "billingAddress": graphql_address_data,
        "shippingAddress": graphql_address_data,
        "shippingMethod": new_shipping_method_id,
        "user": user_id,
        "userEmail": "new_" + order.user_email,
        "voucherCode": voucher.codes.last().code,
        "customerNote": order.customer_note + "_new",
        "redirectUrl": "https://www.example.com",
        "externalReference": order.external_reference + "_new",
        "metadata": [{"key": key, "value": "new_value"}],
        "privateMetadata": [{"key": "new_key", "value": value}],
        "languageCode": "PL",
    }
    assert set(input_fields) == set(input.keys())

    # fields making changes to related models (other than order)
    non_base_model_fields = ["billingAddress", "shippingAddress"]
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    for key, value in input.items():
        variables = {"id": order_id, "input": {key: value}}

        # when
        response = staff_api_client.post_graphql(
            DRAFT_ORDER_UPDATE_MUTATION,
            variables,
        )
        content = get_graphql_content(response)

        # then
        assert not content["data"]["draftOrderUpdate"]["errors"]
        if key not in non_base_model_fields:
            save_order_mock.assert_called()
            save_order_mock.reset_mock()
        call_event_mock.assert_called()
        call_event_mock.reset_mock()


@patch(
    "saleor.graphql.order.mutations.draft_order_update.call_order_event",
    wraps=call_order_event,
)
def test_draft_order_update_address_not_changed_save_flag_changed(
    call_event_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    address,
):
    """Address input doesn't introduce any changes, but address save flag has changed."""
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order_id = graphene.Node.to_global_id("Order", order.id)

    order.shipping_address = address
    order.billing_address = address
    order.draft_save_billing_address = False
    order.draft_save_shipping_address = False
    order.save(
        update_fields=[
            "shipping_address",
            "billing_address",
            "draft_save_billing_address",
            "draft_save_shipping_address",
            "status",
        ]
    )

    address_input = {
        snake_to_camel_case(key): value for key, value in address.as_data().items()
    }
    address_input.pop("privateMetadata")
    skip_validation = address_input.pop("validationSkipped")
    address_input["skipValidation"] = skip_validation

    input = {
        "billingAddress": address_input,
        "saveBillingAddress": True,
        "shippingAddress": address_input,
        "saveShippingAddress": True,
    }

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": order_id, "input": input}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderUpdate"]["errors"]
    order.refresh_from_db()
    assert order.draft_save_billing_address is True
    assert order.draft_save_shipping_address is True
    call_event_mock.assert_called()


@patch(
    "saleor.graphql.order.mutations.draft_order_update.call_order_event",
    wraps=call_order_event,
)
def test_draft_order_update_address_not_set(
    call_event_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    graphql_address_data,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.shipping_address = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "billing_address", "status"])

    order_id = graphene.Node.to_global_id("Order", order.id)

    input = {
        "billingAddress": graphql_address_data,
        "shippingAddress": graphql_address_data,
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": order_id, "input": input}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderUpdate"]["errors"]
    order.refresh_from_db()
    assert order.shipping_address
    assert order.billing_address
    call_event_mock.assert_called()


@patch(
    "saleor.graphql.order.mutations.draft_order_update.call_order_event",
    wraps=call_order_event,
)
def test_draft_order_update_same_shipping_method_no_shipping_price_set(
    call_event_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    """The shipping price may not be set even when the shipping method has been added.

    It can happen when shipping method is added to the order without lines
    or with lines that do not require shipping.

    In such a case we should process shipping method no matter it hasn't changed.
    """

    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    order.undiscounted_base_shipping_price_amount = 0
    order.save(update_fields=["undiscounted_base_shipping_price_amount", "status"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", order.shipping_method_id
    )
    input = {"shippingMethod": shipping_method_id}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"id": order_id, "input": input}

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["draftOrderUpdate"]["errors"]
    order.refresh_from_db()
    assert order.undiscounted_base_shipping_price_amount != 0
    call_event_mock.assert_called()
