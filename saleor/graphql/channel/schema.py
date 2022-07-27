import graphene

from ...core.permissions import AuthorizationFilters
from ..core.descriptions import ADDED_IN_36, PREVIEW_FEATURE
from ..core.fields import PermissionsField
from ..core.types import NonNullList
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
    channel = graphene.Field(
        Channel,
        id=graphene.Argument(
            graphene.ID, description="ID of the channel.", required=False
        ),
        slug=graphene.Argument(
            graphene.String,
            description="Slug of the channel." + ADDED_IN_36 + PREVIEW_FEATURE,
            required=False,
        ),
        description="Look up a channel by ID or slug.",
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
    def resolve_channel(_root, info, *, id=None, slug=None, **kwargs):
        return resolve_channel(info, id, slug)

    @staticmethod
    def resolve_channels(_root, _info, **kwargs):
        return resolve_channels()


class ChannelMutations(graphene.ObjectType):
    channel_create = ChannelCreate.Field()
    channel_update = ChannelUpdate.Field()
    channel_delete = ChannelDelete.Field()
    channel_activate = ChannelActivate.Field()
    channel_deactivate = ChannelDeactivate.Field()
