from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from prices import Money, TaxedMoney

from ...core.utils.translations import get_translation
from ...core.weight import zero_weight
from ...discount import DiscountType, RewardValueType
from ...discount.interface import VariantPromotionRuleInfo
from ...discount.models import (
    DiscountValueType,
)
from ...discount.utils.voucher import validate_voucher_in_order
from ...graphql.core.utils import to_global_id_or_none
from ...graphql.order.utils import OrderLineData
from ...graphql.tests.utils import get_graphql_content
from ...payment import ChargeStatus
from ...payment.models import Payment
from ...plugins.manager import get_plugins_manager
from ...tests.fixtures import recalculate_order
from ...warehouse import WarehouseClickAndCollectOption
from ...warehouse.models import Stock, Warehouse
from ...warehouse.tests.utils import get_quantity_allocated_for_stock
from .. import FulfillmentStatus, OrderChargeStatus, OrderEvents, OrderStatus
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
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=order_with_lines.total.gross.amount * Decimal("0.5"),
        amount_value=order_with_lines.total.gross.amount * Decimal("0.5"),
        name="Test discount",
    )

    fetch_order_prices_if_expired(
        order_with_lines, get_plugins_manager(allow_replica=False), force_update=True
    )
    target_subtotal = order_with_lines.total - order_with_lines.shipping_price
    assert order_with_lines.subtotal == target_subtotal


def test_recalculate_order_keeps_weight_unit(order_with_lines):
    initial_weight_unit = order_with_lines.weight.unit
    recalculate_order(order_with_lines)
    recalculated_weight_unit = order_with_lines.weight.unit
    assert initial_weight_unit == recalculated_weight_unit


def test_add_variant_to_order_adds_line_for_new_variant(
    order_with_lines,
    product,
    anonymous_plugins,
):
    order = order_with_lines
    variant = product.variants.get()
    lines_before = order.lines.count()
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)

    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )

    line = order.lines.last()
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.product_variant_id == variant.get_global_id()
    assert line.quantity == 1
    assert line.unit_price == TaxedMoney(net=Money(10, "USD"), gross=Money(10, "USD"))
    assert line.variant_name == str(variant)
    assert line.product_name == str(variant.product)
    assert not line.unit_discount_amount
    assert not line.unit_discount_value
    assert not line.unit_discount_reason


def test_add_variant_to_order_adds_line_for_new_variant_on_promotion(
    order_with_lines,
    product,
    anonymous_plugins,
    catalogue_promotion_without_rules,
):
    # given
    order = order_with_lines
    variant = product.variants.first()

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(order.channel)

    channel_listing = variant.channel_listings.get(channel=order.channel)
    channel_listing.discounted_price_amount = (
        channel_listing.price.amount - reward_value
    )
    channel_listing.save(update_fields=["discounted_price_amount"])

    listing_rule = channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel_listing.channel.currency_code,
    )

    lines_before = order.lines.count()
    line_data = OrderLineData(
        variant_id=str(variant.id),
        variant=variant,
        quantity=1,
        rules_info=[
            VariantPromotionRuleInfo(
                rule=rule,
                variant_listing_promotion_rule=listing_rule,
                promotion=catalogue_promotion_without_rules,
                promotion_translation=None,
                rule_translation=None,
            )
        ],
    )

    # when
    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )

    # then
    line = order.lines.last()
    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.quantity == 1
    unit_amount = variant_channel_listing.discounted_price_amount
    assert line.unit_price == TaxedMoney(
        net=Money(unit_amount, "USD"), gross=Money(unit_amount, "USD")
    )
    assert line.variant_name == str(variant)
    assert line.product_name == str(variant.product)

    assert line.unit_discount_amount == reward_value
    assert line.unit_discount_value == reward_value

    assert line.discounts.count() == 1
    assert line.discounts.first().promotion_rule == rule


def test_add_variant_to_draft_order_adds_line_for_variant_with_price_0(
    order_with_lines,
    product,
    anonymous_plugins,
):
    # given
    order = order_with_lines
    variant = product.variants.get()
    variant_channel_listing = variant.channel_listings.get()
    variant_channel_listing.price = Money(0, "USD")
    variant_channel_listing.discounted_price = Money(0, "USD")
    variant_channel_listing.save(
        update_fields=["price_amount", "discounted_price_amount", "currency"]
    )

    lines_before = order.lines.count()
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)

    # when
    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )

    # then
    line = order.lines.last()
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.product_variant_id == variant.get_global_id()
    assert line.quantity == 1
    assert line.unit_price == TaxedMoney(net=Money(0, "USD"), gross=Money(0, "USD"))
    assert line.product_name == variant.product.name


def test_add_variant_to_order_not_allocates_stock_for_new_variant(
    order_with_lines,
    product,
    anonymous_plugins,
):
    variant = product.variants.get()
    stock = Stock.objects.get(product_variant=variant)

    stock_before = get_quantity_allocated_for_stock(stock)

    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)
    add_variant_to_order(
        order=order_with_lines,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )

    stock.refresh_from_db()
    assert get_quantity_allocated_for_stock(stock) == stock_before


def test_add_variant_to_order_edits_line_for_existing_variant(
    order_with_lines, anonymous_plugins
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
        user=None,
        app=None,
        manager=anonymous_plugins,
    )

    existing_line.refresh_from_db()
    assert order_with_lines.lines.count() == lines_before
    assert existing_line.product_sku == variant.sku
    assert existing_line.product_variant_id == variant.get_global_id()
    assert existing_line.quantity == line_quantity_before + 1


def test_add_variant_to_order_not_allocates_stock_for_existing_variant(
    order_with_lines, anonymous_plugins
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
        user=None,
        app=None,
        manager=anonymous_plugins,
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


def test_order_weight_add_more_variant(order_with_lines, anonymous_plugins):
    variant = order_with_lines.lines.first().variant
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=2)

    add_variant_to_order(
        order=order_with_lines,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )
    order_with_lines.refresh_from_db()

    assert order_with_lines.weight == _calculate_order_weight_from_lines(
        order_with_lines
    )


def test_order_weight_add_new_variant(
    order_with_lines,
    product,
    anonymous_plugins,
):
    variant = product.variants.first()
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=2)

    add_variant_to_order(
        order=order_with_lines,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
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
        order.channel,
        get_plugins_manager(allow_replica=False),
    )
    assert order.weight == _calculate_order_weight_from_lines(order)


def test_order_weight_delete_line(lines_info):
    order = lines_info[0].line.order
    line_info = lines_info[0]
    delete_order_line(line_info, get_plugins_manager(allow_replica=False))
    assert order.weight == _calculate_order_weight_from_lines(order)


def test_get_order_weight_non_existing_product(
    order_with_lines,
    product,
    anonymous_plugins,
):
    # Removing product should not affect order's weight
    order = order_with_lines
    variant = product.variants.first()
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)

    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )
    old_weight = order.weight

    product.delete()

    order.refresh_from_db()
    new_weight = order.weight

    assert old_weight == new_weight


@patch("saleor.discount.utils.voucher.validate_voucher")
def test_get_voucher_discount_for_order_voucher_validation(
    mock_validate_voucher, voucher, order_with_lines
):
    order_with_lines.voucher = voucher
    order_with_lines.save()
    subtotal = order_with_lines.subtotal
    quantity = order_with_lines.get_total_quantity()
    customer_email = order_with_lines.get_customer_email()

    validate_voucher_in_order(
        order_with_lines, order_with_lines.lines.all(), order_with_lines.channel
    )

    mock_validate_voucher.assert_called_once_with(
        voucher,
        subtotal.gross,
        quantity,
        customer_email,
        order_with_lines.channel,
        order_with_lines.user,
    )


@patch("saleor.discount.utils.voucher.validate_voucher")
def test_validate_voucher_in_order_without_voucher(
    mock_validate_voucher, order_with_lines
):
    order_with_lines.voucher = None
    order_with_lines.save()

    assert not order_with_lines.voucher

    validate_voucher_in_order(
        order_with_lines, order_with_lines.lines.all(), order_with_lines.channel
    )
    mock_validate_voucher.assert_not_called()


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
        order.channel,
        get_plugins_manager(allow_replica=False),
    )
    change_order_line_quantity(
        staff_user,
        app,
        lines_info[0],
        lines_info[0].quantity,
        0,
        order.channel,
        get_plugins_manager(allow_replica=False),
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
        order.channel,
        get_plugins_manager(allow_replica=False),
    )
    assert line_info.line.total_price == line_info.line.unit_price * new_quantity


@patch("saleor.plugins.manager.PluginsManager.notify")
@pytest.mark.parametrize(
    ("has_standard", "has_digital"), [(True, True), (True, False), (False, True)]
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
    manager = get_plugins_manager(allow_replica=False)
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
    ("has_standard", "has_digital"), [(True, True), (True, False), (False, True)]
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
    manager = get_plugins_manager(allow_replica=False)
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
    ("event_fun", "expected_event_type"),
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
    ("event_fun", "expected_event_type"),
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
    ("event_fun", "expected_event_type"),
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
    ("event_fun", "expected_event_type"),
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
    ("event_fun", "expected_event_type"),
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


def test_add_variant_to_order_adds_line_for_new_variant_on_promotion_with_custom_price(
    order_with_lines,
    product,
    anonymous_plugins,
    catalogue_promotion_without_rules,
):
    # given
    order = order_with_lines
    variant = product.variants.first()

    reward_value = Decimal("5")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(order.channel)

    channel_listing = variant.channel_listings.get(channel=order.channel)
    channel_listing.discounted_price_amount = (
        channel_listing.price.amount - reward_value
    )
    channel_listing.save(update_fields=["discounted_price_amount"])

    listing_rule = channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=channel_listing.channel.currency_code,
    )

    lines_before = order.lines.count()
    price_override = Decimal(15)
    line_data = OrderLineData(
        variant_id=str(variant.id),
        variant=variant,
        quantity=1,
        price_override=price_override,
        rules_info=[
            VariantPromotionRuleInfo(
                rule=rule,
                variant_listing_promotion_rule=listing_rule,
                promotion=catalogue_promotion_without_rules,
                promotion_translation=None,
                rule_translation=None,
            )
        ],
    )

    # when
    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )

    # then
    line = order.lines.last()
    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.quantity == 1
    assert variant_channel_listing.price_amount != price_override
    unit_amount = price_override - reward_value
    assert line.unit_price == TaxedMoney(
        net=Money(unit_amount, "USD"), gross=Money(unit_amount, "USD")
    )
    assert line.variant_name == str(variant)
    assert line.product_name == str(variant.product)

    assert line.unit_discount_amount == reward_value
    assert line.unit_discount_value == reward_value

    assert line.discounts.count() == 1
    assert line.discounts.first().promotion_rule == rule


def test_add_variant_to_order_adds_line_with_custom_price_for_new_variant(
    order_with_lines,
    product,
    anonymous_plugins,
):
    # given
    order = order_with_lines
    variant = product.variants.get()
    lines_before = order.lines.count()
    price_override = Decimal(18)
    line_data = OrderLineData(
        variant_id=str(variant.id),
        variant=variant,
        quantity=1,
        price_override=price_override,
    )

    # when
    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )

    # then
    variant_channel_listing = variant.channel_listings.get(channel=order.channel)
    line = order.lines.last()
    assert order.lines.count() == lines_before + 1
    assert variant_channel_listing.price_amount != price_override
    assert line.product_sku == variant.sku
    assert line.product_variant_id == variant.get_global_id()
    assert line.quantity == 1
    assert line.unit_price == TaxedMoney(
        net=Money(price_override, "USD"), gross=Money(price_override, "USD")
    )
    assert line.variant_name == str(variant)
    assert line.product_name == str(variant.product)
    assert line.base_unit_price_amount == price_override
    assert line.undiscounted_base_unit_price_amount == price_override
    assert not line.unit_discount_amount
    assert not line.unit_discount_value
    assert not line.unit_discount_reason


def test_add_variant_to_order_adds_translations_in_order_language(
    order_with_lines,
    product,
    product_translation_fr,
    variant_translation_fr,
    settings,
    anonymous_plugins,
):
    # given
    language_code = "fr"
    settings.LANGUAGE_CODE = "es"

    order = order_with_lines
    order.language_code = language_code
    order.save(update_fields=["language_code"])
    variant = variant_translation_fr.product_variant
    line_data = OrderLineData(variant_id=str(variant.id), variant=variant, quantity=1)

    # when
    add_variant_to_order(
        order=order,
        line_data=line_data,
        user=None,
        app=None,
        manager=anonymous_plugins,
    )

    # then
    line = order.lines.last()
    assert line.quantity == 1
    assert (
        line.translated_product_name
        == get_translation(variant.product, language_code).name
    )
    assert line.translated_variant_name == get_translation(variant, language_code).name


@pytest.mark.parametrize(
    ("granted_refund_amount", "charged_amount", "expected_charge_status"),
    [
        # granted refund contains part of the order's total, charge amount is 0
        (Decimal("10.40"), Decimal("0"), OrderChargeStatus.NONE),
        # granted refund covers the whole order's total, charge amount is 0
        # status is FULL, as the order total - granted refund amount is 0.
        # It means that a charge amount equal to 0 fully covers the order total (0)
        (Decimal("98.40"), Decimal("0"), OrderChargeStatus.FULL),
        (Decimal("0"), Decimal("0"), OrderChargeStatus.NONE),
        (Decimal("0"), Decimal("11.00"), OrderChargeStatus.PARTIAL),
        (Decimal("4"), Decimal("11.00"), OrderChargeStatus.PARTIAL),
        # granted refund covers 88.40 of total, which is 98.40. Charge amount is 10.
        # status is FULL, as the order total - granted refund amount is 10.
        (Decimal("88.40"), Decimal("10.00"), OrderChargeStatus.FULL),
        (Decimal("0"), Decimal("98.40"), OrderChargeStatus.FULL),
        # granted refund covers 88.40 of total, which is 98.40. Charge amount is 98.40.
        # status is OVERCHARGED as the charge amount is greater than the order
        # total - granted refund amount
        (Decimal("88.40"), Decimal("98.40"), OrderChargeStatus.OVERCHARGED),
    ],
)
def test_order_update_charge_status_with_transaction_item_and_granted_refund(
    granted_refund_amount,
    charged_amount,
    expected_charge_status,
    order_with_lines,
    staff_user,
):
    # given
    assert order_with_lines.total.gross.amount == Decimal("98.40")
    order_with_lines.payment_transactions.create(
        charged_value=charged_amount,
        authorized_value=Decimal(12),
        currency=order_with_lines.currency,
    )

    order_with_lines.granted_refunds.create(
        amount_value=granted_refund_amount,
        currency="USD",
        reason="Test reason",
        user=staff_user,
    )

    # when
    update_order_charge_data(order_with_lines)

    # then
    order_with_lines.refresh_from_db()

    assert order_with_lines.charge_status == expected_charge_status
