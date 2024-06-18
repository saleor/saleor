import datetime
from collections import defaultdict
from collections.abc import Iterable

import pytz
from django.core.exceptions import ValidationError

from ....channel import models
from ....core.utils.date_time import convert_to_utc_date_time
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.utils import get_duplicated_values, get_duplicates_items
from ..types import Channel

ErrorType = defaultdict[str, list[ValidationError]]


class BaseChannelListingMutation(BaseMutation):
    """Base channel listing mutation with basic channel validation."""

    class Meta:
        abstract = True

    @classmethod
    def validate_duplicated_channel_ids(
        cls,
        add_channels_ids: Iterable[str],
        remove_channels_ids: Iterable[str],
        errors: ErrorType,
        error_code,
    ):
        duplicated_ids = get_duplicates_items(add_channels_ids, remove_channels_ids)
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
    def clean_channels(
        cls,
        info: ResolveInfo,
        input,
        errors: ErrorType,
        error_code,
        input_source="add_channels",
    ) -> dict:
        add_channels = input.get(input_source, [])
        add_channels_ids = [channel["channel_id"] for channel in add_channels]
        remove_channels_ids = input.get("remove_channels", [])
        cls.validate_duplicated_channel_ids(
            add_channels_ids, remove_channels_ids, errors, error_code
        )
        cls.validate_duplicated_channel_values(
            add_channels_ids, input_source, errors, error_code
        )
        cls.validate_duplicated_channel_values(
            remove_channels_ids, "remove_channels", errors, error_code
        )
        if errors:
            return {}
        channels_to_add: list[models.Channel] = []
        if add_channels_ids:
            channels_to_add = cls.get_nodes_or_error(
                add_channels_ids, "channel_id", Channel
            )
        if remove_channels_ids:
            remove_channels_pks = cls.get_global_ids_or_error(
                remove_channels_ids, Channel, field="remove_channels"
            )
        else:
            remove_channels_pks = []

        cleaned_input = {input_source: [], "remove_channels": remove_channels_pks}

        for channel_listing, channel in zip(add_channels, channels_to_add):
            channel_listing["channel"] = channel
            cleaned_input[input_source].append(channel_listing)
        return cleaned_input

    @classmethod
    def clean_publication_date(
        cls, errors, error_code_enum, cleaned_input, input_source="add_channels"
    ):
        invalid_channels = []
        for add_channel in cleaned_input.get(input_source, []):
            # should update errors dict
            if "publication_date" in add_channel and "published_at" in add_channel:
                invalid_channels.append(add_channel["channel_id"])
                continue
            publication_date = add_channel.get("publication_date")
            publication_date = (
                convert_to_utc_date_time(publication_date)
                if publication_date
                else add_channel.get("published_at")
            )
            is_published = add_channel.get("is_published")
            if is_published and not publication_date:
                add_channel["published_at"] = datetime.datetime.now(pytz.UTC)
            elif "publication_date" in add_channel or "published_at" in add_channel:
                add_channel["published_at"] = publication_date
        if invalid_channels:
            error_msg = (
                "Only one of argument: publicationDate or publishedAt "
                "must be specified."
            )
            errors["publication_date"].append(
                ValidationError(
                    error_msg,
                    code=error_code_enum.INVALID.value,
                    params={"channels": invalid_channels},
                )
            )
