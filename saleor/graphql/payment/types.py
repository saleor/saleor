import graphene
from graphene import relay

from ...payment import PROVIDERS_ENUM, ChargeStatus, models
from ..core.types.common import CountableDjangoObjectType
from ..core.utils import str_to_enum

PaymentGatewayEnum = graphene.Enum.from_enum(PROVIDERS_ENUM)
PaymentChargeStatusEnum = graphene.Enum(
    'PaymentChargeStatusEnum',
    [(str_to_enum(code.upper()), code) for code, name in ChargeStatus.CHOICES])


class PaymentMethod(CountableDjangoObjectType):
    #FIXME gateway_response field should be resolved into query-readable format
    charge_status = PaymentChargeStatusEnum(
        description='Internal payment status.', required=True)

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
