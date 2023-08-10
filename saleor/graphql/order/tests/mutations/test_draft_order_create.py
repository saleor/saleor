from datetime import datetime, timedelta
from unittest.mock import ANY, Mock, patch

import graphene
import pytest
import pytz
from prices import Money

from .....checkout import AddressType
from .....core.taxes import TaxError, zero_taxed_money
from .....discount.models import VoucherChannelListing
from .....order import OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from .....order.models import Order, OrderEvent
from .....product.models import ProductVariant
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
                    redirectUrl
                    lines {
                        productName
                        productSku
                        quantity
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
                    customerNote
                    total {
                        gross {
                            amount
                        }
                    }
                    shippingMethodName
                    externalReference
                }
            }
        }
    """


def test_draft_order_create(
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

    order = Order.objects.first()
    assert order.user == customer_user
    assert order.shipping_method == shipping_method
    assert order.shipping_method_name == shipping_method.name
    assert order.billing_address
    assert order.shipping_address
    assert order.billing_address.metadata == stored_metadata
    assert order.shipping_address.metadata == stored_metadata
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
    response = Mock(return_value=(fake_order, None))
    mock_fetch_order_prices_if_expired.side_effect = response
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
    mock_fetch_order_prices_if_expired.assert_called_once_with(order, ANY, lines, False)


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


@pytest.mark.parametrize("force_new_line", (True, False))
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

    order_line_1 = order.lines.get(variant=variant_1)
    assert order_line_1.base_unit_price_amount == expected_price_variant_1
    assert order_line_1.undiscounted_base_unit_price_amount == expected_price_variant_1
