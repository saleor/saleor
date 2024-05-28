from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytz
from django.db.models import Sum
from django.test import override_settings
from freezegun import freeze_time
from prices import Money, TaxedMoney

from .....core import EventDeliveryStatus
from .....core.models import EventDelivery
from .....core.prices import quantize_price
from .....core.taxes import zero_taxed_money
from .....discount import DiscountValueType
from .....discount.models import VoucherCustomer
from .....order import OrderOrigin, OrderStatus
from .....order import events as order_events
from .....order.calculations import fetch_order_prices_if_expired
from .....order.error_codes import OrderErrorCode
from .....order.interface import OrderTaxedPricesData
from .....order.models import OrderEvent
from .....payment.model_helpers import get_subtotal
from .....plugins import PLUGIN_IDENTIFIER_PREFIX
from .....plugins.base_plugin import ExcludedShippingMethod
from .....plugins.tests.sample_plugins import PluginSample
from .....plugins.webhook.conftest import (  # noqa: F401
    tax_data_response,
    tax_line_data_response,
)
from .....product.models import ProductVariant
from .....warehouse.models import Allocation, PreorderAllocation, Stock
from .....warehouse.tests.utils import get_available_quantity_for_stock
from .....webhook.event_types import WebhookEventSyncType
from ....payment.types import PaymentChargeStatusEnum
from ....tests.utils import assert_no_permission, get_graphql_content

DRAFT_ORDER_COMPLETE_MUTATION = """
    mutation draftComplete($id: ID!) {
        draftOrderComplete(id: $id) {
            errors {
                field
                code
                message
                variants
                orderLines
            }
            order {
                status
                origin
                paymentStatus
                voucher {
                    code
                }
                voucherCode
                total {
                    net {
                        amount
                    }
                }
                subtotal {
                    net {
                        amount
                    }
                }
                undiscountedTotal {
                    net {
                        amount
                    }
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
):
    # given
    order = draft_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.search_vector
    assert order.status == OrderStatus.UNFULFILLED

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


def test_draft_order_complete_no_automatically_confirm_all_new_orders(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
    channel_USD,
):
    # given
    channel_USD.automatically_confirm_all_new_orders = False
    channel_USD.save()
    order = draft_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.search_vector
    assert order.status == OrderStatus.UNCONFIRMED

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 1 event with correct type
    event = OrderEvent.objects.get(user=staff_user)
    assert event.type == order_events.OrderEvents.PLACED_FROM_DRAFT
    assert not OrderEvent.objects.exclude(user=staff_user).exists()


def test_draft_order_complete_by_user_no_channel_access(
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

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_by_app(
    product_variant_out_of_stock_webhook_mock,
    app_api_client,
    draft_order,
    permission_manage_orders,
    channel_PLN,
):
    # given
    order = draft_order

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = app_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION,
        variables,
        permissions=(permission_manage_orders,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.search_vector


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_with_voucher(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
    voucher,
):
    # given
    order = draft_order
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order.voucher = voucher
    code_instance = voucher.codes.first()
    order.voucher_code = code_instance.code
    order.should_refresh_prices = True
    order.save(update_fields=["voucher", "voucher_code", "should_refresh_prices"])

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_value = voucher_listing.discount_value
    order_total = order.total_net_amount

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert data["voucherCode"] == code_instance.code
    assert data["voucher"]["code"] == voucher.code
    assert data["undiscountedTotal"]["net"]["amount"] == order_total
    assert data["total"]["net"]["amount"] == order_total - discount_value
    assert (
        data["total"]["net"]["amount"] == order_total - voucher_listing.discount_value
    )
    subtotal = get_subtotal(order.lines.all(), order.currency)
    assert data["subtotal"]["net"]["amount"] == subtotal.gross.amount
    assert order.search_vector

    lines = order.lines.all()
    for line in lines:
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    lines_undiscounted_total = sum(
        line.undiscounted_total_price_net_amount for line in lines
    )
    lines_total = sum(line.total_price_net_amount for line in lines)
    assert lines_undiscounted_total == lines_total + discount_value

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )
    assert not VoucherCustomer.objects.filter(
        voucher_code=code_instance, customer_email=order.get_customer_email()
    ).exists()


def test_draft_order_complete_with_invalid_voucher(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order_with_voucher,
):
    # given
    order = draft_order_with_voucher
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order.voucher.channel_listings.all().delete()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert not data["order"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID_VOUCHER.name
    assert data["errors"][0]["field"] == "voucher"


def test_draft_order_complete_with_voucher_once_per_customer(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order_with_voucher,
):
    # given
    order = draft_order_with_voucher
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order.voucher.apply_once_per_customer = True
    order.voucher.save(update_fields=["apply_once_per_customer"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    code_instance = order.voucher.codes.first()
    assert not VoucherCustomer.objects.filter(
        voucher_code=code_instance, customer_email=order.get_customer_email()
    ).exists()
    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    assert data["voucherCode"] == code_instance.code
    assert data["voucher"]["code"] == order.voucher.code
    assert VoucherCustomer.objects.filter(
        voucher_code=code_instance, customer_email=order.get_customer_email()
    ).exists()


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_0_total(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
):
    # given
    """Ensure the payment status is FULLY_CHARGED when the total order price is 0."""
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    price = zero_taxed_money(order.currency)
    order.shipping_price = price
    order.total = price
    order.save(
        update_fields=[
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "total_net_amount",
            "total_gross_amount",
        ]
    )

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    payment_charge_status = PaymentChargeStatusEnum.FULLY_CHARGED
    assert data["paymentStatus"] == payment_charge_status.name
    assert order.search_vector

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_without_sku(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    ProductVariant.objects.update(sku=None)
    draft_order.lines.update(product_sku=None)

    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()
    product_variant_out_of_stock_webhook_mock.assert_called_once_with(
        Stock.objects.last()
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_draft_order_complete_with_out_of_stock_webhook(
    product_variant_out_of_stock_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    first_line = order.lines.first()
    first_line.quantity = 5
    first_line.save()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    total_stock = Stock.objects.aggregate(Sum("quantity"))["quantity__sum"]
    total_allocation = Allocation.objects.filter(order_line__order=order).aggregate(
        Sum("quantity_allocated")
    )["quantity_allocated__sum"]
    assert total_stock == total_allocation
    assert product_variant_out_of_stock_webhook_mock.call_count == 2
    product_variant_out_of_stock_webhook_mock.assert_called_with(Stock.objects.last())


def test_draft_order_from_reissue_complete(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.origin = OrderOrigin.REISSUE
    order.save(update_fields=["origin"])

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.REISSUE.upper()

    for line in order.lines.all():
        allocation = line.allocations.get()
        assert allocation.quantity_allocated == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_with_inactive_channel(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    channel = order.channel
    channel.is_active = False
    channel.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.CHANNEL_INACTIVE.name
    assert data["errors"][0]["field"] == "channel"


def test_draft_order_complete_with_unavailable_variant(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    variant = order.lines.first().variant
    variant.channel_listings.filter(channel=order.channel).delete()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.name
    assert data["errors"][0]["field"] == "lines"
    assert data["errors"][0]["variants"] == [variant_id]


def test_draft_order_complete_channel_without_shipping_zones(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.channel.shipping_zones.clear()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]

    assert len(data["errors"]) == 3
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name,
        OrderErrorCode.INSUFFICIENT_STOCK.name,
    }
    assert {error["field"] for error in data["errors"]} == {"shipping", "lines"}


def test_draft_order_complete_product_without_inventory_tracking(
    staff_api_client,
    shipping_method,
    permission_group_manage_orders,
    staff_user,
    draft_order_without_inventory_tracking,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order_without_inventory_tracking
    order.shipping_method = shipping_method
    order.save()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]

    assert not content["data"]["draftOrderComplete"]["errors"]

    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    assert not Allocation.objects.filter(order_line__order=order).exists()

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_not_available_shipping_method(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.channel.shipping_zones.clear()

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no allocation were created
    assert not Allocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]

    assert len(data["errors"]) == 3
    assert {error["code"] for error in data["errors"]} == {
        OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name,
        OrderErrorCode.INSUFFICIENT_STOCK.name,
    }
    assert {error["field"] for error in data["errors"]} == {"shipping", "lines"}


@patch("saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_order")
def test_draft_order_complete_with_excluded_shipping_method(
    mocked_webhook,
    draft_order,
    shipping_method,
    staff_api_client,
    permission_group_manage_orders,
    settings,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "archives-are-incomplete"
    mocked_webhook.return_value = [
        ExcludedShippingMethod(str(shipping_method.id), webhook_reason)
    ]
    order = draft_order
    order.status = OrderStatus.DRAFT
    order.shipping_method = shipping_method
    order.save()
    query = DRAFT_ORDER_COMPLETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert (
        data["errors"][0]["code"] == OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.name
    )
    assert data["errors"][0]["field"] == "shipping"


@patch("saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_order")
def test_draft_order_complete_with_not_excluded_shipping_method(
    mocked_webhook,
    draft_order,
    shipping_method,
    staff_api_client,
    permission_group_manage_orders,
    settings,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    webhook_reason = "archives-are-incomplete"
    other_shipping_method_id = "1337"
    assert other_shipping_method_id != shipping_method.id
    mocked_webhook.return_value = [
        ExcludedShippingMethod(other_shipping_method_id, webhook_reason)
    ]
    order = draft_order
    order.status = OrderStatus.DRAFT
    order.shipping_method = shipping_method
    order.save()
    query = DRAFT_ORDER_COMPLETE_MUTATION
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert len(data["errors"]) == 0


def test_draft_order_complete_out_of_stock_variant(
    staff_api_client, permission_group_manage_orders, staff_user, draft_order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    line_1, _ = order.lines.order_by("-quantity").all()
    stock_1 = Stock.objects.get(product_variant=line_1.variant)
    line_1.quantity = get_available_quantity_for_stock(stock_1) + 1
    line_1.save(update_fields=["quantity"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()

    # then
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT
    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.INSUFFICIENT_STOCK.name
    assert error["orderLines"] == [graphene.Node.to_global_id("OrderLine", line_1.id)]


def test_draft_order_complete_existing_user_email_updates_user_field(
    staff_api_client, draft_order, customer_user, permission_group_manage_orders
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.user_email = customer_user.email
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    assert "errors" not in content
    order.refresh_from_db()
    assert order.user == customer_user


def test_draft_order_complete_anonymous_user_email_sets_user_field_null(
    staff_api_client, draft_order, permission_group_manage_orders
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.user_email = "anonymous@example.com"
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    assert "errors" not in content
    order.refresh_from_db()
    assert order.user is None


def test_draft_order_complete_anonymous_user_no_email(
    staff_api_client, draft_order, permission_group_manage_orders
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.user_email = ""
    order.user = None
    order.save()
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    assert data["status"] == OrderStatus.UNFULFILLED.upper()


def test_draft_order_complete_drops_shipping_address(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
    address,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    order.shipping_address = address.get_copy()
    order.billing_address = address.get_copy()
    order.save()
    order.lines.update(is_shipping_required=False)

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()

    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.shipping_address is None


def test_draft_order_complete_unavailable_for_purchase(
    staff_api_client, permission_group_manage_orders, staff_user, draft_order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    product = order.lines.first().variant.product
    product.channel_listings.update(
        available_for_purchase_at=datetime.now(pytz.UTC) + timedelta(days=5)
    )

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.name


def test_draft_order_complete_preorders(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order_with_preorder_lines,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order_with_preorder_lines

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    # Ensure no preorder allocation were created
    assert not PreorderAllocation.objects.filter(order_line__order=order).exists()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()
    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()

    for line in order.lines.all():
        preorder_allocation = line.preorder_allocations.get()
        assert preorder_allocation.quantity == line.quantity_unfulfilled

    # ensure there are only 2 events with correct types
    event_params = {
        "user": staff_user,
        "type__in": [
            order_events.OrderEvents.PLACED_FROM_DRAFT,
            order_events.OrderEvents.CONFIRMED,
        ],
        "parameters": {},
    }
    matching_events = OrderEvent.objects.filter(**event_params)
    assert matching_events.count() == 2
    assert matching_events[0].type != matching_events[1].type
    assert not OrderEvent.objects.exclude(**event_params).exists()


def test_draft_order_complete_insufficient_stock_preorders(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order_with_preorder_lines,
    channel_USD,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order_with_preorder_lines

    # Ensure no events were created
    assert not OrderEvent.objects.exists()

    line = order.lines.order_by("-quantity").first()
    channel_listing = line.variant.channel_listings.get(channel_id=channel_USD.id)
    line.quantity = channel_listing.preorder_quantity_threshold + 1
    line.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    error = content["data"]["draftOrderComplete"]["errors"][0]
    order.refresh_from_db()
    assert order.status == OrderStatus.DRAFT
    assert order.origin == OrderOrigin.DRAFT

    assert error["field"] == "lines"
    assert error["code"] == OrderErrorCode.INSUFFICIENT_STOCK.name


def test_draft_order_complete_not_draft_order(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["errors"][0]["code"] == OrderErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "id"


def test_draft_order_complete_display_gross_prices(
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    channel = order.channel
    tax_config = channel.tax_configuration

    # Change the current display_gross_prices to the opposite of what is set in the
    # order.display_gross_prices.
    new_display_gross_prices = not order.display_gross_prices

    tax_config.display_gross_prices = new_display_gross_prices
    tax_config.save()
    tax_config.country_exceptions.all().delete()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)
    assert not content["data"]["draftOrderComplete"]["errors"]
    order.refresh_from_db()
    assert order.display_gross_prices == new_display_gross_prices


@freeze_time()
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_draft_order_complete_fails_with_invalid_tax_app(
    mock_request,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    channel_USD,
    tax_app,
    tax_data_response,  # noqa: F811
):
    # given
    mock_request.return_value = tax_data_response
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order = draft_order
    order.should_refresh_prices = True
    order.save()

    channel_USD.tax_configuration.tax_app_id = "invalid"
    channel_USD.tax_configuration.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderComplete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == OrderErrorCode.TAX_ERROR.name
    assert data["errors"][0]["message"] == "Configured Tax App didn't responded."
    assert not EventDelivery.objects.exists()

    order.refresh_from_db()
    assert not order.should_refresh_prices
    assert order.tax_error == "Empty tax data."


@freeze_time()
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_draft_order_complete_force_tax_calculation_when_tax_error_was_saved(
    mock_request,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    channel_USD,
    tax_app,
    tax_data_response,  # noqa: F811
):
    # given
    mock_request.return_value = tax_data_response
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order = draft_order
    order.should_refresh_prices = False
    order.tax_error = "Test error."
    order.save()

    tax_app.identifier = "test_app"
    tax_app.save()
    channel_USD.tax_configuration.tax_app_id = "test_app"
    channel_USD.tax_configuration.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    get_graphql_content(response)

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.webhook.app == tax_app
    mock_request.assert_called_once_with(delivery)

    order.refresh_from_db()
    assert not order.should_refresh_prices
    assert not order.tax_error


@freeze_time()
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_draft_order_complete_calls_correct_tax_app(
    mock_request,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    channel_USD,
    tax_app,
    tax_data_response,  # noqa: F811
):
    # given
    mock_request.return_value = tax_data_response
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order = draft_order
    order.should_refresh_prices = True
    order.save()

    tax_app.identifier = "test_app"
    tax_app.save()
    channel_USD.tax_configuration.tax_app_id = "test_app"
    channel_USD.tax_configuration.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    get_graphql_content(response)

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.webhook.app == tax_app
    mock_request.assert_called_once_with(delivery)

    order.refresh_from_db()
    assert not order.should_refresh_prices
    assert not order.tax_error


@freeze_time()
@patch("saleor.plugins.tests.sample_plugins.PluginSample.calculate_order_line_total")
@override_settings(PLUGINS=["saleor.plugins.tests.sample_plugins.PluginSample"])
def test_draft_order_complete_calls_failing_plugin(
    mock_calculate_order_line_total,
    staff_api_client,
    permission_group_manage_orders,
    draft_order,
    channel_USD,
):
    # given
    def side_effect(order, *args, **kwargs):
        price = Money("10.0", order.currency)
        order.tax_error = "Test error"
        return OrderTaxedPricesData(
            price_with_discounts=TaxedMoney(price, price),
            undiscounted_price=TaxedMoney(price, price),
        )

    mock_calculate_order_line_total.side_effect = side_effect

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order = draft_order
    order.should_refresh_prices = True
    order.save()

    channel_USD.tax_configuration.tax_app_id = (
        PLUGIN_IDENTIFIER_PREFIX + PluginSample.PLUGIN_ID
    )
    channel_USD.tax_configuration.save()

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderComplete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == OrderErrorCode.TAX_ERROR.name
    assert data["errors"][0]["message"] == "Configured Tax App didn't responded."

    order.refresh_from_db()
    assert not order.should_refresh_prices
    assert order.tax_error == "Empty tax data."


DRAFT_ORDER_COMPLETE_WITH_DISCOUNTS_MUTATION = """
    mutation draftComplete($id: ID!) {
        draftOrderComplete(id: $id) {
            errors {
                field
                code
                message
            }
            order {
                id
                total {
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
                    id
                    quantity
                    totalPrice {
                        net {
                            amount
                        }
                    }
                    unitDiscount {
                        amount
                    }
                    unitDiscountValue
                    unitDiscountReason
                    unitDiscountType
                    isGift
                }
            }
        }
    }
    """


def test_draft_order_complete_with_catalogue_and_order_discount(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order_and_promotions,
    plugins_manager,
):
    # given
    Allocation.objects.all().delete()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order, rule_catalogue, rule_total, _ = draft_order_and_promotions
    catalogue_promotion_id = graphene.Node.to_global_id(
        "Promotion", rule_catalogue.promotion_id
    )
    order_promotion_id = graphene.Node.to_global_id(
        "Promotion", rule_total.promotion_id
    )
    rule_catalogue_value = rule_catalogue.reward_value
    rule_total_value = rule_total.reward_value

    currency = order.currency
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    fetch_order_prices_if_expired(order, plugins_manager, force_update=True)

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_WITH_DISCOUNTS_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["draftOrderComplete"]["order"]

    assert len(order_data["discounts"]) == 1

    order_discount = order_data["discounts"][0]
    assert order_discount["amount"]["amount"] == 25.00 == rule_total_value
    assert order_discount["reason"] == f"Promotion: {order_promotion_id}"
    assert order_discount["amount"]["amount"] == 25.00 == rule_total_value
    assert order_discount["valueType"] == DiscountValueType.FIXED.upper()

    lines_db = order.lines.all()
    line_1_db = [line for line in lines_db if line.quantity == 3][0]
    line_2_db = [line for line in lines_db if line.quantity == 2][0]
    line_1_base_total = line_1_db.quantity * line_1_db.base_unit_price_amount
    line_2_base_total = line_2_db.quantity * line_2_db.base_unit_price_amount
    base_total = line_1_base_total + line_2_base_total
    line_1_order_discount_portion = rule_total_value * line_1_base_total / base_total
    line_2_order_discount_portion = rule_total_value - line_1_order_discount_portion

    lines = order_data["lines"]
    line_1 = [line for line in lines if line["quantity"] == 3][0]
    line_2 = [line for line in lines if line["quantity"] == 2][0]
    line_1_total = quantize_price(
        line_1_db.undiscounted_total_price_net_amount - line_1_order_discount_portion,
        currency,
    )
    assert line_1["totalPrice"]["net"]["amount"] == float(line_1_total)
    assert line_1["unitDiscount"]["amount"] == 0.00
    assert line_1["unitDiscountReason"] is None
    assert line_1["unitDiscountValue"] == 0.00

    line_2_total = quantize_price(
        line_2_db.undiscounted_total_price_net_amount
        - rule_catalogue_value * line_2_db.quantity
        - line_2_order_discount_portion,
        currency,
    )
    assert line_2["totalPrice"]["net"]["amount"] == float(line_2_total)
    assert line_2["unitDiscount"]["amount"] == rule_catalogue_value
    assert line_2["unitDiscountReason"] == f"Promotion: {catalogue_promotion_id}"
    assert line_2["unitDiscountType"] == DiscountValueType.FIXED.upper()
    assert line_2["unitDiscountValue"] == rule_catalogue_value

    total = (
        order.undiscounted_total_net_amount
        - line_2["quantity"] * rule_catalogue_value
        - rule_total_value
    )
    assert order_data["total"]["net"]["amount"] == total
    assert total == line_2_total + line_1_total + order.base_shipping_price_amount


def test_draft_order_complete_with_catalogue_and_gift_discount(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order_and_promotions,
    plugins_manager,
):
    # given
    Allocation.objects.all().delete()
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    rule_total.reward_value = Decimal(0)
    rule_total.save(update_fields=["reward_value"])
    catalogue_promotion_id = graphene.Node.to_global_id(
        "Promotion", rule_catalogue.promotion_id
    )
    gift_promotion_id = graphene.Node.to_global_id("Promotion", rule_gift.promotion_id)
    rule_catalogue_value = rule_catalogue.reward_value

    currency = order.currency
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    fetch_order_prices_if_expired(order, plugins_manager, force_update=True)

    # when
    response = staff_api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_WITH_DISCOUNTS_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["draftOrderComplete"]["order"]
    assert not order_data["discounts"]

    lines_db = order.lines.all()
    line_1_db = [line for line in lines_db if line.quantity == 3][0]
    line_2_db = [line for line in lines_db if line.quantity == 2][0]
    gift_line_db = [line for line in lines_db if line.is_gift][0]
    gift_price = gift_line_db.variant.channel_listings.get(
        channel=order.channel
    ).price_amount

    lines = order_data["lines"]
    assert len(lines) == 3
    line_1 = [line for line in lines if line["quantity"] == 3][0]
    line_2 = [line for line in lines if line["quantity"] == 2][0]
    gift_line = [line for line in lines if line["isGift"] is True][0]

    line_1_total = line_1_db.undiscounted_total_price_net_amount
    assert line_1["totalPrice"]["net"]["amount"] == line_1_total
    assert line_1["unitDiscount"]["amount"] == 0.00
    assert line_1["unitDiscountReason"] is None
    assert line_1["unitDiscountValue"] == 0.00

    line_2_total = quantize_price(
        line_2_db.undiscounted_total_price_net_amount
        - rule_catalogue_value * line_2_db.quantity,
        currency,
    )
    assert line_2["totalPrice"]["net"]["amount"] == line_2_total
    assert line_2["unitDiscount"]["amount"] == rule_catalogue_value
    assert line_2["unitDiscountReason"] == f"Promotion: {catalogue_promotion_id}"
    assert line_2["unitDiscountType"] == DiscountValueType.FIXED.upper()
    assert line_2["unitDiscountValue"] == rule_catalogue_value

    assert gift_line["totalPrice"]["net"]["amount"] == 0.00
    assert gift_line["unitDiscount"]["amount"] == gift_price
    assert gift_line["unitDiscountReason"] == f"Promotion: {gift_promotion_id}"
    assert gift_line["unitDiscountType"] == DiscountValueType.FIXED.upper()
    assert gift_line["unitDiscountValue"] == gift_price

    total = (
        order.undiscounted_total_net_amount - rule_catalogue_value * line_2_db.quantity
    )
    assert order_data["total"]["net"]["amount"] == total
    assert total == line_2_total + line_1_total + order.base_shipping_price_amount


def test_draft_order_complete_with_invalid_address(
    staff_api_client,
    permission_group_manage_orders,
    staff_user,
    draft_order,
    address,
):
    """Check if draft order can be completed with invalid address.

    After introducing `AddressInput.skip_validation`, Saleor may have invalid address
    stored in database.
    """
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = draft_order
    wrong_postal_code = "wrong postal code"
    address.postal_code = wrong_postal_code

    order.shipping_address = address.get_copy()
    order.billing_address = address.get_copy()
    order.save(update_fields=["shipping_address", "billing_address"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["draftOrderComplete"]["order"]
    order.refresh_from_db()

    assert data["status"] == order.status.upper()
    assert data["origin"] == OrderOrigin.DRAFT.upper()
    assert order.shipping_address.postal_code == wrong_postal_code
    assert order.billing_address.postal_code == wrong_postal_code
