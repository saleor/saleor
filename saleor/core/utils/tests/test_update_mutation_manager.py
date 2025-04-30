import pytest

from ..update_mutation_manager import InstanceTracker, InstanceTrackerError


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
    modified_field = tracker.get_modified_fields()

    # then
    assert modified_field == fields_to_track


def test_instance_tracker_get_modified_fields_no_instance():
    # given
    fields_to_track = ["field", "field2"]
    tracker = InstanceTracker(None, fields_to_track)

    # when & then
    with pytest.raises(InstanceTrackerError):
        tracker.get_modified_fields()
