from decimal import Decimal
from unittest.mock import Mock, patch

import graphene
import pytest
from prices import Money, TaxedMoney

from ...core.weight import zero_weight
from ...discount import OrderDiscountType
from ...discount.models import (
    DiscountValueType,
    NotApplicable,
    Voucher,
    VoucherChannelListing,
    VoucherType,
)
from ...discount.utils import validate_voucher_in_order
from ...graphql.core.utils import to_global_id_or_none
from ...graphql.order.utils import OrderLineData
from ...graphql.tests.utils import get_graphql_content
from ...payment import ChargeStatus
from ...payment.models import Payment
from ...plugins.manager import get_plugins_manager
from ...product.models import Collection
from ...tests.fixtures import recalculate_order
from ...warehouse import WarehouseClickAndCollectOption
from ...warehouse.models import Stock, Warehouse
from ...warehouse.tests.utils import get_quantity_allocated_for_stock
from .. import FulfillmentStatus, OrderEvents, OrderStatus
from ..calculations import fetch_order_prices_if_expired
from ..events import (
    OrderEventsEmails,
    event_fulfillment_confirmed_notification,
    event_fulfillment_digital_links_notification,
    event_order_cancelled_notification,
    event_order_confirmation_notification,
    event_order_refunded_notification,
    event_payment_confirmed_notification,
)
from ..models import Order
from ..notifications import (
    get_default_fulfillment_payload,
    send_fulfillment_confirmation_to_customer,
)
from ..utils import (
    add_variant_to_order,
    change_order_line_quantity,
    delete_order_line,
    get_voucher_discount_for_order,
    restock_fulfillment_lines,
    update_order_authorize_data,
    update_order_charge_data,
    update_order_status,
)


def test_total_setter():
    price = TaxedMoney(net=Money(10, "USD"), gross=Money(15, "USD"))
    order = Order()
    order.total = price
    assert order.total_net_amount == Decimal(10)
    assert order.total.net == Money(10, "USD")
    assert order.total_gross_amount == Decimal(15)
    assert order.total.gross == Money(15, "USD")
    assert order.total.tax == Money(5, "USD")


def test_order_get_subtotal(order_with_lines):
    order_with_lines.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=order_with_lines.total.gross.amount * Decimal("0.5"),
        amount_value=order_with_lines.total.gross.amount * Decimal("0.5"),
        name="Test discount",
    )

    fetch_order_prices_if_expired(
        order_with_lines, get_plugins_manager(), force_update=True
    )

    target_subtotal = order_with_lines.total - order_with_lines.shipping_price
    assert order_with_lines.get_subtotal() == target_subtotal


def test_recalculate_order_keeps_weight_unit(order_with_lines):
    initial_weight_unit = order_with_lines.weight.unit
    recalculate_order(order_with_lines)
    recalculated_weight_unit = order_with_lines.weight.unit
    assert initial_weight_unit == recalculated_weight_unit


def test_add_variant_to_order_adds_line_for_new_variant(
    order_with_lines,
    product,
    product_translation_fr,
    settings,
    anonymous_user,
    anonymous_plugins,
    site_settings,
):
    order = order_with_lines
    variant = product.variants.get()
    lines_before = order.lines.count()
    settings.LANGUAGE_CODE = "fr"
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)

    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
    )

    line = order.lines.last()
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.product_variant_id == variant.get_global_id()
    assert line.quantity == 1
    assert line.unit_price == TaxedMoney(net=Money(10, "USD"), gross=Money(10, "USD"))
    assert line.translated_product_name == str(variant.product.translated)
    assert line.variant_name == str(variant)
    assert line.product_name == str(variant.product)
    assert not line.unit_discount_amount
    assert not line.unit_discount_value
    assert not line.unit_discount_reason


def test_add_variant_to_order_adds_line_for_new_variant_on_sale(
    order_with_lines,
    product,
    product_translation_fr,
    sale,
    discount_info,
    settings,
    anonymous_user,
    anonymous_plugins,
    site_settings,
):
    order = order_with_lines
    variant = product.variants.first()
    discount_info.variants_ids.add(variant.id)
    sale.variants.add(variant)
    lines_before = order.lines.count()
    settings.LANGUAGE_CODE = "fr"
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)

    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
        discounts=[discount_info],
    )

    line = order.lines.last()
    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    sale_channel_listing = sale.channel_listings.first()
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.quantity == 1
    unit_amount = (
        variant_channel_listing.price_amount - sale_channel_listing.discount_value
    )
    assert line.unit_price == TaxedMoney(
        net=Money(unit_amount, "USD"), gross=Money(unit_amount, "USD")
    )
    assert line.translated_product_name == str(variant.product.translated)
    assert line.variant_name == str(variant)
    assert line.product_name == str(variant.product)

    assert line.unit_discount_amount == sale_channel_listing.discount_value
    assert line.unit_discount_value == sale_channel_listing.discount_value
    assert line.unit_discount_reason


def test_add_variant_to_draft_order_adds_line_for_variant_with_price_0(
    order_with_lines,
    product,
    product_translation_fr,
    settings,
    anonymous_user,
    anonymous_plugins,
    site_settings,
):
    order = order_with_lines
    variant = product.variants.get()
    variant_channel_listing = variant.channel_listings.get()
    variant_channel_listing.price = Money(0, "USD")
    variant_channel_listing.save(update_fields=["price_amount", "currency"])

    lines_before = order.lines.count()
    settings.LANGUAGE_CODE = "fr"
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)

    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
    )

    line = order.lines.last()
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.product_variant_id == variant.get_global_id()
    assert line.quantity == 1
    assert line.unit_price == TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))
    assert line.translated_product_name == str(variant.product.translated)
    assert line.product_name == variant.product.name


def test_add_variant_to_order_not_allocates_stock_for_new_variant(
    order_with_lines,
    product,
    anonymous_user,
    anonymous_plugins,
    site_settings,
):
    variant = product.variants.get()
    stock = Stock.objects.get(product_variant=variant)

    stock_before = get_quantity_allocated_for_stock(stock)

    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)
    add_variant_to_order(
        order=order_with_lines,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
    )

    stock.refresh_from_db()
    assert get_quantity_allocated_for_stock(stock) == stock_before


def test_add_variant_to_order_edits_line_for_existing_variant(
    order_with_lines, anonymous_user, anonymous_plugins, site_settings
):
    existing_line = order_with_lines.lines.first()
    variant = existing_line.variant
    lines_before = order_with_lines.lines.count()
    line_quantity_before = existing_line.quantity
    line_data = OrderLineData(
        line_id=str(existing_line.pk), variant=variant, quantity=1
    )

    add_variant_to_order(
        order=order_with_lines,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
    )

    existing_line.refresh_from_db()
    assert order_with_lines.lines.count() == lines_before
    assert existing_line.product_sku == variant.sku
    assert existing_line.product_variant_id == variant.get_global_id()
    assert existing_line.quantity == line_quantity_before + 1


def test_add_variant_to_order_not_allocates_stock_for_existing_variant(
    order_with_lines, anonymous_user, anonymous_plugins, site_settings
):
    existing_line = order_with_lines.lines.first()
    variant = existing_line.variant
    stock = Stock.objects.get(product_variant=variant)
    stock_before = get_quantity_allocated_for_stock(stock)
    quantity_before = existing_line.quantity
    quantity_unfulfilled_before = existing_line.quantity_unfulfilled
    line_data = OrderLineData(
        line_id=str(existing_line.id), variant=variant, quantity=1
    )

    add_variant_to_order(
        order=order_with_lines,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
    )

    stock.refresh_from_db()
    existing_line.refresh_from_db()
    assert get_quantity_allocated_for_stock(stock) == stock_before
    assert existing_line.quantity == quantity_before + 1
    assert existing_line.quantity_unfulfilled == quantity_unfulfilled_before + 1


def test_restock_fulfillment_lines(fulfilled_order, warehouse):
    fulfillment = fulfilled_order.fulfillments.first()
    line_1 = fulfillment.lines.first()
    line_2 = fulfillment.lines.last()
    stock_1 = Stock.objects.get(product_variant=line_1.order_line.variant)
    stock_2 = Stock.objects.get(product_variant=line_2.order_line.variant)
    stock_1_quantity_allocated_before = get_quantity_allocated_for_stock(stock_1)
    stock_2_quantity_allocated_before = get_quantity_allocated_for_stock(stock_2)
    stock_1_quantity_before = stock_1.quantity
    stock_2_quantity_before = stock_2.quantity
    order_line_1 = line_1.order_line
    order_line_2 = line_2.order_line
    order_line_1_quantity_fulfilled_before = order_line_1.quantity_fulfilled
    order_line_2_quantity_fulfilled_before = order_line_2.quantity_fulfilled

    restock_fulfillment_lines(fulfillment, warehouse)

    stock_1.refresh_from_db()
    stock_2.refresh_from_db()
    assert get_quantity_allocated_for_stock(stock_1) == (
        stock_1_quantity_allocated_before + line_1.quantity
    )
    assert get_quantity_allocated_for_stock(stock_2) == (
        stock_2_quantity_allocated_before + line_2.quantity
    )
    assert stock_1.quantity == stock_1_quantity_before + line_1.quantity
    assert stock_2.quantity == stock_2_quantity_before + line_2.quantity
    order_line_1.refresh_from_db()
    order_line_2.refresh_from_db()
    assert (
        order_line_1.quantity_fulfilled
        == order_line_1_quantity_fulfilled_before - line_1.quantity
    )
    assert (
        order_line_2.quantity_fulfilled
        == order_line_2_quantity_fulfilled_before - line_2.quantity
    )


def test_update_order_status_partially_fulfilled(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    line = fulfillment.lines.first()
    order_line = line.order_line

    order_line.quantity_fulfilled -= line.quantity
    order_line.save()
    line.delete()
    update_order_status(fulfilled_order)

    assert fulfilled_order.status == OrderStatus.PARTIALLY_FULFILLED


def test_update_order_status_unfulfilled(order_with_lines):
    order_with_lines.status = OrderStatus.FULFILLED
    order_with_lines.save()

    update_order_status(order_with_lines)

    order_with_lines.refresh_from_db()
    assert order_with_lines.status == OrderStatus.UNFULFILLED


def test_update_order_status_fulfilled(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment_line = fulfillment.lines.first()
    fulfillment_line.quantity -= 3
    fulfillment_line.save()
    fulfilled_order.status = OrderStatus.UNFULFILLED
    fulfilled_order.save()
    replaced_fulfillment = fulfilled_order.fulfillments.create(
        status=FulfillmentStatus.REPLACED
    )
    replaced_fulfillment.lines.create(
        quantity=3, order_line=fulfillment_line.order_line
    )

    update_order_status(fulfilled_order)

    fulfilled_order.refresh_from_db()
    assert fulfilled_order.status == OrderStatus.FULFILLED


def test_update_order_status_returned(fulfilled_order):
    fulfilled_order.fulfillments.all().update(status=FulfillmentStatus.RETURNED)
    fulfilled_order.status = OrderStatus.UNFULFILLED
    fulfilled_order.save()

    update_order_status(fulfilled_order)

    fulfilled_order.refresh_from_db()
    assert fulfilled_order.status == OrderStatus.RETURNED


def test_update_order_status_partially_returned(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment_line = fulfillment.lines.first()
    fulfillment_line.quantity -= 3
    fulfillment_line.save()
    returned_fulfillment = fulfilled_order.fulfillments.create(
        status=FulfillmentStatus.RETURNED
    )
    replaced_fulfillment = fulfilled_order.fulfillments.create(
        status=FulfillmentStatus.REPLACED
    )
    refunded_and_returned_fulfillment = fulfilled_order.fulfillments.create(
        status=FulfillmentStatus.REFUNDED_AND_RETURNED
    )
    returned_fulfillment.lines.create(
        quantity=1, order_line=fulfillment_line.order_line
    )
    replaced_fulfillment.lines.create(
        quantity=1, order_line=fulfillment_line.order_line
    )
    refunded_and_returned_fulfillment.lines.create(
        quantity=1, order_line=fulfillment_line.order_line
    )

    fulfilled_order.status = OrderStatus.UNFULFILLED
    fulfilled_order.save()

    update_order_status(fulfilled_order)

    fulfilled_order.refresh_from_db()
    assert fulfilled_order.status == OrderStatus.PARTIALLY_RETURNED


def test_update_order_status_waiting_for_approval(fulfilled_order):
    fulfilled_order.fulfillments.create(status=FulfillmentStatus.WAITING_FOR_APPROVAL)
    fulfilled_order.status = OrderStatus.FULFILLED
    fulfilled_order.save()

    update_order_status(fulfilled_order)

    fulfilled_order.refresh_from_db()
    assert fulfilled_order.status == OrderStatus.PARTIALLY_FULFILLED


def test_validate_fulfillment_tracking_number_as_url(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    assert not fulfillment.is_tracking_number_url
    fulfillment.tracking_number = "https://www.example.com"
    fulfillment.save()
    assert fulfillment.is_tracking_number_url


def test_order_queryset_confirmed(draft_order, channel_USD):
    other_orders = [
        Order.objects.create(status=OrderStatus.UNFULFILLED, channel=channel_USD),
        Order.objects.create(
            status=OrderStatus.PARTIALLY_FULFILLED, channel=channel_USD
        ),
        Order.objects.create(status=OrderStatus.FULFILLED, channel=channel_USD),
        Order.objects.create(status=OrderStatus.CANCELED, channel=channel_USD),
    ]

    confirmed_orders = Order.objects.confirmed()

    assert draft_order not in confirmed_orders
    assert all([order in confirmed_orders for order in other_orders])


def test_order_queryset_drafts(draft_order, channel_USD):
    other_orders = [
        Order.objects.create(status=OrderStatus.UNFULFILLED, channel=channel_USD),
        Order.objects.create(
            status=OrderStatus.PARTIALLY_FULFILLED, channel=channel_USD
        ),
        Order.objects.create(status=OrderStatus.FULFILLED, channel=channel_USD),
        Order.objects.create(status=OrderStatus.CANCELED, channel=channel_USD),
    ]

    draft_orders = Order.objects.drafts()

    assert draft_order in draft_orders
    assert all([order not in draft_orders for order in other_orders])


def test_order_queryset_to_ship(settings, channel_USD):
    total = TaxedMoney(net=Money(10, "USD"), gross=Money(15, "USD"))
    orders_to_ship = [
        Order.objects.create(
            status=OrderStatus.UNFULFILLED,
            total=total,
            total_charged_amount=total.gross.amount,
            channel=channel_USD,
        ),
        Order.objects.create(
            status=OrderStatus.PARTIALLY_FULFILLED,
            total=total,
            total_charged_amount=total.gross.amount,
            channel=channel_USD,
        ),
    ]
    for order in orders_to_ship:
        order.payments.create(
            gateway="mirumee.payments.dummy",
            charge_status=ChargeStatus.FULLY_CHARGED,
            total=order.total.gross.amount,
            captured_amount=order.total.gross.amount,
            currency=order.total.gross.currency,
        )

    orders_not_to_ship = [
        Order.objects.create(
            status=OrderStatus.DRAFT, total=total, channel=channel_USD
        ),
        Order.objects.create(
            status=OrderStatus.UNFULFILLED, total=total, channel=channel_USD
        ),
        Order.objects.create(
            status=OrderStatus.PARTIALLY_FULFILLED, total=total, channel=channel_USD
        ),
        Order.objects.create(
            status=OrderStatus.FULFILLED, total=total, channel=channel_USD
        ),
        Order.objects.create(
            status=OrderStatus.CANCELED, total=total, channel=channel_USD
        ),
    ]

    orders = Order.objects.ready_to_fulfill()

    assert all([order in orders for order in orders_to_ship])
    assert all([order not in orders for order in orders_not_to_ship])


def test_queryset_ready_to_capture(channel_USD):
    total = TaxedMoney(net=Money(10, "USD"), gross=Money(15, "USD"))

    preauth_order = Order.objects.create(
        status=OrderStatus.UNFULFILLED, total=total, channel=channel_USD
    )
    Payment.objects.create(
        order=preauth_order, charge_status=ChargeStatus.NOT_CHARGED, is_active=True
    )

    Order.objects.create(status=OrderStatus.DRAFT, total=total, channel=channel_USD)
    Order.objects.create(
        status=OrderStatus.UNFULFILLED, total=total, channel=channel_USD
    )
    Order.objects.create(status=OrderStatus.CANCELED, total=total, channel=channel_USD)

    qs = Order.objects.ready_to_capture()
    assert preauth_order in qs
    statuses = [o.status for o in qs]
    assert OrderStatus.DRAFT not in statuses
    assert OrderStatus.CANCELED not in statuses


def _calculate_order_weight_from_lines(order):
    weight = zero_weight()
    for line in order.lines.all():
        weight += line.variant.get_weight() * line.quantity
    return weight


def test_calculate_order_weight(order_with_lines):
    order_weight = order_with_lines.weight
    calculated_weight = _calculate_order_weight_from_lines(order_with_lines)
    assert calculated_weight == order_weight


def test_order_weight_add_more_variant(
    order_with_lines, anonymous_user, anonymous_plugins, site_settings
):
    variant = order_with_lines.lines.first().variant
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=2)

    add_variant_to_order(
        order=order_with_lines,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
    )
    order_with_lines.refresh_from_db()

    assert order_with_lines.weight == _calculate_order_weight_from_lines(
        order_with_lines
    )


def test_order_weight_add_new_variant(
    order_with_lines,
    product,
    anonymous_user,
    anonymous_plugins,
    site_settings,
):
    variant = product.variants.first()
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=2)

    add_variant_to_order(
        order=order_with_lines,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
    )
    order_with_lines.refresh_from_db()

    assert order_with_lines.weight == _calculate_order_weight_from_lines(
        order_with_lines
    )


def test_order_weight_change_line_quantity(staff_user, lines_info):
    app = None
    line_info = lines_info[0]
    new_quantity = line_info.quantity + 2
    order = line_info.line.order
    change_order_line_quantity(
        staff_user,
        app,
        line_info,
        new_quantity,
        line_info.quantity,
        order.channel.slug,
        get_plugins_manager(),
    )
    assert order.weight == _calculate_order_weight_from_lines(order)


def test_order_weight_delete_line(lines_info):
    order = lines_info[0].line.order
    line_info = lines_info[0]
    delete_order_line(line_info, get_plugins_manager())
    assert order.weight == _calculate_order_weight_from_lines(order)


def test_get_order_weight_non_existing_product(
    order_with_lines,
    product,
    anonymous_user,
    anonymous_plugins,
    site_settings,
):
    # Removing product should not affect order's weight
    order = order_with_lines
    variant = product.variants.first()
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)

    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=anonymous_user,
        app=None,
        manager=anonymous_plugins,
        site_settings=site_settings,
    )
    old_weight = order.get_total_weight()

    product.delete()

    order.refresh_from_db()
    new_weight = order.get_total_weight()

    assert old_weight == new_weight


@patch("saleor.discount.utils.validate_voucher")
def test_get_voucher_discount_for_order_voucher_validation(
    mock_validate_voucher, voucher, order_with_lines
):
    order_with_lines.voucher = voucher
    order_with_lines.save()
    subtotal = order_with_lines.get_subtotal()
    quantity = order_with_lines.get_total_quantity()
    customer_email = order_with_lines.get_customer_email()

    validate_voucher_in_order(order_with_lines)

    mock_validate_voucher.assert_called_once_with(
        voucher,
        subtotal.gross,
        quantity,
        customer_email,
        order_with_lines.channel,
        order_with_lines.user,
    )


@patch("saleor.discount.utils.validate_voucher")
def test_validate_voucher_in_order_without_voucher(
    mock_validate_voucher, order_with_lines
):
    order_with_lines.voucher = None
    order_with_lines.save()

    assert not order_with_lines.voucher

    validate_voucher_in_order(order_with_lines)
    mock_validate_voucher.assert_not_called()


@pytest.mark.parametrize(
    "subtotal, discount_value, discount_type, min_spent_amount, expected_value",
    [
        ("100", 10, DiscountValueType.FIXED, None, 10),
        ("100.05", 10, DiscountValueType.PERCENTAGE, 100, 10),
    ],
)
def test_value_voucher_order_discount(
    subtotal,
    discount_value,
    discount_type,
    min_spent_amount,
    expected_value,
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_type,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
        min_spent_amount=(min_spent_amount if min_spent_amount is not None else None),
    )
    subtotal = Money(subtotal, "USD")
    subtotal = TaxedMoney(net=subtotal, gross=subtotal)
    order = Mock(
        get_subtotal=Mock(return_value=subtotal), voucher=voucher, channel=channel_USD
    )
    discount = get_voucher_discount_for_order(order)
    assert discount == Money(expected_value, "USD")


@pytest.mark.parametrize(
    "shipping_cost, discount_value, discount_type, expected_value",
    [(10, 50, DiscountValueType.PERCENTAGE, 5), (10, 20, DiscountValueType.FIXED, 10)],
)
def test_shipping_voucher_order_discount(
    shipping_cost, discount_value, discount_type, expected_value, channel_USD
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
    )
    subtotal = Money(100, "USD")
    subtotal = TaxedMoney(net=subtotal, gross=subtotal)
    shipping_total = TaxedMoney(
        gross=Money(shipping_cost, "USD"), net=Money(shipping_cost, "USD")
    )
    order = Mock(
        get_subtotal=Mock(return_value=subtotal),
        shipping_price=shipping_total,
        voucher=voucher,
        channel=channel_USD,
    )
    discount = get_voucher_discount_for_order(order)
    assert discount == Money(expected_value, "USD")


@pytest.mark.parametrize(
    "total, total_quantity, min_spent_amount, min_checkout_items_quantity,"
    "voucher_type",
    [
        (99, 10, 100, 10, VoucherType.SHIPPING),
        (100, 9, 100, 10, VoucherType.SHIPPING),
        (99, 9, 100, 10, VoucherType.SHIPPING),
        (99, 10, 100, 10, VoucherType.ENTIRE_ORDER),
        (100, 9, 100, 10, VoucherType.ENTIRE_ORDER),
        (99, 9, 100, 10, VoucherType.ENTIRE_ORDER),
        (99, 10, 100, 10, VoucherType.SPECIFIC_PRODUCT),
        (100, 9, 100, 10, VoucherType.SPECIFIC_PRODUCT),
        (99, 9, 100, 10, VoucherType.SPECIFIC_PRODUCT),
    ],
)
def test_shipping_voucher_checkout_discount_not_applicable_returns_zero(
    total,
    total_quantity,
    min_spent_amount,
    min_checkout_items_quantity,
    voucher_type,
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=voucher_type,
        discount_value_type=DiscountValueType.FIXED,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
        min_spent_amount=(min_spent_amount if min_spent_amount is not None else None),
    )
    price = Money(total, "USD")
    price = TaxedMoney(net=price, gross=price)
    order = Mock(
        get_subtotal=Mock(return_value=price),
        get_total_quantity=Mock(return_value=total_quantity),
        shipping_price=price,
        voucher=voucher,
        channel=channel_USD,
    )
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order)


@pytest.mark.parametrize(
    "discount_value, discount_type, apply_once_per_order, discount_amount",
    [
        (5, DiscountValueType.FIXED, True, "5"),
        (5, DiscountValueType.FIXED, False, "25"),
        (10000, DiscountValueType.FIXED, True, "12.3"),
        (10000, DiscountValueType.FIXED, False, "86.1"),
        (10, DiscountValueType.PERCENTAGE, True, "1.23"),
        (10, DiscountValueType.PERCENTAGE, False, "8.61"),
    ],
)
def test_get_discount_for_order_specific_products_voucher(
    order_with_lines,
    discount_value,
    discount_type,
    apply_once_per_order,
    discount_amount,
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        apply_once_per_order=apply_once_per_order,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
    )
    voucher.products.add(order_with_lines.lines.first().variant.product)
    voucher.products.add(order_with_lines.lines.last().variant.product)
    order_with_lines.voucher = voucher
    order_with_lines.save()
    discount = get_voucher_discount_for_order(order_with_lines)
    assert discount == Money(discount_amount, "USD")


def test_product_voucher_checkout_discount_raises_not_applicable(
    order_with_lines, product_with_images, channel_USD
):
    discounted_product = product_with_images
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
    )
    voucher.save()
    voucher.products.add(discounted_product)
    order_with_lines.voucher = voucher
    order_with_lines.save()
    # Offer is valid only for products listed in voucher
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order_with_lines)


def test_category_voucher_checkout_discount_raises_not_applicable(
    order_with_lines, channel_USD
):
    discounted_collection = Collection.objects.create(
        name="Discounted", slug="discount"
    )
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
    )
    voucher.save()
    voucher.collections.add(discounted_collection)
    order_with_lines.voucher = voucher
    order_with_lines.save()
    # Discount should be valid only for items in the discounted collections
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order_with_lines)


def test_ordered_item_change_quantity(staff_user, transactional_db, lines_info):
    app = None
    order = lines_info[0].line.order
    assert not order.events.count()
    change_order_line_quantity(
        staff_user,
        app,
        lines_info[1],
        lines_info[1].quantity,
        0,
        order.channel.slug,
        get_plugins_manager(),
    )
    change_order_line_quantity(
        staff_user,
        app,
        lines_info[0],
        lines_info[0].quantity,
        0,
        order.channel.slug,
        get_plugins_manager(),
    )
    assert order.get_total_quantity() == 0


def test_change_order_line_quantity_changes_total_prices(
    staff_user, transactional_db, lines_info
):
    app = None
    order = lines_info[0].line.order
    assert not order.events.count()
    line_info = lines_info[0]
    new_quantity = line_info.quantity + 1
    change_order_line_quantity(
        staff_user,
        app,
        line_info,
        line_info.quantity,
        new_quantity,
        order.channel.slug,
        get_plugins_manager(),
    )
    assert line_info.line.total_price == line_info.line.unit_price * new_quantity


@patch("saleor.plugins.manager.PluginsManager.notify")
@pytest.mark.parametrize(
    "has_standard,has_digital", ((True, True), (True, False), (False, True))
)
def test_send_fulfillment_order_lines_mails_by_user(
    mocked_notify,
    staff_user,
    fulfilled_order,
    fulfillment,
    digital_content,
    has_standard,
    has_digital,
):
    manager = get_plugins_manager()
    redirect_url = "http://localhost.pl"
    order = fulfilled_order
    order.redirect_url = redirect_url
    assert order.lines.count() == 2

    if not has_standard:
        line = order.lines.all()[0]
        line.variant = digital_content.product_variant
        assert line.is_digital
        line.save()

    if has_digital:
        line = order.lines.all()[1]
        line.variant = digital_content.product_variant
        assert line.is_digital
        line.save()

    send_fulfillment_confirmation_to_customer(
        order=order, fulfillment=fulfillment, user=staff_user, app=None, manager=manager
    )
    expected_payload = get_default_fulfillment_payload(order, fulfillment)
    expected_payload["requester_user_id"] = to_global_id_or_none(staff_user)
    expected_payload["requester_app_id"] = None
    mocked_notify.assert_called_once_with(
        "order_fulfillment_confirmation",
        payload=expected_payload,
        channel_slug=fulfilled_order.channel.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.notify")
@pytest.mark.parametrize(
    "has_standard,has_digital", ((True, True), (True, False), (False, True))
)
def test_send_fulfillment_order_lines_mails_by_app(
    mocked_notify,
    app,
    fulfilled_order,
    fulfillment,
    digital_content,
    has_standard,
    has_digital,
):
    manager = get_plugins_manager()
    redirect_url = "http://localhost.pl"
    order = fulfilled_order
    order.redirect_url = redirect_url
    assert order.lines.count() == 2

    if not has_standard:
        line = order.lines.all()[0]
        line.variant = digital_content.product_variant
        assert line.is_digital
        line.save()

    if has_digital:
        line = order.lines.all()[1]
        line.variant = digital_content.product_variant
        assert line.is_digital
        line.save()

    send_fulfillment_confirmation_to_customer(
        order=order, fulfillment=fulfillment, user=None, app=app, manager=manager
    )
    expected_payload = get_default_fulfillment_payload(order, fulfillment)
    expected_payload["requester_user_id"] = None
    expected_payload["requester_app_id"] = to_global_id_or_none(app)
    mocked_notify.assert_called_once_with(
        "order_fulfillment_confirmation",
        payload=expected_payload,
        channel_slug=fulfilled_order.channel.slug,
    )


@pytest.mark.parametrize(
    "event_fun, expected_event_type",
    [
        (event_order_confirmation_notification, OrderEventsEmails.ORDER_CONFIRMATION),
        (event_payment_confirmed_notification, OrderEventsEmails.PAYMENT),
    ],
)
def test_email_sent_event_with_user(order, event_fun, expected_event_type):
    user = order.user
    event_fun(order_id=order.id, user_id=user.pk, customer_email=order.user_email)
    events = order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event
    assert event.type == OrderEvents.EMAIL_SENT
    assert event.user == user
    assert event.order is order
    assert event.date
    assert event.parameters == {
        "email": order.get_customer_email(),
        "email_type": expected_event_type,
    }


@pytest.mark.parametrize(
    "event_fun, expected_event_type",
    [
        (event_order_cancelled_notification, OrderEventsEmails.ORDER_CANCEL),
        (event_fulfillment_confirmed_notification, OrderEventsEmails.FULFILLMENT),
        (event_fulfillment_digital_links_notification, OrderEventsEmails.DIGITAL_LINKS),
        (event_order_refunded_notification, OrderEventsEmails.ORDER_REFUND),
    ],
)
def test_email_sent_event_with_user_without_app(order, event_fun, expected_event_type):
    user = order.user
    event_fun(
        order_id=order.id, user_id=user.pk, app_id=None, customer_email=order.user_email
    )
    events = order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event
    assert event.type == OrderEvents.EMAIL_SENT
    assert event.user == user
    assert not event.app
    assert event.order is order
    assert event.date
    assert event.parameters == {
        "email": order.get_customer_email(),
        "email_type": expected_event_type,
    }


@pytest.mark.parametrize(
    "event_fun, expected_event_type",
    [
        (event_order_cancelled_notification, OrderEventsEmails.ORDER_CANCEL),
        (event_fulfillment_confirmed_notification, OrderEventsEmails.FULFILLMENT),
        (event_fulfillment_digital_links_notification, OrderEventsEmails.DIGITAL_LINKS),
        (event_order_refunded_notification, OrderEventsEmails.ORDER_REFUND),
    ],
)
def test_email_sent_event_with_app(order, app, event_fun, expected_event_type):
    event_fun(
        order_id=order.id, user_id=None, app_id=app.pk, customer_email=order.user_email
    )
    events = order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event
    assert event.type == OrderEvents.EMAIL_SENT
    assert not event.user
    assert event.app == app
    assert event.order is order
    assert event.date
    assert event.parameters == {
        "email": order.get_customer_email(),
        "email_type": expected_event_type,
    }


@pytest.mark.parametrize(
    "event_fun, expected_event_type",
    [
        (event_order_confirmation_notification, OrderEventsEmails.ORDER_CONFIRMATION),
        (event_payment_confirmed_notification, OrderEventsEmails.PAYMENT),
    ],
)
def test_email_sent_event_without_user_pk(order, event_fun, expected_event_type):
    event_fun(order_id=order.id, user_id=None, customer_email=order.user_email)
    events = order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event
    assert event.type == OrderEvents.EMAIL_SENT
    assert not event.user
    assert event.order is order
    assert event.date
    assert event.parameters == {
        "email": order.get_customer_email(),
        "email_type": expected_event_type,
    }


@pytest.mark.parametrize(
    "event_fun, expected_event_type",
    [
        (event_order_cancelled_notification, OrderEventsEmails.ORDER_CANCEL),
        (event_fulfillment_confirmed_notification, OrderEventsEmails.FULFILLMENT),
        (event_fulfillment_digital_links_notification, OrderEventsEmails.DIGITAL_LINKS),
        (event_order_refunded_notification, OrderEventsEmails.ORDER_REFUND),
    ],
)
def test_email_sent_event_without_user_and_app_pk(
    order, event_fun, expected_event_type
):
    event_fun(
        order_id=order.id, user_id=None, app_id=None, customer_email=order.user_email
    )
    events = order.events.all()
    assert len(events) == 1
    event = events[0]
    assert event
    assert event.type == OrderEvents.EMAIL_SENT
    assert not event.user
    assert not event.app
    assert event.order is order
    assert event.date
    assert event.parameters == {
        "email": order.get_customer_email(),
        "email_type": expected_event_type,
    }


GET_ORDER_AVAILABLE_COLLECTION_POINTS = """
    query getAvailableCollectionPointsForOrder(
        $id: ID!
    ){
      order(id:$id){
        availableCollectionPoints{
          name
        }
      }
    }
"""


def test_available_collection_points_for_preorders_variants_in_order(
    api_client, staff_api_client, order_with_preorder_lines
):
    expected_collection_points = list(
        Warehouse.objects.for_channel(order_with_preorder_lines.channel_id)
        .exclude(
            click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
        )
        .values("name")
    )
    response = staff_api_client.post_graphql(
        GET_ORDER_AVAILABLE_COLLECTION_POINTS,
        variables={
            "id": graphene.Node.to_global_id("Order", order_with_preorder_lines.id)
        },
    )
    response_content = get_graphql_content(response)
    assert (
        expected_collection_points
        == response_content["data"]["order"]["availableCollectionPoints"]
    )


def test_available_collection_points_for_preorders_and_regular_variants_in_order(
    api_client,
    staff_api_client,
    order_with_preorder_lines,
):
    expected_collection_points = list(
        Warehouse.objects.for_channel(order_with_preorder_lines.channel_id)
        .exclude(
            click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
        )
        .values("name")
    )

    response = staff_api_client.post_graphql(
        GET_ORDER_AVAILABLE_COLLECTION_POINTS,
        variables={
            "id": graphene.Node.to_global_id("Order", order_with_preorder_lines.id)
        },
    )
    response_content = get_graphql_content(response)
    assert (
        expected_collection_points
        == response_content["data"]["order"]["availableCollectionPoints"]
    )


def test_order_update_total_authorize_data_with_payment(
    order_with_lines, payment_txn_preauth
):
    # given
    authorized_amount = payment_txn_preauth.transactions.first().amount

    # when
    update_order_authorize_data(order_with_lines)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.total_authorized == Money(
        authorized_amount, order_with_lines.currency
    )


def test_order_update_total_authorize_data_with_transaction_item(order_with_lines):
    # given
    first_authorized_amount = Decimal(10)
    order_with_lines.payment_transactions.create(
        authorized_value=first_authorized_amount,
        charged_value=Decimal(12),
        currency=order_with_lines.currency,
    )
    second_authorized_amount = Decimal(3)
    order_with_lines.payment_transactions.create(
        authorized_value=second_authorized_amount,
        charged_value=Decimal(12),
        currency=order_with_lines.currency,
    )

    # when
    update_order_authorize_data(order_with_lines)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.total_authorized == Money(
        first_authorized_amount + second_authorized_amount, order_with_lines.currency
    )


def test_order_update_total_authorize_data_with_transaction_item_and_payment(
    order_with_lines, payment_txn_preauth
):
    # given
    first_authorized_amount = payment_txn_preauth.transactions.first().amount

    second_authorized_amount = Decimal(3)
    order_with_lines.payment_transactions.create(
        authorized_value=second_authorized_amount,
        charged_value=Decimal(12),
        currency=order_with_lines.currency,
    )

    # when
    update_order_authorize_data(order_with_lines)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.total_authorized == Money(
        first_authorized_amount + second_authorized_amount, order_with_lines.currency
    )


def test_order_update_charge_data_with_payment(order_with_lines, payment_txn_captured):
    # given
    charged_amount = payment_txn_captured.transactions.first().amount

    # when
    update_order_charge_data(order_with_lines)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.total_charged == Money(
        charged_amount, order_with_lines.currency
    )


def test_order_update_charge_data_with_transaction_item(order_with_lines):
    # given
    first_charged_amount = Decimal(10)
    order_with_lines.payment_transactions.create(
        charged_value=first_charged_amount,
        authorized_value=Decimal(12),
        currency=order_with_lines.currency,
    )
    second_charged_amount = Decimal(3)
    order_with_lines.payment_transactions.create(
        authorized_value=Decimal(11),
        charged_value=second_charged_amount,
        currency=order_with_lines.currency,
    )

    # when
    update_order_charge_data(order_with_lines)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.total_charged == Money(
        first_charged_amount + second_charged_amount, order_with_lines.currency
    )


def test_order_update_charge_data_with_transaction_item_and_payment(
    order_with_lines, payment_txn_captured
):
    # given
    first_charged_amount = payment_txn_captured.transactions.first().amount
    second_charged_amount = Decimal(3)
    order_with_lines.payment_transactions.create(
        authorized_value=Decimal(11),
        charged_value=second_charged_amount,
        currency=order_with_lines.currency,
    )

    # when
    update_order_charge_data(order_with_lines)

    # then
    order_with_lines.refresh_from_db()
    assert order_with_lines.total_charged == Money(
        first_charged_amount + second_charged_amount, order_with_lines.currency
    )
