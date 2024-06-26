import graphene
import pytest
from prices import TaxedMoney

from .....core.prices import quantize_price
from .....core.taxes import zero_money
from .....discount import DiscountType, DiscountValueType, RewardValueType
from .....order import OrderStatus
from .....order.error_codes import OrderErrorCode
from .....order.models import OrderEvent
from .....payment.model_helpers import get_subtotal
from ....tests.utils import assert_no_permission, get_graphql_content

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
                        amount {
                            amount
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
    assert (
        discounted_line_data["unitPrice"]["net"]["amount"]
        == discounted_variant_total / discounted_line.quantity
    )
    assert (
        discounted_line_data["totalPrice"]["net"]["amount"] == discounted_variant_total
    )
    assert (
        discounted_line_data["unitDiscount"]["amount"]
        == discount_amount / discounted_line.quantity
    )
    assert discounted_line_data["unitDiscountType"] == DiscountValueType.FIXED.upper()
    assert discounted_line_data["unitDiscountReason"] == f"Voucher code: {code}"

    line_1_total = line_1.undiscounted_base_unit_price_amount * line_1.quantity
    assert line_1_data["unitPrice"]["net"]["amount"] == line_1_total / line_1.quantity
    assert line_1_data["totalPrice"]["net"]["amount"] == line_1_total
    assert line_1_data["unitDiscount"]["amount"] == 0
    assert line_1_data["unitDiscountType"] is None
    assert line_1_data["unitDiscountReason"] is None

    order.refresh_from_db()
    assert order.voucher_code == voucher.code
    assert order.search_vector

    # TODO (SHOPX-874): Order discount object shouldn't be created
    assert order.discounts.count() == 1

    assert discounted_line.discounts.count() == 1
    order_line_discount = discounted_line.discounts.first()
    assert order_line_discount.voucher == voucher
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.value_type == DiscountValueType.FIXED
    assert order_line_discount.value == discount_amount
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
    assert discounted_line_data["unitPrice"]["net"]["amount"] == float(
        round(discounted_variant_total / discounted_line.quantity, 2)
    )
    assert (
        discounted_line_data["totalPrice"]["net"]["amount"] == discounted_variant_total
    )
    assert discounted_line_data["unitDiscount"]["amount"] == float(
        round(discount_amount / discounted_line.quantity, 2)
    )
    assert discounted_line_data["unitDiscountType"] == DiscountValueType.FIXED.upper()
    assert discounted_line_data["unitDiscountReason"] == f"Voucher code: {code}"

    line_1_total = line_1.undiscounted_base_unit_price_amount * line_1.quantity
    assert line_1_data["unitPrice"]["net"]["amount"] == line_1_total / line_1.quantity
    assert line_1_data["totalPrice"]["net"]["amount"] == line_1_total
    assert line_1_data["unitDiscount"]["amount"] == 0
    assert line_1_data["unitDiscountType"] is None
    assert line_1_data["unitDiscountReason"] is None

    order.refresh_from_db()
    assert order.voucher_code == voucher.code
    assert order.search_vector

    # TODO (SHOPX-874): Order discount object shouldn't be created
    assert order.discounts.count() == 1

    assert discounted_line.discounts.count() == 1
    order_line_discount = discounted_line.discounts.first()
    assert order_line_discount.voucher == voucher
    assert order_line_discount.type == DiscountType.VOUCHER
    assert order_line_discount.value_type == DiscountValueType.FIXED
    assert order_line_discount.value == discount_amount
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
    order.save(update_fields=["voucher"])

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

    assert not data["errors"]
    order.refresh_from_db()
    assert not order.voucher
    assert order.search_vector

    assert not order.discounts.count()


def test_draft_order_update_clear_voucher_code(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    voucher,
):
    # given
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

    assert not data["errors"]
    order.refresh_from_db()
    assert not order.voucher
    assert order.search_vector

    assert not order.discounts.count()


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
    method_2 = shipping_method_weight_based
    m2_channel_listing = method_2.channel_listings.first()
    m2_channel_listing.price_amount = 15
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


def test_draft_order_update_shipping_method(
    staff_api_client, permission_group_manage_orders, draft_order, shipping_method
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.shipping_method = None
    order.base_shipping_price = zero_money(order.currency)
    order.save()

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
    assert order.base_shipping_price == shipping_total
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
    assert order["discounts"][0]["amount"]["amount"] == discount_amount
    assert order["discounts"][0]["reason"] == f"Promotion: {promotion_id}"
    assert order["discounts"][0]["type"] == DiscountType.ORDER_PROMOTION.upper()
    assert order["discounts"][0]["valueType"] == RewardValueType.PERCENTAGE.upper()

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

    assert gift_line["totalPrice"]["net"]["amount"] == 0.00
    assert gift_line["unitDiscount"]["amount"] == gift_price
    assert gift_line["unitDiscountReason"] == f"Promotion: {promotion_id}"
    assert gift_line["unitDiscountType"] == RewardValueType.FIXED.upper()
    assert gift_line["unitDiscountValue"] == gift_price

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
