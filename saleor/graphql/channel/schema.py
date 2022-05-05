import graphene

from ...core.permissions import AuthorizationFilters
from ..core.fields import PermissionsField
from ..core.types import NonNullList
from ..core.utils import from_global_id_or_error
from .mutations import (
    ChannelActivate,
    ChannelCreate,
    ChannelDeactivate,
    ChannelDelete,
    ChannelUpdate,
)
from .resolvers import resolve_channel, resolve_channels
from .types import Channel


class ChannelQueries(graphene.ObjectType):
    channel = PermissionsField(
        Channel,
        id=graphene.Argument(graphene.ID, description="ID of the channel."),
        description="Look up a channel by ID.",
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )
    channels = PermissionsField(
        NonNullList(Channel),
        description="List of all channels.",
        permissions=[
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
        ],
    )

    @staticmethod
    def resolve_channel(_root, _info, *, id=None, **kwargs):
        _, id = from_global_id_or_error(id, Channel)
        return resolve_channel(id)

    @staticmethod
    def resolve_channels(_root, _info, **kwargs):
        return resolve_channels()


class ChannelMutations(graphene.ObjectType):
    channel_create = ChannelCreate.Field()
    channel_update = ChannelUpdate.Field()
    channel_delete = ChannelDelete.Field()
    channel_activate = ChannelActivate.Field()
    channel_deactivate = ChannelDeactivate.Field()
