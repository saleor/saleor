import pytest

from ...account.models import Address
from ...graphql.meta.inputs import MetadataInput
from ..models import ModelWithMetadata
from ..utils.metadata_manager import (
    MetadataEmptyKeyError,
    MetadataItem,
    MetadataItemCollection,
    MetadataType,
    create_from_graphql_input,
    store_on_instance,
)


@pytest.fixture
def valid_metadata_input() -> MetadataInput:
    valid_metadata_item = MetadataInput()

    # Graphene doesn't accept params in constructor
    valid_metadata_item.key = "key"
    valid_metadata_item.value = "value"

    return valid_metadata_item


@pytest.fixture
def invalid_metadata_input() -> MetadataInput:
    invalid_metadata_item = MetadataInput()

    # Key can't be empty
    invalid_metadata_item.key = ""
    invalid_metadata_item.value = "value"

    return invalid_metadata_item


@pytest.fixture
def valid_metadata_input_list(valid_metadata_input) -> list[MetadataInput]:
    return [valid_metadata_input]


@pytest.fixture
def invalid_metadata_input_list(invalid_metadata_input) -> list[MetadataInput]:
    return [invalid_metadata_input]


@pytest.fixture
def invalid_metadata_input_list_with_one_valid(
    valid_metadata_input, invalid_metadata_input
) -> list[MetadataInput]:
    return [valid_metadata_input, invalid_metadata_input]


def test_create_collection_empty():
    collection = MetadataItemCollection([])

    assert collection.items == []


def test_create_collection_valid(valid_metadata_input_list):
    collection = MetadataItemCollection(
        [
            MetadataItem(
                valid_metadata_input_list[0].key, valid_metadata_input_list[0].value
            )
        ]
    )

    assert collection.items[0].key == valid_metadata_input_list[0].key
    assert collection.items[0].value == valid_metadata_input_list[0].value


def test_create_collection(valid_metadata_input_list):
    collection = create_from_graphql_input(valid_metadata_input_list)

    assert collection.items[0].key == valid_metadata_input_list[0].key
    assert collection.items[0].value == valid_metadata_input_list[0].value


def test_testing_model_is_inheriting_metadata():
    # Tests below requires model that inherits from ModelWithMetadata
    # This test checks if tested Model actually inherits from it.
    # If the inheritance chain is broken, this tests will fail
    # In such case other tests must be updated to use other model

    assert issubclass(Address, ModelWithMetadata)


def test_write_on_model_public(valid_metadata_input_list):
    instance = Address()

    collection = create_from_graphql_input(valid_metadata_input_list)

    store_on_instance(collection, instance, MetadataType.PUBLIC)

    assert (
        instance.metadata.get(valid_metadata_input_list[0].key)
        == valid_metadata_input_list[0].value
    )


def test_write_on_model_private(valid_metadata_input_list):
    instance = Address()

    collection = create_from_graphql_input(valid_metadata_input_list)

    store_on_instance(collection, instance, MetadataType.PRIVATE)

    assert (
        instance.private_metadata.get(valid_metadata_input_list[0].key)
        == valid_metadata_input_list[0].value
    )


def test_throw_on_empty_key(invalid_metadata_input_list):
    with pytest.raises(MetadataEmptyKeyError):
        create_from_graphql_input(invalid_metadata_input_list)


def test_throw_on_empty_key_with_whitespaces():
    item = MetadataInput()
    item.key = "  "
    item.value = "ok"

    with pytest.raises(MetadataEmptyKeyError):
        create_from_graphql_input([item])


def test_store_multiple_keys():
    overwritten_value = "value1-overwrite"

    metadata_list = [
        MetadataItem(key="key1", value="value1"),
        MetadataItem(key="key2", value="value2"),
        # Test key with the same value to be overwritten
        MetadataItem(key="key1", value=overwritten_value),
    ]

    instance = Address()

    collection = MetadataItemCollection(items=metadata_list)

    store_on_instance(collection, instance, MetadataType.PUBLIC)

    assert instance.metadata.get(metadata_list[1].key) == metadata_list[1].value

    # Check if the key with the same value was overwritten
    assert instance.metadata.get(metadata_list[0].key) == overwritten_value


def test_throws_for_invalid_metadata_target():
    with pytest.raises(
        ValueError,
        match="Unknown argument, provide MetadataType.PRIVATE or MetadataType.PUBLIC",
    ):
        store_on_instance(
            MetadataItemCollection(items=[MetadataItem(key="a", value="b")]),
            Address(),
            "invalid_target",
        )
