import warnings

from .exceptions import ChannelSlugNotPassedException, NoChannelException
from .models import Channel

# TODO: Add message with deprecation date.
deprecation_warning_message = "TODO"


def get_default_channel_slug_if_available() -> str:
    try:
        channel = Channel.objects.get()
    except Channel.MultipleObjectsReturned:
        raise ChannelSlugNotPassedException()
    except Channel.DoesNotExist:
        raise NoChannelException()
    warnings.warn(deprecation_warning_message)
    return channel.slug
