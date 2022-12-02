import graphene

from .mutations.external_notification_trigger import ExternalNotificationTrigger


class ExternalNotificationMutations(graphene.ObjectType):
    external_notification_trigger = ExternalNotificationTrigger.Field()
