from decimal import Decimal

import graphene

from ...discount import DiscountValueType
from ..models import OrderLine
from ..search import prepare_order_search_document_value, update_order_search_document


def test_update_order_search_document(order):
    # given
    order.search_document = ""
    order.save(update_fields=["search_document"])
    assert not order.search_document

    # when
    update_order_search_document(order)

    # then
    assert f"{order.id}\n{order.user_email}\n".lower() in order.search_document


def test_prepare_order_search_document_value(
    order_with_lines, address_usa, payment_dummy
):
    # given
    order = order_with_lines
    order.shipping_address = address_usa
    order.save(update_fields=["shipping_address"])
    discount = order.discounts.create(
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
    search_document_value = prepare_order_search_document_value(order)

    # then
    assert str(order.id) in search_document_value
    user = order.user
    assert (
        f"{order.user_email}\n{user.email}\n{user.first_name}\n{user.last_name}".lower()
        in search_document_value
    )
    for address in [order.billing_address, order.shipping_address]:
        address_data = (
            f"{address.first_name}\n{address.last_name}\n"
            f"{address.street_address_1}\n{address.street_address_2}\n"
            f"{address.city}\n{address.postal_code}\n{address.country.name}\n"
            f"{address.country.code}\n{address.phone}\n"
        )
        assert address_data.lower() in search_document_value
    assert psp_reference.lower() in search_document_value
    assert discount.name in search_document_value
    assert discount.translated_name in search_document_value
    for line in order.lines.all():
        assert line.product_sku.lower() in search_document_value


def test_prepare_order_search_document_value_empty_relation_fields(
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
    payment_id = graphene.Node.to_global_id("Payment", payment_dummy.pk)

    lines = []
    for line in order.lines.all():
        line.product_sku = None
        lines.append(line)
    OrderLine.objects.bulk_update(lines, ["product_sku"])

    # when
    search_document_value = prepare_order_search_document_value(order)

    # then
    user = order.user
    assert (
        f"#{order.id}\n{order.user_email}\n{user.email}\n"
        f"{user.first_name}\n{user.last_name}\n"
        f"{payment_id}\n".lower() == search_document_value
    )


def test_prepare_order_search_document_value_no_relations_data(order, address_usa):
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
    search_document_value = prepare_order_search_document_value(order)

    # then
    assert f"#{order.id}\n{order.user_email}\n".lower() == search_document_value
