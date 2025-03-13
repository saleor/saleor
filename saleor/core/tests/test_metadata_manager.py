from sympy.testing.pytest import raises

from saleor.core.models import ModelWithMetadata
from saleor.core.utils.metadata_manager import (
    MetadataEmptyKeyError,
    MetadataItemCollection,
    MetadataType,
    create_from_graphql_input,
    store_on_instance,
)
from saleor.graphql.meta.inputs import MetadataInput

valid_metadata_item = MetadataInput()

# Graphene doesn't accept params in constructor
valid_metadata_item.key = "key"
valid_metadata_item.value = "value"

invalid_metadata_item = MetadataInput()

# Key can't be empty
invalid_metadata_item.key = ""
invalid_metadata_item.value = "value"

valid_list = [valid_metadata_item]
invalid_list = [invalid_metadata_item]
invalid_list_with_one_valid = [
    valid_metadata_item,
    invalid_metadata_item,
]


def test_create_collection_empty():
    collection = MetadataItemCollection([])

    assert collection.items == []


def test_create_collection_valid():
    collection = MetadataItemCollection(
        [MetadataItemCollection.MetadataItem(valid_list[0].key, valid_list[0].value)]
    )

    assert collection.items[0].key == valid_list[0].key
    assert collection.items[0].value == valid_list[0].value


def test_create_collection():
    collection = create_from_graphql_input(valid_list)

    assert collection.items[0].key == valid_list[0].key
    assert collection.items[0].value == valid_list[0].value


def test_write_on_model_public():
    class TestInstance(ModelWithMetadata):
        pass

    instance = TestInstance()

    collection = create_from_graphql_input(valid_list)

    store_on_instance(collection, instance, MetadataType.PUBLIC)

    assert instance.metadata.get(valid_list[0].key) == valid_list[0].value


def test_write_on_model_private():
    class TestInstance(ModelWithMetadata):
        pass

    instance = TestInstance()

    collection = create_from_graphql_input(valid_list)

    store_on_instance(collection, instance, MetadataType.PRIVATE)

    assert instance.private_metadata.get(valid_list[0].key) == valid_list[0].value


def test_throw_on_empty_key():
    with raises(MetadataEmptyKeyError):
        create_from_graphql_input(invalid_list)


def test_throw_on_empty_key_with_whitespaces():
    item = MetadataInput()
    item.key = "  "
    item.value = "ok"

    with raises(MetadataEmptyKeyError):
        create_from_graphql_input([item])


def test_store_multiple_keys():
    overwritten_value = "value1-overwrite"

    metadata_list = [
        MetadataItemCollection.MetadataItem(key="key1", value="value1"),
        MetadataItemCollection.MetadataItem(key="key2", value="value2"),
        # Test key with the same value to be overwritten
        MetadataItemCollection.MetadataItem(key="key1", value=overwritten_value),
    ]

    class TestInstance(ModelWithMetadata):
        pass

    instance = TestInstance()

    collection = MetadataItemCollection(items=metadata_list)

    store_on_instance(collection, instance, MetadataType.PUBLIC)

    assert instance.metadata.get(metadata_list[1].key) == metadata_list[1].value

    # Check if the key with the same value was overwritten
    assert instance.metadata.get(metadata_list[0].key) == overwritten_value
