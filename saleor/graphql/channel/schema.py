import graphene

from ...permission.auth_filters import AuthorizationFilters
from ..core import ResolveInfo
from ..core.doc_category import DOC_CATEGORY_CHANNELS
from ..core.fields import PermissionsField
from ..core.types import NonNullList
from ..directives import doc
from .mutations import (
    ChannelActivate,
    ChannelCreate,
    ChannelDeactivate,
    ChannelDelete,
    ChannelReorderWarehouses,
    ChannelUpdate,
)
from .resolvers import resolve_channel, resolve_channels
from .types import Channel


class ChannelQueries(graphene.ObjectType):
    channel = doc(
        DOC_CATEGORY_CHANNELS,
        graphene.Field(
            Channel,
            id=graphene.Argument(
                graphene.ID, description="ID of the channel.", required=False
            ),
            slug=graphene.Argument(
                graphene.String,
                description="Slug of the channel.",
                required=False,
            ),
            description="Look up a channel by ID or slug.",
        ),
    )
    channels = doc(
        DOC_CATEGORY_CHANNELS,
        PermissionsField(
            NonNullList(Channel),
            description="List of all channels.",
            permissions=[
                AuthorizationFilters.AUTHENTICATED_APP,
                AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            ],
        ),
    )

    @staticmethod
    def resolve_channel(_root, info: ResolveInfo, *, id=None, slug=None, **kwargs):
        return resolve_channel(info, id, slug)

    @staticmethod
    def resolve_channels(_root, info: ResolveInfo, **kwargs):
        return resolve_channels(info)


class ChannelMutations(graphene.ObjectType):
    channel_create = ChannelCreate.Field()
    channel_update = ChannelUpdate.Field()
    channel_delete = ChannelDelete.Field()
    channel_activate = ChannelActivate.Field()
    channel_deactivate = ChannelDeactivate.Field()
    channel_reorder_warehouses = ChannelReorderWarehouses.Field()
