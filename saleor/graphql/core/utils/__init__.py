import binascii
import mimetypes
import os
import secrets
from enum import Enum
from typing import TYPE_CHECKING, Type, Union
from uuid import UUID

import graphene
import requests
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from graphene import ObjectType
from graphql.error import GraphQLError
from PIL import Image

from ....core.utils import generate_unique_slug
from ....plugins.webhook.utils import APP_ID_PREFIX

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


def is_image_mimetype(mimetype: str) -> bool:
    """Check if mimetype is image."""
    if mimetype is None:
        return False
    return mimetype.startswith("image/")


def is_image_url(url: str) -> bool:
    """Check if file URL seems to be an image."""
    if url.endswith(".webp"):
        # webp is not recognized by mimetypes as image
        # https://bugs.python.org/issue38902
        return True
    filetype = mimetypes.guess_type(url)[0]
    return filetype is not None and is_image_mimetype(filetype)


def validate_image_url(url: str, field_name: str, error_code: str) -> None:
    """Check if remote file has content type of image.

    Instead of the whole file, only the headers are fetched.
    """
    head = requests.head(url)
    header = head.headers
    content_type = header.get("content-type")
    if content_type is None or not is_image_mimetype(content_type):
        raise ValidationError(
            {field_name: ValidationError("Invalid file type.", code=error_code)}
        )


def get_filename_from_url(url: str) -> str:
    """Prepare unique filename for file from URL to avoid overwritting."""
    file_name = os.path.basename(url)
    name, format = os.path.splitext(file_name)
    hash = secrets.token_hex(nbytes=4)
    return f"{name}_{hash}{format}"


def validate_image_file(file, field_name, error_class) -> None:
    """Validate if the file is an image."""
    if not file:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "File is required.", code=error_class.REQUIRED
                )
            }
        )
    if not is_image_mimetype(file.content_type):
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


def get_duplicates_items(first_list, second_list):
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


def validate_if_int_or_uuid(id):
    result = True
    try:
        int(id)
    except ValueError:
        try:
            UUID(id)
        except (AttributeError, ValueError):
            result = False
    return result


def from_global_id_or_error(
    global_id: str, only_type: Union[ObjectType, str] = None, raise_error: bool = False
):
    """Resolve global ID or raise GraphQLError.

    Validates if given ID is a proper ID handled by Saleor.
    Valid IDs formats, base64 encoded:
    'app:<int>:<str>' : External app ID with 'app' prefix
    '<type>:<int>' : Internal ID containing object type and ID as integer
    '<type>:<UUID>' : Internal ID containing object type and UUID
    Optionally validate the object type, if `only_type` is provided,
    raise GraphQLError when `raise_error` is set to True.
    """
    try:
        type_, id_ = graphene.Node.from_global_id(global_id)
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise GraphQLError(f"Couldn't resolve id: {global_id}.")
    if type_ == APP_ID_PREFIX:
        id_ = global_id
    else:
        if not validate_if_int_or_uuid(id_):
            raise GraphQLError(f"Error occurred during ID - {global_id} validation.")

    if only_type and str(type_) != str(only_type):
        if not raise_error:
            return type_, None
        raise GraphQLError(f"Must receive a {only_type} id.")
    return type_, id_


def from_global_id_or_none(
    global_id, only_type: Union[ObjectType, str] = None, raise_error: bool = False
):
    if not global_id:
        return None

    return from_global_id_or_error(global_id, only_type, raise_error)[1]


def to_global_id_or_none(instance):
    class_name = instance.__class__.__name__
    if instance.pk is None:
        return None
    return graphene.Node.to_global_id(class_name, instance.pk)


def add_hash_to_file_name(file):
    """Add unique text fragment to the file name to prevent file overriding."""
    file_name, format = os.path.splitext(file._name)
    hash = secrets.token_hex(nbytes=4)
    new_name = f"{file_name}_{hash}{format}"
    file._name = new_name
