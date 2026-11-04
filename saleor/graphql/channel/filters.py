from functools import cached_property

from django.db.models import QuerySet

from ...channel.models import Channel


def get_channel_slug_from_filter_data(filter_data: dict):
    channel = filter_data.get("channel")
    return str(channel) if channel else None


def get_currency_from_filter_data(filter_data: dict):
    currency = filter_data.get("currency")
    return str(currency) if currency else None


def resolve_channel_id_from_filter_data(
    filter_data: dict, database_connection_name: str
) -> int | None:
    """Return the id of the channel referenced by the filter data, if it exists."""
    channel_slug = get_channel_slug_from_filter_data(filter_data)
    if not channel_slug:
        return None
    return (
        Channel.objects.using(database_connection_name)
        .filter(slug=channel_slug)
        .values_list("id", flat=True)
        .first()
    )


class ChannelIdFilterSetMixin:
    """Resolve the channel from the filter data once per filterset instance.

    Channel-dependent filters must compare `channel_id` against a literal value
    instead of a `channel_channel.slug` subquery. The subquery hides the channel from
    the Postgres planner, which then misestimates the listing rows by two orders of
    magnitude and picks a plan that reads the whole catalogue on every page.
    """

    data: dict
    queryset: QuerySet

    @cached_property
    def channel_id(self) -> int | None:
        return resolve_channel_id_from_filter_data(self.data, self.queryset.db)
