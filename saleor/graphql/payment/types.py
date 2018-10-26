import graphene
from graphene import relay

from ...payment import GATEWAYS_ENUM, ChargeStatus, models
from ..core.types.common import CountableDjangoObjectType
from ..core.utils import str_to_enum

PaymentGatewayEnum = graphene.Enum.from_enum(GATEWAYS_ENUM)
PaymentChargeStatusEnum = graphene.Enum(
    'PaymentChargeStatusEnum',
    [(str_to_enum(code.upper()), code) for code, name in ChargeStatus.CHOICES])


class OrderAction(graphene.Enum):
    CAPTURE = 'CAPTURE'
    MARK_AS_PAID = 'MARK_AS_PAID'
    REFUND = 'REFUND'
    VOID = 'VOID'

    @property
    def description(self):
        if self == OrderAction.CAPTURE:
            return 'Represents the capture action.'
        if self == OrderAction.MARK_AS_PAID:
            return 'Represents a mark-as-paid action.'
        if self == OrderAction.REFUND:
            return 'Represents a refund action.'
        if self == OrderAction.VOID:
            return 'Represents a void action.'


class Payment(CountableDjangoObjectType):
    # FIXME gateway_response field should be resolved into query-readable format
    # if we want to use it on the frontend
    # otherwise it should be removed from this type
    charge_status = PaymentChargeStatusEnum(
        description='Internal payment status.', required=True)
    actions = graphene.List(
        OrderAction, description='''List of actions that can be performed in
        the current state of a payment.''', required=True)

    class Meta:
        description = 'Represents a payment of a given type.'
        interfaces = [relay.Node]
        model = models.Payment
        filter_fields = ['id']

    def resolve_actions(self, info):
        actions = []
        if self.can_capture():
            actions.append(OrderAction.CAPTURE)
        if self.can_refund():
            actions.append(OrderAction.REFUND)
        if self.can_void():
            actions.append(OrderAction.VOID)
        return actions


class Transaction(CountableDjangoObjectType):
    class Meta:
        description = 'An object representing a single payment.'
        interfaces = [relay.Node]
        model = models.Transaction
        filter_fields = ['id']
