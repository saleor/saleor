from dataclasses import dataclass
from enum import Enum
from typing import Any

from ...graphql.meta.inputs import MetadataInput
from ..models import ModelWithMetadata


class MetadataType(Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class MetadataEmptyKeyError(Exception):
    pass


@dataclass
class MetadataItem:
    key: str
    value: str

    def __init__(self, key: str, value: str):
        if not key.strip():
            raise MetadataEmptyKeyError()

        self.key = key
        self.value = value


@dataclass
class MetadataItemCollection:
    items: list[MetadataItem]


def store_on_instance(
    metadata_collection: MetadataItemCollection,
    instance: ModelWithMetadata,
    target: MetadataType,
):
    if not metadata_collection.items:
        return

    match target:
        case MetadataType.PUBLIC:
            instance.store_value_in_metadata(
                {item.key: item.value for item in metadata_collection.items}
            )
        case MetadataType.PRIVATE:
            instance.store_value_in_private_metadata(
                {item.key: item.value for item in metadata_collection.items}
            )
        case _:
            raise ValueError(
                "Unknown argument, provide MetadataType.PRIVATE or MetadataType.PUBLIC"
            )


def create_from_graphql_input(
    items: list[MetadataInput] | None,
) -> MetadataItemCollection:
    """Create MetadataItemCollection from graphQL input.

    Use with care.

    This method is eventually raising MetadataEmptyKeyError, so if it's used directly
    in mutation, error will not be handled.

    Use BaseMutation.create_metadata_from_graphql_input to include error translation.
    """
    if not items:
        return MetadataItemCollection([])

    return MetadataItemCollection(
        [MetadataItem(item.key, item.value) for item in items]
    )


def metadata_is_valid(metadata: Any) -> bool:
    if not isinstance(metadata, dict):
        return False
    for key, value in metadata.items():
        if not isinstance(key, str) or not isinstance(value, str) or not key.strip():
            return False
    return True
