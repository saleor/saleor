import graphene

from ...channel import models
from ...core.permissions import ChannelPermission
from ..core.mutations import ModelMutation
from ..core.types.common import ChannelError
from .types import Channel


class ChannelCreateInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the channel.", required=True)
    slug = graphene.String(description="Slug of the channel.", required=True)
    currency_code = graphene.String(
        description="Currency of the channel.", required=True
    )


class ChannelCreate(ModelMutation):
    class Arguments:
        input = ChannelCreateInput(
            required=True, description="Fields required to create channel."
        )

    class Meta:
        description = "Creates new channel."
        model = models.Channel
        permissions = (ChannelPermission.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"

    @classmethod
    def get_type_for_model(cls):
        return Channel


class ChannelUpdateInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the channel.")
    slug = graphene.String(description="Slug of the channel.")


class ChannelUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a channel to update.")
        input = ChannelUpdateInput(
            description="Fields required to update a channel.", required=True
        )

    class Meta:
        description = "Update a channel."
        model = models.Channel
        permissions = (ChannelPermission.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"
