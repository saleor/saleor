import graphene
from graphene import relay

from ...order import models
from ..core.types.common import CountableDjangoObjectType
from ...payment import PROVIDERS_ENUM
from graphene import types


class Payment(CountableDjangoObjectType):
    class Meta:
        description = 'Represents payment.'
        interfaces = [relay.Node]
        model = models.Payment
        exclude_fields = ['order']

PaymentGatewayEnum = graphene.Enum.from_enum(PROVIDERS_ENUM)
