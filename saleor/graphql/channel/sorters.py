from graphql.error import GraphQLError

LACK_OF_CHANNEL_IN_SORTING_MSG = (
    "You must provide a `channel` parameter to properly sorting data."
)


def validate_channel_slug(channel_slug: str):
    if not channel_slug:
        raise GraphQLError(LACK_OF_CHANNEL_IN_SORTING_MSG)
