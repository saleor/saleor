from typing import Dict, Optional

import graphene
from django.core.exceptions import ValidationError

from ....channel import models
from ....channel.error_codes import ChannelErrorCode
from ....checkout.models import Checkout
from ....core.tracing import traced_atomic_transaction
from ....order.models import Order
from ....permission.enums import ChannelPermissions
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import ChannelError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Channel
from ..utils import delete_invalid_warehouse_to_shipping_zone_relations


class ChannelDeleteInput(graphene.InputObjectType):
    channel_id = graphene.ID(
        required=True,
        description="ID of channel to migrate orders from origin channel.",
    )


class ChannelDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a channel to delete.")
        input = ChannelDeleteInput(description="Fields required to delete a channel.")

    class Meta:
        description = (
            "Delete a channel. Orders associated with the deleted "
            "channel will be moved to the target channel. "
            "Checkouts, product availability, and pricing will be removed."
        )
        model = models.Channel
        object_type = Channel
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"

    @classmethod
    def validate_input(cls, origin_channel, target_channel):
        if origin_channel.id == target_channel.id:
            raise ValidationError(
                {
                    "channel_id": ValidationError(
                        "Cannot migrate data to the channel that is being removed.",
                        code=ChannelErrorCode.INVALID.value,
                    )
                }
            )
        origin_channel_currency = origin_channel.currency_code
        target_channel_currency = target_channel.currency_code
        if origin_channel_currency != target_channel_currency:
            raise ValidationError(
                {
                    "channel_id": ValidationError(
                        f"Cannot migrate from {origin_channel_currency} "
                        f"to {target_channel_currency}. "
                        "Migration are allowed between the same currency",
                        code=ChannelErrorCode.CHANNELS_CURRENCY_MUST_BE_THE_SAME.value,
                    )
                }
            )

    @classmethod
    def migrate_orders_to_target_channel(cls, origin_channel_id, target_channel_id):
        Order.objects.select_for_update().filter(channel_id=origin_channel_id).update(
            channel=target_channel_id
        )

    @classmethod
    def delete_checkouts(cls, origin_channel_id):
        Checkout.objects.select_for_update().filter(
            channel_id=origin_channel_id
        ).delete()

    @classmethod
    def perform_delete_with_order_migration(cls, origin_channel, target_channel):
        cls.validate_input(origin_channel, target_channel)

        with traced_atomic_transaction():
            origin_channel_id = origin_channel.id
            cls.delete_checkouts(origin_channel_id)
            cls.migrate_orders_to_target_channel(origin_channel_id, target_channel.id)

    @classmethod
    def perform_delete_channel_without_order(cls, origin_channel):
        if Order.objects.filter(channel=origin_channel).exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot remove channel with orders. Try to migrate orders to "
                        "another channel by passing `targetChannel` param.",
                        code=ChannelErrorCode.CHANNEL_WITH_ORDERS.value,
                    )
                }
            )
        with traced_atomic_transaction():
            cls.delete_checkouts(origin_channel.id)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.channel_deleted, instance)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id: str, input: Optional[Dict] = None
    ):
        origin_channel = cls.get_node_or_error(info, id, only_type=Channel)
        target_channel_global_id = input.get("channel_id") if input else None
        if target_channel_global_id:
            target_channel = cls.get_node_or_error(
                info, target_channel_global_id, only_type=Channel
            )
            cls.perform_delete_with_order_migration(origin_channel, target_channel)
        else:
            cls.perform_delete_channel_without_order(origin_channel)
        with traced_atomic_transaction():
            delete_invalid_warehouse_to_shipping_zone_relations(
                origin_channel,
                origin_channel.warehouses.values("id"),
                channel_deletion=True,
            )
        return super().perform_mutation(root, info, id=id)
