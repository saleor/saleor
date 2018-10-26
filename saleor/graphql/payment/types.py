import graphene
from django_countries.fields import Country
from graphene import relay

from ...payment import GATEWAYS_ENUM, ChargeStatus, models
from ..account.types import Address
from ..core.types.common import CountableDjangoObjectType, CountryDisplay
from ..core.types.money import Money
from ..core.utils import str_to_enum

PaymentGatewayEnum = graphene.Enum.from_enum(GATEWAYS_ENUM)
PaymentChargeStatusEnum = graphene.Enum(
    'PaymentChargeStatusEnum',
    [(str_to_enum(code.upper()), code) for code, name in ChargeStatus.CHOICES])


class OrderAction(graphene.Enum):
    # FIXME could use a better name
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


class Transaction(CountableDjangoObjectType):
    amount = graphene.Field(
        Money, description='Total amount of the transaction.')

    class Meta:
        description = 'An object representing a single payment.'
        interfaces = [relay.Node]
        model = models.Transaction
        filter_fields = ['id', 'charge_status', 'is_success']
        exclude_fields = ['currency']

    @staticmethod
    def resolve_amount(self, info):
        return self.get_amount()


class Payment(CountableDjangoObjectType):
    # FIXME gateway_response field should be resolved into query-readable format
    # if we want to use it on the frontend
    # otherwise it should be removed from this type
    charge_status = PaymentChargeStatusEnum(
        description='Internal payment status.', required=True)
    actions = graphene.List(
        OrderAction, description='''List of actions that can be performed in
        the current state of a payment.''', required=True)
    total = graphene.Field(
        Money, description='Total amount of the payment.')
    captured_amount = graphene.Field(
        Money, description='Total amount captured for this payment.')
    billing_address = graphene.Field(
        Address, description='Customer billing address.')
    transactions = graphene.List(
        Transaction,
        description='List of all transactions within this payment.')

    class Meta:
        description = 'Represents a payment of a given type.'
        interfaces = [relay.Node]
        model = models.Payment
        filter_fields = ['id']
        exclude_fields = [
            'billing_first_name', 'billing_last_name', 'billing_company_name',
            'billing_address_1', 'billing_address_2', 'billing_city',
            'billing_postal_code', 'billing_country_code',
            'billing_country_area', 'currency', 'billing_city_area']

    def resolve_actions(self, info):
        actions = []
        if self.can_capture():
            actions.append(OrderAction.CAPTURE)
        if self.can_refund():
            actions.append(OrderAction.REFUND)
        if self.can_void():
            actions.append(OrderAction.VOID)
        return actions

    def resolve_total(self, info):
        return self.get_total()

    def resolve_captured_amount(self, info):
        return self.get_captured_amount()

    def resolve_billing_address(self, info):
        return Address(
            first_name=self.billing_first_name,
            last_name=self.billing_last_name,
            company_name=self.billing_company_name,
            street_address_1=self.billing_address_1,
            street_address_2=self.billing_address_2,
            city=self.billing_city,
            city_area=self.billing_city_area,
            postal_code=self.billing_postal_code,
            country=Country(self.billing_country_code),
            country_area=self.billing_country_area)

    def resolve_transactions(self, info):
        return self.transactions.all()
