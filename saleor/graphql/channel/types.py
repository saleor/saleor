from graphene import relay

from ...channel import models
from ..core.connection import CountableDjangoObjectType


class Channel(CountableDjangoObjectType):
    class Meta:
        descritpion = "TODO: fill"
        model = models.Channel
        interface = [relay.Node]
        only_fields = ["id", "name", "slug", "currency_code"]
