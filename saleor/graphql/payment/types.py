import graphene
from graphene import relay

from ...payment import PROVIDERS_ENUM, models
from ..core.types.common import CountableDjangoObjectType

PaymentGatewayEnum = graphene.Enum.from_enum(PROVIDERS_ENUM)


class PaymentMethod(CountableDjangoObjectType):
    class Meta:
        description = 'Represents a payment method of a given type.'
        interfaces = [relay.Node]
        model = models.PaymentMethod
        filter_fields = ['id']


class Transaction(CountableDjangoObjectType):
    class Meta:
        description = 'An object representing a single payment.'
        interfaces = [relay.Node]
        model = models.Transaction
        filter_fields = ['id']
