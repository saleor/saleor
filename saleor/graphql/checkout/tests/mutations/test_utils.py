import graphene

from .....checkout.fetch import fetch_checkout_lines
from ...mutations.utils import (
    CheckoutLineData,
    group_lines_input_data_on_update,
    group_lines_input_on_add,
)


def test_group_on_add_when_same_variants_in_multiple_lines():
    variant_1_id = graphene.Node.to_global_id("ProductVariant", 1)
    variant_2_id = graphene.Node.to_global_id("ProductVariant", 2)
    variant_3_id = graphene.Node.to_global_id("ProductVariant", 3)
    variant_4_id = graphene.Node.to_global_id("ProductVariant", 4)
    variant_5_id = graphene.Node.to_global_id("ProductVariant", 5)

    lines_data = [
        {"quantity": 8, "variant_id": variant_1_id},
        {"quantity": 2, "variant_id": variant_1_id},
        {"quantity": 6, "variant_id": variant_2_id},
        {"quantity": 1, "variant_id": variant_3_id},
        {"quantity": 6, "variant_id": variant_2_id},
        {"quantity": 1, "variant_id": variant_3_id},
        {"quantity": 8, "variant_id": variant_1_id},
        {"quantity": 2, "variant_id": variant_1_id},
        {"quantity": 922, "variant_id": variant_4_id},
        {"quantity": 6, "variant_id": variant_2_id},
        {"quantity": 1, "variant_id": variant_3_id},
        {"quantity": 6, "variant_id": variant_2_id},
        {"quantity": 1, "variant_id": variant_3_id},
        {"quantity": 1000, "variant_id": variant_5_id},
    ]

    expected = [
        CheckoutLineData(
            variant_id=str(id + 1),
            line_id=None,
            quantity=quantity,
            quantity_to_update=True,
            custom_price=None,
            custom_price_to_update=False,
        )
        for id, quantity in enumerate([20, 24, 4, 922, 1000])
    ]

    assert expected == group_lines_input_on_add(lines_data)


def test_group_on_add_when_same_variants_in_multiple_lines_and_price_provided():
    variant_1_id = graphene.Node.to_global_id("ProductVariant", 1)
    variant_2_id = graphene.Node.to_global_id("ProductVariant", 2)

    lines_data = [
        {"quantity": 6, "variant_id": variant_1_id, "price": 1.22},
        {"quantity": 6, "variant_id": variant_1_id},
        {"quantity": 1, "variant_id": variant_2_id, "price": 33.2},
        {"quantity": 1, "variant_id": variant_2_id, "price": 10},
    ]

    expected = [
        CheckoutLineData(
            variant_id="1",
            line_id=None,
            quantity=12,
            quantity_to_update=True,
            custom_price=1.22,
            custom_price_to_update=True,
        ),
        CheckoutLineData(
            variant_id="2",
            line_id=None,
            quantity=2,
            quantity_to_update=True,
            custom_price=10,
            custom_price_to_update=True,
        ),
    ]

    assert expected == group_lines_input_on_add(lines_data)


def test_group_on_add_when_same_variants_in_multiple_lines_and_force_new_line():
    variant_1_id = graphene.Node.to_global_id("ProductVariant", 1)
    variant_2_id = graphene.Node.to_global_id("ProductVariant", 2)

    lines_data = [
        {"quantity": 6, "variant_id": variant_1_id, "price": 1.22},
        {"quantity": 6, "variant_id": variant_1_id, "force_new_line": True},
        {"quantity": 1, "variant_id": variant_2_id, "price": 33.2},
        {"quantity": 1, "variant_id": variant_2_id, "price": 10},
    ]

    expected = [
        CheckoutLineData(
            variant_id="1",
            line_id=None,
            quantity=6,
            quantity_to_update=True,
            custom_price=None,
            custom_price_to_update=False,
        ),
        CheckoutLineData(
            variant_id="1",
            line_id=None,
            quantity=6,
            quantity_to_update=True,
            custom_price=1.22,
            custom_price_to_update=True,
        ),
        CheckoutLineData(
            variant_id="2",
            line_id=None,
            quantity=2,
            quantity_to_update=True,
            custom_price=10,
            custom_price_to_update=True,
        ),
    ]

    assert expected == group_lines_input_on_add(lines_data)


def test_group_on_update_when_line_id_as_parameter_provided():
    line_1_id = graphene.Node.to_global_id("CheckoutLine", "abc")
    line_2_id = graphene.Node.to_global_id("CheckoutLine", "qwe")

    lines_data = [
        {"quantity": 6, "line_id": line_1_id, "price": 1.22},
        {"quantity": 1, "line_id": line_2_id, "price": 10},
    ]

    expected = [
        CheckoutLineData(
            variant_id=None,
            line_id="abc",
            quantity=6,
            quantity_to_update=True,
            custom_price=1.22,
            custom_price_to_update=True,
        ),
        CheckoutLineData(
            variant_id=None,
            line_id="qwe",
            quantity=1,
            quantity_to_update=True,
            custom_price=10,
            custom_price_to_update=True,
        ),
    ]

    assert expected == group_lines_input_data_on_update(lines_data)


def test_group_on_update_when_one_line_and_mixed_parameters_provided(
    checkout_with_item,
):
    line = checkout_with_item.lines.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant_id)
    line_id = graphene.Node.to_global_id("CheckoutLine", line.id)

    existing_checkout_lines, _ = fetch_checkout_lines(checkout_with_item)

    lines_data = [
        {"quantity": 6, "variant_id": variant_id, "price": 1.22},
        {"quantity": 1, "line_id": line_id, "price": 10},
    ]

    expected = [
        CheckoutLineData(
            variant_id=str(line.variant_id),
            line_id=str(line.id),
            quantity=7,
            quantity_to_update=True,
            custom_price=10,
            custom_price_to_update=True,
        )
    ]
    assert expected == group_lines_input_data_on_update(
        lines_data, existing_checkout_lines
    )
