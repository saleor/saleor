from ....order import OrderStatus
from ..update_mutation_manager import InstanceTracker


def test_instance_tracker(product):
    # given
    fields_to_track = ["name", "slug"]
    tracker = InstanceTracker(product, fields_to_track)

    # when
    product.name = product.name + "_updated"
    modified_field = tracker.get_modified_fields()

    # then
    assert modified_field == ["name"]


def test_instance_tracker_no_instance_on_init(product):
    # given
    fields_to_track = ["name", "slug"]
    tracker = InstanceTracker(None, fields_to_track)

    # when
    tracker.instance = product
    modified_fields = tracker.get_modified_fields()

    # then
    assert modified_fields == fields_to_track


def test_instance_tracker_no_instance_on_init_and_on_get_modified_fields():
    # given
    fields_to_track = ["name", "slug"]
    tracker = InstanceTracker(None, fields_to_track)

    # when
    modified_fields = tracker.get_modified_fields()

    # then
    assert modified_fields == []


def test_instance_tracker_remove_instance(product):
    # given
    fields_to_track = ["name", "slug"]
    tracker = InstanceTracker(product, fields_to_track)

    # when
    tracker.instance = None
    modified_fields = tracker.get_modified_fields()

    # then
    assert modified_fields == fields_to_track


def test_instance_tracker_foreign_relation(order_with_lines):
    # given
    order = order_with_lines
    fields_to_track = ["status", "shipping_address", "billing_address"]
    foreign_fields_to_track = ["last_name", "first_name"]
    tracker = InstanceTracker(
        order,
        fields_to_track,
        foreign_fields_to_track={"shipping_address": foreign_fields_to_track},
    )

    order.status = OrderStatus.FULFILLED
    shipping_address = order.shipping_address
    shipping_address.last_name = "new_last_name"

    # when
    modified_fields = tracker.get_modified_fields()
    foreign_modified_fields = tracker.get_foreign_modified_fields()

    # then
    assert modified_fields == ["status", "shipping_address"]
    assert foreign_modified_fields["shipping_address"] == ["last_name"]


def test_instance_tracker_foreign_relation_new_instance(order_with_lines):
    # given
    order = order_with_lines
    order.shipping_address = None

    fields_to_track = ["status", "shipping_address", "billing_address"]
    foreign_fields_to_track = ["last_name", "first_name"]
    tracker = InstanceTracker(
        order,
        fields_to_track,
        foreign_fields_to_track={"shipping_address": foreign_fields_to_track},
    )

    order.status = OrderStatus.FULFILLED
    order.shipping_address = order.billing_address

    # when
    modified_fields = tracker.get_modified_fields()
    foreign_modified_fields = tracker.get_foreign_modified_fields()

    # then
    assert modified_fields == ["status", "shipping_address"]
    assert foreign_modified_fields["shipping_address"] == foreign_fields_to_track
