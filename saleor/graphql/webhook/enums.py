import graphene

from ...webhook.event_types import WebhookEventType
from ..core.utils import str_to_enum

WebhookEventTypeEnum = graphene.Enum(
    "WebhookEventTypeEnum",
    [(str_to_enum(e_type[0]), e_type[0]) for e_type in WebhookEventType.CHOICES],
)
WebhookSampleEventTypeEnum = graphene.Enum(
    "WebhookSampleEventTypeEnum",
    [
        (str_to_enum(e_type[0]), e_type[0])
        for e_type in WebhookEventType.CHOICES
        if e_type[0] != WebhookEventType.ANY
    ],
)
