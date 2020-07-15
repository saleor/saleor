import warnings

from .exceptions import ChannelSlugNotPassedException, NoChannelException
from .models import Channel

# TODO: Add message with deprecation date.
DEPRECATION_WARNING_MESSAGE = (
    "DEPRECATED: Channel slug not passed. Query working only if exists one channel."
    "This behavior will be removed after XXXX-XX-XX."
)


def get_default_channel_slug_if_available() -> str:
    try:
        channel = Channel.objects.get()
    except Channel.MultipleObjectsReturned:
        raise ChannelSlugNotPassedException()
    except Channel.DoesNotExist:
        raise NoChannelException()
    warnings.warn(DEPRECATION_WARNING_MESSAGE)
    return channel.slug
