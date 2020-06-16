import graphene

from ...channel import models
from ...core.permissions import ChannelPermission
from ..core.mutations import ModelMutation
from ..core.types.common import ChannelError
from .types import Channel  # noqa: F401


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
