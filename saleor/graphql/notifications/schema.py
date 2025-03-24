import graphene

from ..core.descriptions import DEFAULT_DEPRECATION_REASON
from .mutations.external_notification_trigger import ExternalNotificationTrigger


class ExternalNotificationMutations(graphene.ObjectType):
    external_notification_trigger = ExternalNotificationTrigger.Field(
        deprecation_reason=DEFAULT_DEPRECATION_REASON
    )
