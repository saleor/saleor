from decimal import Decimal

from ..utils import (
    assign_collection_point_to_checkout,
    assign_shipping_method_to_checkout,
    remove_delivery_method_from_checkout,
)


def test_remove_delivery_method_from_checkout_with_cc(
    checkout_with_delivery_method_for_cc,
):
    # given
    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "save_shipping_address",
    }
    # when
    updated_fields = remove_delivery_method_from_checkout(
        checkout_with_delivery_method_for_cc
    )

    # then
    assert expected_updated_fields == set(updated_fields)
    assert checkout_with_delivery_method_for_cc.collection_point_id is None
    assert checkout_with_delivery_method_for_cc.shipping_address_id is None


def test_remove_delivery_method_from_checkout_with_shipping(
    checkout_with_item, checkout_delivery
):
    # given
    assigned_delivery = checkout_delivery(checkout_with_item)
    checkout_with_item.assigned_delivery = assigned_delivery
    checkout_with_item.shipping_method_name = assigned_delivery.name

    expected_updated_fields = {"assigned_delivery_id", "shipping_method_name"}
    # when
    updated_fields = remove_delivery_method_from_checkout(checkout_with_item)

    # then
    assert expected_updated_fields == set(updated_fields)
    assert checkout_with_item.assigned_delivery is None
    assert checkout_with_item.shipping_method_name is None


def test_remove_delivery_method_from_checkout_without_method(checkout_with_item):
    # given
    expected_updated_fields = []

    # when
    updated_fields = remove_delivery_method_from_checkout(checkout_with_item)

    # then
    assert expected_updated_fields == updated_fields


def test_assign_shipping_to_checkout_without_delivery_method(
    checkout, checkout_delivery
):
    # given
    expected_updated_fields = {
        "assigned_delivery_id",
        "shipping_method_name",
        "undiscounted_base_shipping_price_amount",
    }
    assigned_delivery = checkout_delivery(checkout=checkout)

    # when
    fields_to_update = assign_shipping_method_to_checkout(checkout, assigned_delivery)

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.assigned_delivery == assigned_delivery
    assert checkout.shipping_method_name == assigned_delivery.name


def test_assign_shipping_to_checkout_with_cc(
    checkout_with_delivery_method_for_cc, checkout_delivery
):
    # given
    checkout = checkout_with_delivery_method_for_cc
    expected_updated_fields = {
        "assigned_delivery_id",
        "shipping_method_name",
        "collection_point_id",
        "shipping_address_id",
        "undiscounted_base_shipping_price_amount",
        "save_shipping_address",
    }

    assigned_delivery = checkout_delivery(checkout=checkout)

    # when
    fields_to_update = assign_shipping_method_to_checkout(checkout, assigned_delivery)
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.assigned_delivery == assigned_delivery
    assert checkout.shipping_method_name == assigned_delivery.name
    assert checkout.collection_point_id is None
    assert checkout.shipping_address_id is None


def test_assign_shipping_to_checkout_with_different_shipping_method(
    checkout, shipping_method, shipping_method_weight_based, checkout_delivery
):
    # given
    checkout.assigned_delivery = checkout_delivery(
        checkout, shipping_method_weight_based
    )
    checkout.shipping_method_name = shipping_method_weight_based.name

    assigned_delivery = checkout_delivery(checkout=checkout)

    expected_updated_fields = {
        "assigned_delivery_id",
        "shipping_method_name",
        "undiscounted_base_shipping_price_amount",
    }

    # when
    fields_to_update = assign_shipping_method_to_checkout(checkout, assigned_delivery)

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.assigned_delivery == assigned_delivery
    assert checkout.shipping_method_name == shipping_method.name


def test_assign_shipping_to_checkout_with_the_same_shipping_method(
    checkout, checkout_delivery
):
    # given
    assigned_delivery = checkout_delivery(checkout=checkout)
    shipping_price_amount = Decimal(10)
    checkout.assigned_delivery = assigned_delivery
    checkout.shipping_method_name = assigned_delivery.name
    checkout.undiscounted_base_shipping_price_amount = shipping_price_amount

    # when
    fields_to_update = assign_shipping_method_to_checkout(checkout, assigned_delivery)

    # then
    assert not fields_to_update
    assert checkout.assigned_delivery == assigned_delivery
    assert checkout.shipping_method_name == assigned_delivery.name


def test_assign_collection_point_to_checkout_without_delivery_method(
    checkout, warehouses_for_cc
):
    # given
    collection_point = warehouses_for_cc[0]
    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "save_shipping_address",
    }

    # when
    fields_to_update = assign_collection_point_to_checkout(checkout, collection_point)

    # then
    assert expected_updated_fields == set(fields_to_update)

    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)


def test_assign_collection_point_to_checkout_with_shipping_method(
    checkout, checkout_delivery, warehouses_for_cc
):
    # given
    assigned_delivery = checkout_delivery(checkout)
    checkout.assigned_delivery = assigned_delivery
    checkout.shipping_method_name = assigned_delivery.name

    collection_point = warehouses_for_cc[0]
    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "assigned_delivery_id",
        "shipping_method_name",
        "save_shipping_address",
    }

    # when
    fields_to_update = assign_collection_point_to_checkout(checkout, collection_point)

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)
    assert checkout.assigned_delivery is None
    assert checkout.shipping_method_name is None


def test_assign_collection_point_to_checkout_with_different_cc(
    checkout, warehouses_for_cc, address_other_country
):
    # given
    previous_collection_point = warehouses_for_cc[1]
    previous_collection_point.address = address_other_country

    new_collection_point = warehouses_for_cc[0]

    checkout.collection_point = previous_collection_point
    checkout.shipping_address = previous_collection_point.address

    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "save_shipping_address",
    }

    # when
    fields_to_update = assign_collection_point_to_checkout(
        checkout, new_collection_point
    )

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.collection_point == new_collection_point
    assert checkout.shipping_address == new_collection_point.address
    assert int(checkout.shipping_address_id) != int(new_collection_point.address.id)


def test_assign_collection_point_to_checkout_with_the_same_cc(
    checkout, warehouses_for_cc, address_other_country
):
    # given
    collection_point = warehouses_for_cc[0]

    checkout.collection_point = collection_point
    checkout.shipping_address = collection_point.address.get_copy()

    # when
    fields_to_update = assign_collection_point_to_checkout(checkout, collection_point)

    # then
    assert not fields_to_update
    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)
