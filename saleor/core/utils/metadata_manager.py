from dataclasses import dataclass
from enum import Enum

from django.core.exceptions import ValidationError

from saleor.core.error_codes import MetadataErrorCode
from saleor.core.models import ModelWithMetadata
from saleor.graphql.meta.inputs import MetadataInput


class MetadataType(Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


@dataclass
class MetadataItemCollection:
    @dataclass
    class MetadataItem:
        key: str
        value: str

        def __init__(self, key: str, value: str):
            # Ensures it can't be created with invalid shape
            # TODO Probably either inject error from the outside
            # or allow to overwrite
            # or raise custom error that will be re-thrown
            if not key:
                raise ValidationError(
                    {
                        "input": ValidationError(
                            "Metadata key cannot be empty.",
                            code=MetadataErrorCode.REQUIRED.value,
                        )
                    }
                )

            self.key = key
            self.value = value

    items: list[MetadataItem]


def write_on_instance(
    metadata_collection: MetadataItemCollection | None,
    instance: ModelWithMetadata,
    target: MetadataType,
):
    # Accept None for the compatibility, but eventually should check against existence before calling this
    if metadata_collection is None:
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
) -> MetadataItemCollection | None:
    """:rtype: object"""
    if items is None:
        return None

    return MetadataItemCollection(
        [MetadataItemCollection.MetadataItem(item.key, item.value) for item in items]
    )
