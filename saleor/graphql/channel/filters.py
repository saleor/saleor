from typing import Dict

from graphql.error import GraphQLError

LACK_OF_CHANNEL_IN_FILTERING_MSG = (
    "You must provide a `channel` filter parameter to properly filter data."
)


def get_channel_slug_from_filter_data(filter_data: Dict):
    channel_slug = filter_data.get("channel", None)
    if not channel_slug:
        raise GraphQLError(LACK_OF_CHANNEL_IN_FILTERING_MSG)
    return channel_slug
