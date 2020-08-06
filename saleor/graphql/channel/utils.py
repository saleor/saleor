from graphql.error import GraphQLError

from ...channel.exceptions import ChannelNotDefined, NoDefaultChannel
from ...channel.models import Channel
from ...channel.utils import get_default_channel


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
