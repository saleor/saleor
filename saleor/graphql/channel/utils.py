from typing import TYPE_CHECKING, DefaultDict, Dict, Iterable, List

from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ...channel.exceptions import ChannelNotDefined, NoDefaultChannel
from ...channel.models import Channel
from ...channel.utils import get_default_channel
from ..core.utils import get_duplicated_values, get_duplicates_ids
from ..utils import resolve_global_ids_to_primary_keys

ErrorType = DefaultDict[str, List[ValidationError]]

if TYPE_CHECKING:
    from ...channel.models import Channel as ChannelModel


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


class CleanChannelMixin:
    @classmethod
    def get_nodes_or_error(cls, ids, field, only_type=None, qs=None):
        raise NotImplementedError

    @classmethod
    def validate_duplicated_channel_ids(
        cls,
        add_channels_ids: Iterable[str],
        remove_channels_ids: Iterable[str],
        errors: ErrorType,
        error_code,
    ):
        duplicated_ids = get_duplicates_ids(add_channels_ids, remove_channels_ids)
        if duplicated_ids:
            error_msg = (
                "The same object cannot be in both lists "
                "for adding and removing items."
            )
            errors["input"].append(
                ValidationError(
                    error_msg,
                    code=error_code,
                    params={"channels": list(duplicated_ids)},
                )
            )

    @classmethod
    def validate_duplicated_channel_values(
        cls, channels_ids: Iterable[str], field_name: str, errors: ErrorType, error_code
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

    @classmethod
    def clean_channels(cls, info, input, errors: ErrorType, error_code) -> Dict:
        add_channels = input.get("add_channels", [])
        add_channels_ids = [channel["channel_id"] for channel in add_channels]
        remove_channels_ids = input.get("remove_channels", [])
        cls.validate_duplicated_channel_ids(
            add_channels_ids, remove_channels_ids, errors, error_code
        )
        cls.validate_duplicated_channel_values(
            add_channels_ids, "add_channels", errors, error_code
        )
        cls.validate_duplicated_channel_values(
            remove_channels_ids, "remove_channels", errors, error_code
        )

        if errors:
            return {}
        channels_to_add: List["ChannelModel"] = []
        if add_channels_ids:
            channels_to_add = cls.get_nodes_or_error(
                add_channels_ids, "channel_id", Channel
            )
        _, remove_channels_pks = resolve_global_ids_to_primary_keys(
            remove_channels_ids, Channel
        )

        cleaned_input = {"add_channels": [], "remove_channels": remove_channels_pks}

        for channel_listing, channel in zip(add_channels, channels_to_add):
            channel_listing["channel"] = channel
            cleaned_input["add_channels"].append(channel_listing)

        return cleaned_input
