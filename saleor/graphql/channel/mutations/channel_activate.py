import graphene
from django.core.exceptions import ValidationError

from ....channel.error_codes import ChannelErrorCode
from ....permission.enums import ChannelPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_CHANNELS
from ...core.mutations import BaseMutation
from ...core.types import ChannelError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Channel


class ChannelActivate(BaseMutation):
    channel = graphene.Field(Channel, description="Activated channel.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the channel to activate.")

    class Meta:
        description = "Activate a channel."
        doc_category = DOC_CATEGORY_CHANNELS
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHANNEL_STATUS_CHANGED,
                description="A channel was activated.",
            ),
        ]

    @classmethod
    def clean_channel_availability(cls, channel):
        if channel.is_active:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "This channel is already activated.",
                        code=ChannelErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        channel = cls.get_node_or_error(info, data["id"], only_type=Channel)
        cls.clean_channel_availability(channel)
        channel.is_active = True
        channel.save(update_fields=["is_active"])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.channel_status_changed, channel)
        return ChannelActivate(channel=channel)
