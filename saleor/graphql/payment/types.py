import graphene
from graphene import relay

from ...payment import PROVIDERS_ENUM, models
from ..core.types.common import CountableDjangoObjectType

PaymentGatewayEnum = graphene.Enum.from_enum(PROVIDERS_ENUM)


class PaymentMethod(CountableDjangoObjectType):
    class Meta:
        description = 'Payment method'
        interfaces = [relay.Node]
        model = models.PaymentMethod
        filter_fields = ['id']


class Transaction(CountableDjangoObjectType):
    class Meta:
        description = 'Single payment transaction'
        interfaces = [relay.Node]
        model = models.Transaction
        filter_fields = ['id']
