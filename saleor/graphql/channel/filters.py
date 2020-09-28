from typing import Dict

from graphql.error import GraphQLError


def get_channel_slug_from_filter_data(filter_data: Dict):
    channel_slug = filter_data.get("channel", None)
    if not channel_slug:
        raise GraphQLError(
            "You must provide a `channel` as one of filter to properly filter data."
        )
    return channel_slug
