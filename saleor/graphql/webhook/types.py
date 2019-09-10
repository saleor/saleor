import graphene

from ...webhook import models
from ..core.connection import CountableDjangoObjectType


class Webhook(CountableDjangoObjectType):
    class Meta:
        description = "Webhook"
        model = models.Webhook
        interfaces = [graphene.relay.Node]
        only_fields = [
            "service_account",
            "service_account",
            "target_url",
            "event",
            "is_active",
        ]
