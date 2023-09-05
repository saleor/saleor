import graphene

from ..core.descriptions import DEPRECATED_IN_3X_MUTATION
from .mutations.external_notification_trigger import ExternalNotificationTrigger


class ExternalNotificationMutations(graphene.ObjectType):
    external_notification_trigger = ExternalNotificationTrigger.Field(
        deprecation_reason=DEPRECATED_IN_3X_MUTATION
    )
