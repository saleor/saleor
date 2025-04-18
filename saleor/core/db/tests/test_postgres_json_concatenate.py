import pytest
from django.db.models import CharField, F, JSONField, Value

from ....checkout.models import CheckoutMetadata
from ..expressions import PostgresJsonConcatenate

TEST_KEY = "test-key"
TEST_VALUE = "test_value"
TEST_DICT = {TEST_KEY: TEST_VALUE}


@pytest.fixture
def checkout_metadata_qs(checkout):
    return CheckoutMetadata.objects.filter(checkout=checkout)


def test_save_concat_add_new_key(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])
    new_dict = {"new-key": "new"}

    # when
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(new_dict, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == {**TEST_DICT, **new_dict}


def test_save_concat_update_key(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])
    new_dict = {TEST_KEY: "new"}

    # when
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(new_dict, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == {**TEST_DICT, **new_dict}


def test_save_concat_new_dict(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.metadata = {}
    checkout.metadata_storage.save()
    new_dict = {"new-key": "new"}

    # when
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(new_dict, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == new_dict


def test_save_concat_with_none_value(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.metadata = TEST_DICT
    checkout.metadata_storage.save()
    new_dict = None

    # when
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(new_dict, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == TEST_DICT


def test_save_concat_add_multiple_new_key(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])
    new_dict = {"new-key": "new", "new-key2": "new2", "new-key3": "new3"}

    # when
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(new_dict, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == {**TEST_DICT, **new_dict}


def test_raise_error_when_no_JSONField_output(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])
    new_dict = {"new-key": "new"}

    # when & then
    with pytest.raises(TypeError) as e:
        checkout_metadata_qs.update(
            metadata=PostgresJsonConcatenate(
                F("metadata"), Value(new_dict, output_field=CharField())
            )
        )
    assert "is not a JSONField" in e.value.args[0]


def test_raise_error_when_no_expression(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])
    new_dict = {"new-key": "new"}

    # when & then
    with pytest.raises(TypeError) as e:
        checkout_metadata_qs.update(
            metadata=PostgresJsonConcatenate(F("metadata"), new_dict)
        )
    assert "is not an Expression" in e.value.args[0]


def test_multiple_updates(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])
    first_dict = {"first-key": 1}
    second_dict = {"second-key": 2}

    # when
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(first_dict, output_field=JSONField())
        )
    )

    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(second_dict, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == {**TEST_DICT, **first_dict, **second_dict}


def test_saving_same_value_no_affect(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])

    # when
    current_json = checkout_metadata_qs.get().metadata
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(current_json, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == current_json


def test_updating_existing_key_to_none(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])
    new_dict = {TEST_KEY: None}

    # when
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(new_dict, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == {TEST_KEY: None}


def test_updating_with_empty_dict(checkout, checkout_metadata_qs):
    # given
    checkout.metadata_storage.store_value_in_metadata(TEST_DICT)
    checkout.metadata_storage.save(update_fields=["metadata"])
    new_dict = {}

    # when
    checkout_metadata_qs.update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(new_dict, output_field=JSONField())
        )
    )

    # then
    metadata = checkout.metadata_storage
    metadata.refresh_from_db()
    assert metadata.metadata == TEST_DICT
