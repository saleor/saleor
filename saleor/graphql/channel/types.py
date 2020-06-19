from graphene import relay

from ...channel import models
from ..core.connection import CountableDjangoObjectType


class Channel(CountableDjangoObjectType):
    class Meta:
        description = "Represents channel."
        model = models.Channel
        interfaces = [relay.Node]
        only_fields = ["id", "name", "slug", "currency_code"]
