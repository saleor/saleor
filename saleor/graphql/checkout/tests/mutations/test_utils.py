import graphene

from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.models import CheckoutDelivery
from .....plugins.manager import get_plugins_manager
from ...mutations.utils import (
    CheckoutLineData,
    assign_delivery_method_to_checkout,
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


def test_assign_delivery_method_to_checkout_delivery_method_to_none(
    checkout_with_delivery_method_for_cc,
):
    # given
    checkout = checkout_with_delivery_method_for_cc

    lines_info, _ = fetch_checkout_lines(checkout)

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    # when
    assign_delivery_method_to_checkout(checkout_info, lines_info, manager, None)

    # then
    assert checkout_with_delivery_method_for_cc.collection_point_id is None
    assert checkout_with_delivery_method_for_cc.shipping_address_id is None
    assert checkout_info.collection_point is None


def test_assign_delivery_method_to_checkout_delivery_method_to_external(
    checkout_with_shipping_method, shipping_app
):
    # given
    checkout = checkout_with_shipping_method

    lines_info, _ = fetch_checkout_lines(checkout)

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    app_shipping_id = "abcd"
    app_shipping_name = "Shipping"
    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{app_shipping_id}"
    )

    shipping_method = CheckoutDelivery.objects.create(
        checkout=checkout,
        external_shipping_method_id=method_id,
        name=app_shipping_name,
        price_amount="10.00",
        currency="USD",
        maximum_delivery_days=7,
        is_external=True,
    )

    # when
    assign_delivery_method_to_checkout(
        checkout_info, lines_info, manager, shipping_method
    )

    # then
    assert checkout.shipping_method_name == app_shipping_name
    assert checkout.assigned_delivery.shipping_method_id == method_id
    assert checkout.assigned_delivery.name == app_shipping_name
    assert checkout_info.collection_point is None


def test_assign_delivery_method_to_checkout_delivery_method_to_cc(
    checkout, shipping_method_weight_based, warehouses_for_cc, checkout_delivery
):
    # given
    checkout.assigned_delivery = checkout_delivery(
        checkout, shipping_method_weight_based
    )
    checkout.shipping_method_name = shipping_method_weight_based.name

    lines_info, _ = fetch_checkout_lines(checkout)

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    collection_point = warehouses_for_cc[0]

    # when
    assign_delivery_method_to_checkout(
        checkout_info, lines_info, manager, collection_point
    )

    # then
    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)
    assert checkout.assigned_delivery is None
    assert checkout.shipping_method_name is None
