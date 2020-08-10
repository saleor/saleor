from typing import DefaultDict, Iterable, List

from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ...channel.exceptions import ChannelNotDefined, NoDefaultChannel
from ...channel.models import Channel
from ...channel.utils import get_default_channel
from ..core.utils import get_duplicated_values, get_duplicates_ids

ErrorType = DefaultDict[str, List[ValidationError]]


def get_default_channel_or_graphql_error() -> Channel:
    """Return a default channel or a GraphQL error.

    Utility to get the default channel in GraphQL query resolvers.
    """
    try:
        channel = get_default_channel()
    except (ChannelNotDefined, NoDefaultChannel) as e:
        raise GraphQLError(str(e))
    else:
        return channel


def validate_duplicated_channel_ids(
    add_channels_ids: Iterable[str],
    remove_channels_ids: Iterable[str],
    errors: ErrorType,
    error_code,
):
    duplicated_ids = get_duplicates_ids(add_channels_ids, remove_channels_ids)
    if duplicated_ids:
        error_msg = (
            "The same object cannot be in both lists " "for adding and removing items."
        )
        errors["input"].append(
            ValidationError(
                error_msg, code=error_code, params={"channels": list(duplicated_ids)},
            )
        )


def validate_duplicated_channel_values(
    channels_ids: Iterable[str], field_name: str, errors: ErrorType, error_code
):
    duplicates = get_duplicated_values(channels_ids)
    if duplicates:
        errors[field_name].append(
            ValidationError(
                "Duplicated channel ID.",
                code=error_code,
                params={"channels": duplicates},
            )
        )
