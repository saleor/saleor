import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ...channel import models
from ...checkout.models import Checkout
from ...core.permissions import ChannelPermissions
from ...order.models import Order
from ..core.mutations import ModelDeleteMutation, ModelMutation
from ..core.types.common import ChannelError, ChannelErrorCode
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
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
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
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"


class ChannelDeleteInput(graphene.InputObjectType):
    target_channel = graphene.ID(
        required=True,
        description="ID of channel to migrate orders from origin channel.",
    )


class ChannelDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a channel to delete.")
        input = ChannelDeleteInput(
            required=True, description="Fields required to delete a channel."
        )

    class Meta:
        description = (
            "Delete a channel. Orders associated with the deleted "
            "channel will be moved to the target channel. "
            "Checkouts, product availability, and pricing will be removed."
        )
        model = models.Channel
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"

    @classmethod
    def validate_input(cls, origin_channel_id, target_channel_id):
        if origin_channel_id == target_channel_id:
            raise ValidationError(
                {
                    "target_channel": ValidationError(
                        "channelID and targetChannelID cannot be the same. "
                        "Use different target channel ID.",
                        code=ChannelErrorCode.CHANNEL_TARGET_ID_MUST_BE_DIFFERENT,
                    )
                }
            )

    @classmethod
    def perform_delete(cls, origin_channel, target_channel):
        cls.validate_input(origin_channel, target_channel)

        with transaction.atomic():
            cls.migrate_orders_to_target_channel(origin_channel, target_channel)
            cls.delete_checkouts(origin_channel)

    @classmethod
    def migrate_orders_to_target_channel(cls, origin_channel, target_channel):
        Order.objects.select_for_update().filter(channel_id=origin_channel).update(
            channel=target_channel
        )

    @classmethod
    def delete_checkouts(cls, origin_channel):
        Checkout.objects.select_for_update().filter(channel_id=origin_channel).delete()

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        origin_channel = cls.get_node_or_error(info, data["id"], only_type=Channel).id
        target_channel = cls.get_node_or_error(
            info, data["input"]["target_channel"], only_type=Channel
        ).id

        cls.perform_delete(origin_channel, target_channel)

        return super().perform_mutation(_root, info, **data)
