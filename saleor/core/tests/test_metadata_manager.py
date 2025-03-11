from django.core.exceptions import ValidationError
from sympy.testing.pytest import raises

from saleor.core.models import ModelWithMetadata
from saleor.core.utils.metadata_manager import MetadataItemCollection, MetadataType
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


def test_create_collection():
    collection = MetadataItemCollection.create_from_graphql_input(valid_list)

    assert collection.items[0].key == valid_list[0].key
    assert collection.items[0].value == valid_list[0].value


def test_write_on_model_public():
    class TestInstance(ModelWithMetadata):
        pass

    instance = TestInstance()

    collection = MetadataItemCollection.create_from_graphql_input(valid_list)

    collection.write_on_instance(instance, MetadataType.PUBLIC)

    assert instance.metadata.get(valid_list[0].key) == valid_list[0].value


def test_write_on_model_private():
    class TestInstance(ModelWithMetadata):
        pass

    instance = TestInstance()

    collection = MetadataItemCollection.create_from_graphql_input(valid_list)

    collection.write_on_instance(instance, MetadataType.PRIVATE)

    assert instance.private_metadata.get(valid_list[0].key) == valid_list[0].value


def test_throw_on_empty_key():
    with raises(ValidationError):
        MetadataItemCollection.create_from_graphql_input(invalid_list)
