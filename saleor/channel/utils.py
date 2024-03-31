import warnings

from django.conf import settings

from .exceptions import ChannelNotDefined, NoDefaultChannel
from .models import Channel

DEPRECATION_WARNING_MESSAGE = (
    "Default channel used in a query. Please make sure that channel is explicitly "
    "provided. This behavior works only when a one channel exists and will be removed "
    "after 2020-12-31."
)


def get_default_channel(allow_replica: bool = False) -> Channel:
    """Return a default channel.

    Returns a channel only when exactly one channel exists in the system. If there are
    more channels, you need to ensure that the channel is explicitly specified. This
    function is intended to use throughout the full migration to the multi-channel
    approach in Saleor and will be removed after 2020-12-31. Since then, the API and
    all functions will require specifying the channel.

    :raises ChannelNotDefined: When there is more than one channel.
    :raises NoDefaultChannel: When there are no channels.
    """

    if allow_replica:
        database_connection_name = settings.DATABASE_CONNECTION_REPLICA_NAME
    else:
        database_connection_name = settings.DATABASE_CONNECTION_DEFAULT_NAME

    try:
        channel = Channel.objects.using(database_connection_name).get()
    except Channel.MultipleObjectsReturned:
        channels = list(
            Channel.objects.using(database_connection_name).filter(is_active=True)
        )
        if len(channels) == 1:
            warnings.warn(DEPRECATION_WARNING_MESSAGE)
            return channels[0]
        raise ChannelNotDefined()
    except Channel.DoesNotExist:
        raise NoDefaultChannel()
    else:
        warnings.warn(DEPRECATION_WARNING_MESSAGE)
        return channel
