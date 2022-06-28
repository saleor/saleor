from decimal import Decimal

from ...discount import DiscountValueType
from ..models import OrderLine
from ..search import prepare_order_search_vector_value, update_order_search_vector


def test_update_order_search_vector(order):
    # given
    order.search_vector = ""
    order.save(update_fields=["search_vector"])
    assert not order.search_vector

    # when
    update_order_search_vector(order)

    # then
    assert order.search_vector


def test_prepare_order_search_vector_value(
    order_with_lines, address_usa, payment_dummy
):
    # given
    order = order_with_lines
    order.shipping_address = address_usa
    order.save(update_fields=["shipping_address"])
    order.discounts.create(
        value_type=DiscountValueType.FIXED,
        name="discount",
        translated_name="discount translated",
        value=Decimal("20"),
        reason="Discount reason",
        amount=(order.undiscounted_total - order.total).gross,  # type: ignore
    )

    psp_reference = "TestABC"
    payment_dummy.psp_reference = psp_reference
    payment_dummy.save(update_fields=["psp_reference"])

    # when
    search_vector = prepare_order_search_vector_value(order)

    # then
    assert search_vector


def test_prepare_order_search_vector_value_empty_relation_fields(
    order_with_lines, payment_dummy
):
    # given
    order = order_with_lines
    order.billing_address = None
    order.shipping_address = None
    order.save(update_fields=["shipping_address", "billing_address"])
    order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=Decimal("20"),
        reason="Discount reason",
        amount=(order.undiscounted_total - order.total).gross,  # type: ignore
    )

    payment_dummy.psp_reference = None
    payment_dummy.save(update_fields=["psp_reference"])

    lines = []
    for line in order.lines.all():
        line.product_sku = None
        lines.append(line)
    OrderLine.objects.bulk_update(lines, ["product_sku"])

    # when
    search_vector_value = prepare_order_search_vector_value(order)

    # then
    assert search_vector_value


def test_prepare_order_search_vector_value_no_relations_data(order, address_usa):
    # given
    order.shipping_address = address_usa
    order.user = None
    order.billing_address = None
    order.shipping_address = None
    order.save(update_fields=["shipping_address", "billing_address", "user"])

    assert not order.lines.all()
    assert not order.discounts.all()
    assert not order.payments.all()

    # when
    search_vector_value = prepare_order_search_vector_value(order)

    # then
    assert search_vector_value
