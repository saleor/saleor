from graphql.error import GraphQLError

LACK_OF_CHANNEL_IN_SORTING_MSG = "You must provide a `channel` as sorting param."


# TODO: consider this function as decorator?
def validate_channel_slug(channel_slug: str):
    if not channel_slug:
        raise GraphQLError(LACK_OF_CHANNEL_IN_SORTING_MSG)
