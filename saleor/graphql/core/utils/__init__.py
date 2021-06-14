import binascii
import os
import secrets
from typing import TYPE_CHECKING, Type, Union

import graphene
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from graphene import ObjectType
from graphql.error import GraphQLError
from PIL import Image

from ....core.utils import generate_unique_slug

if TYPE_CHECKING:
    # flake8: noqa
    from django.db.models import Model


Image.init()


def clean_seo_fields(data):
    """Extract and assign seo fields to given dictionary."""
    seo_fields = data.pop("seo", None)
    if seo_fields:
        data["seo_title"] = seo_fields.get("title")
        data["seo_description"] = seo_fields.get("description")


def snake_to_camel_case(name):
    """Convert snake_case variable name to camelCase."""
    if isinstance(name, str):
        split_name = name.split("_")
        return split_name[0] + "".join(map(str.capitalize, split_name[1:]))
    return name


def str_to_enum(name):
    """Create an enum value from a string."""
    return name.replace(" ", "_").replace("-", "_").upper()


def validate_image_file(file, field_name, error_class):
    """Validate if the file is an image."""
    if not file:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "File is required.", code=error_class.REQUIRED
                )
            }
        )
    if not file.content_type.startswith("image/"):
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Invalid file type.", code=error_class.INVALID
                )
            }
        )
    _validate_image_format(file, field_name, error_class)


def _validate_image_format(file, field_name, error_class):
    """Validate image file format."""
    allowed_extensions = [ext.lower() for ext in Image.EXTENSION]
    _file_name, format = os.path.splitext(file._name)
    if not format:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Lack of file extension.", code=error_class.INVALID
                )
            }
        )
    elif format not in allowed_extensions:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Invalid file extension. Image file required.",
                    code=error_class.INVALID,
                )
            }
        )


def validate_slug_and_generate_if_needed(
    instance: Type["Model"],
    slugable_field: str,
    cleaned_input: dict,
    slug_field_name: str = "slug",
) -> dict:
    """Validate slug from input and generate in create mutation if is not given."""

    # update mutation - just check if slug value is not empty
    # _state.adding is True only when it's new not saved instance.
    if not instance._state.adding:  # type: ignore
        validate_slug_value(cleaned_input)
        return cleaned_input

    # create mutation - generate slug if slug value is empty
    slug = cleaned_input.get(slug_field_name)
    if not slug and slugable_field in cleaned_input:
        slug = generate_unique_slug(instance, cleaned_input[slugable_field])
        cleaned_input[slug_field_name] = slug
    return cleaned_input


def validate_slug_value(cleaned_input, slug_field_name: str = "slug"):
    if slug_field_name in cleaned_input:
        slug = cleaned_input[slug_field_name]
        if not slug:
            raise ValidationError(
                f"{slug_field_name.capitalize()} value cannot be blank."
            )


def get_duplicates_ids(first_list, second_list):
    """Return items that appear on both provided lists."""
    if first_list and second_list:
        return set(first_list) & set(second_list)
    return []


def get_duplicated_values(values):
    """Return set of duplicated values."""
    return {value for value in values if values.count(value) > 1}


def validate_required_string_field(cleaned_input, field_name: str):
    """Strip and validate field value."""
    field_value = cleaned_input.get(field_name)
    field_value = field_value.strip() if field_value else ""
    if field_value:
        cleaned_input[field_name] = field_value
    else:
        raise ValidationError(f"{field_name.capitalize()} is required.")
    return cleaned_input


def from_global_id_or_error(
    id: str, only_type: Union[ObjectType, str] = None, raise_error: bool = False
):
    """Resolve database ID from global ID or raise ValidationError.

    Optionally validate the object type, if `only_type` is provided,
    raise GraphQLError when `raise_error` is set to True.
    """
    try:
        _type, _id = graphene.Node.from_global_id(id)
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise GraphQLError(f"Couldn't resolve id: {id}.")

    if only_type and str(_type) != str(only_type):
        if not raise_error:
            return _type, None
        raise GraphQLError(f"Must receive a {only_type} id.")
    return _type, _id


def add_hash_to_file_name(file):
    """Add unique text fragment to the file name to prevent file overriding."""
    file_name, format = os.path.splitext(file._name)
    hash = secrets.token_hex(nbytes=4)
    new_name = f"{file_name}_{hash}{format}"
    file._name = new_name
