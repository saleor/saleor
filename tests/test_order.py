from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from prices import Money, TaxedMoney

from saleor.core.weight import zero_weight
from saleor.discount.models import (
    DiscountValueType,
    NotApplicable,
    Voucher,
    VoucherType,
)
from saleor.discount.utils import validate_voucher_in_order
from saleor.order import OrderEvents, OrderStatus, models
from saleor.order.emails import send_fulfillment_confirmation_to_customer
from saleor.order.events import OrderEvent, OrderEventsEmails, email_sent_event
from saleor.order.models import Order
from saleor.order.templatetags.order_lines import display_translated_order_line_name
from saleor.order.utils import (
    add_variant_to_draft_order,
    change_order_line_quantity,
    delete_order_line,
    get_voucher_discount_for_order,
    recalculate_order,
    restock_fulfillment_lines,
    restock_order_lines,
    update_order_prices,
    update_order_status,
)
from saleor.payment import ChargeStatus
from saleor.payment.models import Payment
from saleor.product.models import Collection
from saleor.warehouse.models import Stock

from .utils import get_quantity_allocated_for_stock


def test_total_setter():
    price = TaxedMoney(net=Money(10, "USD"), gross=Money(15, "USD"))
    order = models.Order()
    order.total = price
    assert order.total_net_amount == Decimal(10)
    assert order.total.net == Money(10, "USD")
    assert order.total_gross_amount == Decimal(15)
    assert order.total.gross == Money(15, "USD")
    assert order.total.tax == Money(5, "USD")


def test_order_get_subtotal(order_with_lines):
    order_with_lines.discount_name = "Test discount"
    order_with_lines.discount = order_with_lines.total.gross * Decimal("0.5")
    recalculate_order(order_with_lines)

    target_subtotal = order_with_lines.total - order_with_lines.shipping_price
    target_subtotal += order_with_lines.discount
    assert order_with_lines.get_subtotal() == target_subtotal


def test_add_variant_to_draft_order_adds_line_for_new_variant(
    order_with_lines, product, product_translation_fr, settings
):
    order = order_with_lines
    variant = product.variants.get()
    lines_before = order.lines.count()
    settings.LANGUAGE_CODE = "fr"
    add_variant_to_draft_order(order, variant, 1)

    line = order.lines.last()
    assert order.lines.count() == lines_before + 1
    assert line.product_sku == variant.sku
    assert line.quantity == 1
    assert line.unit_price == TaxedMoney(net=Money(10, "USD"), gross=Money(10, "USD"))
    assert line.translated_product_name == str(variant.product.translated)
    assert line.variant_name == str(variant)
    assert line.product_name == str(variant.product)


def test_add_variant_to_draft_order_not_allocates_stock_for_new_variant(
    order_with_lines, product
):
    variant = product.variants.get()
    stock = Stock.objects.get(product_variant=variant)

    stock_before = get_quantity_allocated_for_stock(stock)

    add_variant_to_draft_order(order_with_lines, variant, 1)

    stock.refresh_from_db()
    assert get_quantity_allocated_for_stock(stock) == stock_before


def test_add_variant_to_draft_order_edits_line_for_existing_variant(order_with_lines):
    existing_line = order_with_lines.lines.first()
    variant = existing_line.variant
    lines_before = order_with_lines.lines.count()
    line_quantity_before = existing_line.quantity

    add_variant_to_draft_order(order_with_lines, variant, 1)

    existing_line.refresh_from_db()
    assert order_with_lines.lines.count() == lines_before
    assert existing_line.product_sku == variant.sku
    assert existing_line.quantity == line_quantity_before + 1


def test_add_variant_to_draft_order_not_allocates_stock_for_existing_variant(
    order_with_lines,
):
    existing_line = order_with_lines.lines.first()
    variant = existing_line.variant
    stock = Stock.objects.get(product_variant=variant)
    stock_before = get_quantity_allocated_for_stock(stock)
    quantity_before = existing_line.quantity
    quantity_unfulfilled_before = existing_line.quantity_unfulfilled

    add_variant_to_draft_order(order_with_lines, variant, 1)

    stock.refresh_from_db()
    existing_line.refresh_from_db()
    assert get_quantity_allocated_for_stock(stock) == stock_before
    assert existing_line.quantity == quantity_before + 1
    assert existing_line.quantity_unfulfilled == quantity_unfulfilled_before + 1


@pytest.mark.parametrize("track_inventory", (True, False))
def test_restock_order_lines(order_with_lines, track_inventory):

    order = order_with_lines
    line_1 = order.lines.first()
    line_2 = order.lines.last()

    line_1.variant.track_inventory = track_inventory
    line_2.variant.track_inventory = track_inventory

    line_1.variant.save()
    line_2.variant.save()
    stock_1 = Stock.objects.get(product_variant=line_1.variant)
    stock_2 = Stock.objects.get(product_variant=line_2.variant)

    stock_1_quantity_allocated_before = get_quantity_allocated_for_stock(stock_1)
    stock_2_quantity_allocated_before = get_quantity_allocated_for_stock(stock_2)

    stock_1_quantity_before = stock_1.quantity
    stock_2_quantity_before = stock_2.quantity

    restock_order_lines(order)

    stock_1.refresh_from_db()
    stock_2.refresh_from_db()

    if track_inventory:
        assert get_quantity_allocated_for_stock(stock_1) == (
            stock_1_quantity_allocated_before - line_1.quantity
        )
        assert get_quantity_allocated_for_stock(stock_2) == (
            stock_2_quantity_allocated_before - line_2.quantity
        )
    else:
        assert get_quantity_allocated_for_stock(stock_1) == (
            stock_1_quantity_allocated_before
        )
        assert get_quantity_allocated_for_stock(stock_2) == (
            stock_2_quantity_allocated_before
        )

    assert stock_1.quantity == stock_1_quantity_before
    assert stock_2.quantity == stock_2_quantity_before
    assert line_1.quantity_fulfilled == 0
    assert line_2.quantity_fulfilled == 0


def test_restock_fulfilled_order_lines(fulfilled_order):
    line_1 = fulfilled_order.lines.first()
    line_2 = fulfilled_order.lines.last()
    stock_1 = Stock.objects.get(product_variant=line_1.variant)
    stock_2 = Stock.objects.get(product_variant=line_2.variant)
    stock_1_quantity_allocated_before = get_quantity_allocated_for_stock(stock_1)
    stock_2_quantity_allocated_before = get_quantity_allocated_for_stock(stock_2)
    stock_1_quantity_before = stock_1.quantity
    stock_2_quantity_before = stock_2.quantity

    restock_order_lines(fulfilled_order)

    stock_1.refresh_from_db()
    stock_2.refresh_from_db()
    assert (
        get_quantity_allocated_for_stock(stock_1) == stock_1_quantity_allocated_before
    )
    assert (
        get_quantity_allocated_for_stock(stock_2) == stock_2_quantity_allocated_before
    )
    assert stock_1.quantity == stock_1_quantity_before + line_1.quantity
    assert stock_2.quantity == stock_2_quantity_before + line_2.quantity


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


def test_update_order_status(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    line = fulfillment.lines.first()
    order_line = line.order_line

    order_line.quantity_fulfilled -= line.quantity
    order_line.save()
    line.delete()
    update_order_status(fulfilled_order)

    assert fulfilled_order.status == OrderStatus.PARTIALLY_FULFILLED

    line = fulfillment.lines.first()
    order_line = line.order_line

    order_line.quantity_fulfilled -= line.quantity
    order_line.save()
    line.delete()
    update_order_status(fulfilled_order)

    assert fulfilled_order.status == OrderStatus.UNFULFILLED


def test_order_queryset_confirmed(draft_order):
    other_orders = [
        Order.objects.create(status=OrderStatus.UNFULFILLED),
        Order.objects.create(status=OrderStatus.PARTIALLY_FULFILLED),
        Order.objects.create(status=OrderStatus.FULFILLED),
        Order.objects.create(status=OrderStatus.CANCELED),
    ]

    confirmed_orders = Order.objects.confirmed()

    assert draft_order not in confirmed_orders
    assert all([order in confirmed_orders for order in other_orders])


def test_order_queryset_drafts(draft_order):
    other_orders = [
        Order.objects.create(status=OrderStatus.UNFULFILLED),
        Order.objects.create(status=OrderStatus.PARTIALLY_FULFILLED),
        Order.objects.create(status=OrderStatus.FULFILLED),
        Order.objects.create(status=OrderStatus.CANCELED),
    ]

    draft_orders = Order.objects.drafts()

    assert draft_order in draft_orders
    assert all([order not in draft_orders for order in other_orders])


def test_order_queryset_to_ship(settings):
    total = TaxedMoney(net=Money(10, "USD"), gross=Money(15, "USD"))
    orders_to_ship = [
        Order.objects.create(status=OrderStatus.UNFULFILLED, total=total),
        Order.objects.create(status=OrderStatus.PARTIALLY_FULFILLED, total=total),
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
        Order.objects.create(status=OrderStatus.DRAFT, total=total),
        Order.objects.create(status=OrderStatus.UNFULFILLED, total=total),
        Order.objects.create(status=OrderStatus.PARTIALLY_FULFILLED, total=total),
        Order.objects.create(status=OrderStatus.FULFILLED, total=total),
        Order.objects.create(status=OrderStatus.CANCELED, total=total),
    ]

    orders = Order.objects.ready_to_fulfill()

    assert all([order in orders for order in orders_to_ship])
    assert all([order not in orders for order in orders_not_to_ship])


def test_queryset_ready_to_capture():
    total = TaxedMoney(net=Money(10, "USD"), gross=Money(15, "USD"))

    preauth_order = Order.objects.create(status=OrderStatus.UNFULFILLED, total=total)
    Payment.objects.create(
        order=preauth_order, charge_status=ChargeStatus.NOT_CHARGED, is_active=True
    )

    Order.objects.create(status=OrderStatus.DRAFT, total=total)
    Order.objects.create(status=OrderStatus.UNFULFILLED, total=total)
    Order.objects.create(status=OrderStatus.CANCELED, total=total)

    qs = Order.objects.ready_to_capture()
    assert preauth_order in qs
    statuses = [o.status for o in qs]
    assert OrderStatus.DRAFT not in statuses
    assert OrderStatus.CANCELED not in statuses


def test_update_order_prices(order_with_lines):
    address = order_with_lines.shipping_address
    address.country = "DE"
    address.save()

    line_1 = order_with_lines.lines.first()
    line_2 = order_with_lines.lines.last()
    price_1 = line_1.variant.get_price()
    price_1 = TaxedMoney(net=price_1, gross=price_1)
    price_2 = line_2.variant.get_price()
    price_2 = TaxedMoney(net=price_2, gross=price_2)
    shipping_price = order_with_lines.shipping_method.get_total()
    shipping_price = TaxedMoney(net=shipping_price, gross=shipping_price)

    update_order_prices(order_with_lines, None)

    line_1.refresh_from_db()
    line_2.refresh_from_db()
    assert line_1.unit_price == price_1
    assert line_2.unit_price == price_2
    assert order_with_lines.shipping_price == shipping_price
    total = line_1.quantity * price_1 + line_2.quantity * price_2 + shipping_price
    assert order_with_lines.total == total


def _calculate_order_weight_from_lines(order):
    weight = zero_weight()
    for line in order:
        weight += line.variant.get_weight() * line.quantity
    return weight


def test_calculate_order_weight(order_with_lines):
    order_weight = order_with_lines.weight
    calculated_weight = _calculate_order_weight_from_lines(order_with_lines)
    assert calculated_weight == order_weight


def test_order_weight_add_more_variant(order_with_lines):
    variant = order_with_lines.lines.first().variant
    add_variant_to_draft_order(order_with_lines, variant, 2)
    order_with_lines.refresh_from_db()
    assert order_with_lines.weight == _calculate_order_weight_from_lines(
        order_with_lines
    )


def test_order_weight_add_new_variant(order_with_lines, product):
    variant = product.variants.first()
    add_variant_to_draft_order(order_with_lines, variant, 2)
    order_with_lines.refresh_from_db()
    assert order_with_lines.weight == _calculate_order_weight_from_lines(
        order_with_lines
    )


def test_order_weight_change_line_quantity(order_with_lines):
    line = order_with_lines.lines.first()
    new_quantity = line.quantity + 2
    change_order_line_quantity(None, line, new_quantity, line.quantity)
    order_with_lines.refresh_from_db()
    assert order_with_lines.weight == _calculate_order_weight_from_lines(
        order_with_lines
    )


def test_order_weight_delete_line(order_with_lines):
    line = order_with_lines.lines.first()
    delete_order_line(line)
    assert order_with_lines.weight == _calculate_order_weight_from_lines(
        order_with_lines
    )


def test_get_order_weight_non_existing_product(order_with_lines, product):
    # Removing product should not affect order's weight
    order = order_with_lines
    variant = product.variants.first()
    add_variant_to_draft_order(order, variant, 1)
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
        voucher, subtotal.gross, quantity, customer_email
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
    "product_name, variant_name, translated_product_name, translated_variant_name,"
    "expected_display_name",
    [
        ("product", "variant", "", "", "product (variant)"),
        ("product", "", "", "", "product"),
        ("product", "", "productPL", "", "productPL"),
        ("product", "variant", "productPL", "", "productPL (variant)"),
        ("product", "variant", "productPL", "variantPl", "productPL (variantPl)"),
        ("product", "variant", "", "variantPl", "product (variantPl)"),
    ],
)
def test_display_translated_order_line_name(
    product_name,
    variant_name,
    translated_product_name,
    translated_variant_name,
    expected_display_name,
):
    order_line = MagicMock(
        product_name=product_name,
        variant_name=variant_name,
        translated_product_name=translated_product_name,
        translated_variant_name=translated_variant_name,
    )
    display_name = display_translated_order_line_name(order_line)
    assert display_name == expected_display_name


@pytest.mark.parametrize(
    "subtotal, discount_value, discount_type, min_spent_amount, expected_value",
    [
        ("100", 10, DiscountValueType.FIXED, None, 10),
        ("100.05", 10, DiscountValueType.PERCENTAGE, 100, 10),
    ],
)
def test_value_voucher_order_discount(
    subtotal, discount_value, discount_type, min_spent_amount, expected_value
):
    voucher = Voucher(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_type,
        discount_value=discount_value,
        min_spent=Money(min_spent_amount, "USD")
        if min_spent_amount is not None
        else None,
    )
    subtotal = Money(subtotal, "USD")
    subtotal = TaxedMoney(net=subtotal, gross=subtotal)
    order = Mock(get_subtotal=Mock(return_value=subtotal), voucher=voucher)
    discount = get_voucher_discount_for_order(order)
    assert discount == Money(expected_value, "USD")


@pytest.mark.parametrize(
    "shipping_cost, discount_value, discount_type, expected_value",
    [(10, 50, DiscountValueType.PERCENTAGE, 5), (10, 20, DiscountValueType.FIXED, 10)],
)
def test_shipping_voucher_order_discount(
    shipping_cost, discount_value, discount_type, expected_value
):
    voucher = Voucher(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        min_spent_amount=None,
    )
    subtotal = Money(100, "USD")
    subtotal = TaxedMoney(net=subtotal, gross=subtotal)
    shipping_total = Money(shipping_cost, "USD")
    order = Mock(
        get_subtotal=Mock(return_value=subtotal),
        shipping_price=shipping_total,
        voucher=voucher,
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
    total, total_quantity, min_spent_amount, min_checkout_items_quantity, voucher_type
):
    voucher = Voucher(
        code="unique",
        type=voucher_type,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
        min_spent=(
            Money(min_spent_amount, "USD") if min_spent_amount is not None else None
        ),
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    price = Money(total, "USD")
    price = TaxedMoney(net=price, gross=price)
    order = Mock(
        get_subtotal=Mock(return_value=price),
        get_total_quantity=Mock(return_value=total_quantity),
        shipping_price=price,
        voucher=voucher,
    )
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order)


def test_product_voucher_checkout_discount_raises_not_applicable(
    order_with_lines, product_with_images
):
    discounted_product = product_with_images
    voucher = Voucher(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
    )
    voucher.save()
    voucher.products.add(discounted_product)
    order_with_lines.voucher = voucher
    order_with_lines.save()
    # Offer is valid only for products listed in voucher
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order_with_lines)


def test_category_voucher_checkout_discount_raises_not_applicable(order_with_lines):
    discounted_collection = Collection.objects.create(
        name="Discounted", slug="discount"
    )
    voucher = Voucher(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
    )
    voucher.save()
    voucher.collections.add(discounted_collection)
    order_with_lines.voucher = voucher
    order_with_lines.save()
    # Discount should be valid only for items in the discounted collections
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order_with_lines)


def test_ordered_item_change_quantity(transactional_db, order_with_lines):
    assert not order_with_lines.events.count()
    lines = order_with_lines.lines.all()
    change_order_line_quantity(None, lines[1], lines[1].quantity, 0)
    change_order_line_quantity(None, lines[0], lines[0].quantity, 0)
    assert order_with_lines.get_total_quantity() == 0


@patch("saleor.order.actions.emails.send_fulfillment_confirmation")
@pytest.mark.parametrize(
    "has_standard,has_digital", ((True, True), (True, False), (False, True))
)
def test_send_fulfillment_order_lines_mails(
    mocked_send_fulfillment_confirmation,
    staff_user,
    fulfilled_order,
    fulfillment,
    digital_content,
    has_standard,
    has_digital,
):

    order = fulfilled_order
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
        order=order, fulfillment=fulfillment, user=staff_user
    )
    events = OrderEvent.objects.all()

    mocked_send_fulfillment_confirmation.delay.assert_called_once_with(
        order.pk, fulfillment.pk
    )

    # Ensure the standard fulfillment event was triggered
    assert events[0].user == staff_user
    assert events[0].parameters == {
        "email": order.user_email,
        "email_type": OrderEventsEmails.FULFILLMENT,
    }

    if has_digital:
        assert len(events) == 2
        assert events[1].user == staff_user
        assert events[1].parameters == {
            "email": order.user_email,
            "email_type": OrderEventsEmails.DIGITAL_LINKS,
        }
    else:
        assert len(events) == 1


def test_email_sent_event_with_user_pk(order):
    user = order.user
    email_type = OrderEventsEmails.PAYMENT
    email_sent_event(order=order, user=None, email_type=email_type, user_pk=user.pk)
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
        "email_type": email_type,
    }


def test_email_sent_event_with_user(order):
    user = order.user
    email_type = OrderEventsEmails.PAYMENT
    email_sent_event(order=order, user=user, email_type=email_type)
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
        "email_type": email_type,
    }


def test_email_sent_event_without_user_and_user_pk(order):
    email_type = OrderEventsEmails.PAYMENT
    email_sent_event(order=order, user=None, email_type=email_type)
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
        "email_type": email_type,
    }
