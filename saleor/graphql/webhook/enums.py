import graphene

from ...webhook import WebhookEventType
from ..core.utils import str_to_enum

WebhookEventTypeEnum = graphene.Enum(
    "WebhookEventTypeEnum",
    [(str_to_enum(e_type[0]), e_type[0]) for e_type in WebhookEventType.CHOICES],
)
