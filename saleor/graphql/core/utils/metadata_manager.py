from django.core.exceptions import ValidationError

from saleor.core.error_codes import MetadataErrorCode
from saleor.core.models import ModelWithMetadata

# Keeps unified logic around validation and storing metadata and private metadata
# on ModelWithMetadata


def metadata_contains_empty_key(metadata_list: list[dict]) -> bool:
    return not all(data["key"].strip() for data in metadata_list)


def validate_metadata_keys_and_throw(metadata_list: list[dict]):
    if metadata_contains_empty_key(metadata_list):
        raise ValidationError(
            {
                "input": ValidationError(
                    "Metadata key cannot be empty.",
                    code=MetadataErrorCode.REQUIRED.value,
                )
            }
        )


def update_metadata_on_instance(
    instance: ModelWithMetadata,
    metadata: list[dict] | None,
    private_metadata: list[dict] | None,
):
    if metadata is not None:
        instance.store_value_in_metadata(
            {data["key"]: data["value"] for data in metadata}
        )

    if private_metadata is not None:
        instance.store_value_in_private_metadata(
            {data["key"]: data["value"] for data in private_metadata}
        )
