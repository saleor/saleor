import binascii
import os
import secrets
from dataclasses import dataclass
from typing import Literal, NoReturn, overload

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from graphene import ObjectType
from graphql.error import GraphQLError

from ....plugins.const import APP_ID_PREFIX
from ....thumbnail import FILE_NAME_MAX_LENGTH
from ....webhook.event_types import WebhookEventAsyncType
from ..validators import validate_if_int_or_uuid


def snake_to_camel_case(name):
    """Convert snake_case variable name to camelCase."""
    if isinstance(name, str):
        split_name = name.split("_")
        return split_name[0] + "".join(map(str.capitalize, split_name[1:]))
    return name


def str_to_enum(name):
    """Create an enum value from a string."""
    return name.replace(" ", "_").replace("-", "_").upper()


def get_duplicates_items(first_list, second_list):
    """Return items that appear on both provided lists."""
    if first_list and second_list:
        return set(first_list) & set(second_list)
    return []


def get_duplicated_values(values):
    """Return set of duplicated values."""
    if values:
        return {value for value in values if values.count(value) > 1}
    return {}


@overload
def from_global_id_or_error(
    global_id: str,
    only_type: ObjectType | str | None = None,
    raise_error: Literal[True] = True,
) -> tuple[str, str]: ...


@overload
def from_global_id_or_error(
    global_id: str,
    only_type: type[ObjectType] | str | None = None,
    raise_error: bool = False,
) -> tuple[str, str] | tuple[str, None]: ...


def from_global_id_or_error(
    global_id: str,
    only_type: type[ObjectType] | str | None = None,
    raise_error: bool = False,
):
    """Resolve global ID or raise GraphQLError.

    Validates if given ID is a proper ID handled by Saleor.
    Valid IDs formats, base64 encoded:
    'app:<int>:<str>' : External app ID with 'app' prefix
    '<type>:<int>' : Internal ID containing object type and ID as integer
    '<type>:<UUID>' : Internal ID containing object type and UUID
    Optionally validate the object type, if `only_type` is provided,
    raise GraphQLError when `raise_error` is set to True.

    Returns tuple: (type, id).
    """
    try:
        type_, id_ = graphene.Node.from_global_id(global_id)
        if type_ == APP_ID_PREFIX:
            id_ = global_id
        else:
            validate_if_int_or_uuid(id_)
    except (binascii.Error, UnicodeDecodeError, ValueError, ValidationError) as e:
        if only_type:
            raise GraphQLError(
                f"Invalid ID: {global_id}. Expected: {only_type}."
            ) from e
        raise GraphQLError(f"Invalid ID: {global_id}.") from e

    if only_type and str(type_) != str(only_type):
        if not raise_error:
            return type_, None
        raise GraphQLError(
            f"Invalid ID: {global_id}. Expected: {only_type}, received: {type_}."
        )
    return type_, id_


def from_global_id_or_none(
    global_id, only_type: ObjectType | str | None = None, raise_error: bool = False
):
    if not global_id:
        return None

    return from_global_id_or_error(global_id, only_type, raise_error)[1]


def to_global_id_or_none(instance):
    class_name = instance.__class__.__name__
    if instance is None or instance.pk is None:
        return None
    return graphene.Node.to_global_id(class_name, instance.pk)


def add_hash_to_file_name(file):
    """Add unique text fragment to the file name to prevent file overriding."""
    file_name, format = os.path.splitext(file._name)
    file_name = file_name[:FILE_NAME_MAX_LENGTH]
    hash = secrets.token_hex(nbytes=4)
    new_name = f"{file_name}_{hash}{format}"
    file._name = new_name


def raise_validation_error(field=None, message=None, code=None) -> NoReturn:
    raise ValidationError({field: ValidationError(message, code=code)})


def ext_ref_to_global_id_or_error(
    model,
    external_reference,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Convert external reference to global id."""
    internal_id = (
        model.objects.using(database_connection_name)
        .filter(external_reference=external_reference)
        .values_list("id", flat=True)
        .first()
    )
    if internal_id:
        return graphene.Node.to_global_id(model.__name__, internal_id)
    raise_validation_error(
        field="externalReference",
        message=f"Couldn't resolve to a node: {external_reference}",
        code="not_found",
    )


@dataclass
class WebhookEventInfo:
    type: str
    description: str | None = None


CHECKOUT_CALCULATE_TAXES_MESSAGE = (
    "Optionally triggered when checkout prices are expired."
)


def message_webhook_events(webhook_events: list[WebhookEventInfo]) -> str:
    description = "\n\nTriggers the following webhook events:"
    for event in webhook_events:
        webhook_type = "async" if event.type in WebhookEventAsyncType.ALL else "sync"
        description += f"\n- {event.type.upper()} ({webhook_type})"
        if event.description:
            description += f": {event.description}"
    return description
