import graphene
import graphene_django_optimizer as gql_optimizer
from django_countries.fields import Country
from graphene import relay

from ...payment import models
from ..account.types import Address
from ..core.connection import CountableDjangoObjectType
from ..core.types import Money
from .enums import OrderAction, PaymentChargeStatusEnum


class Transaction(CountableDjangoObjectType):
    amount = graphene.Field(
        Money, description='Total amount of the transaction.')

    class Meta:
        description = 'An object representing a single payment.'
        interfaces = [relay.Node]
        model = models.Transaction
        filter_fields = ['id']
        only_fields = [
            'id', 'created', 'payment', 'token', 'kind', 'is_success',
            'error', 'gateway_response']

    def resolve_amount(self, _info):
        return self.get_amount()


class CreditCard(graphene.ObjectType):
    brand = graphene.String(
        description='Card brand.', required=True)
    first_digits = graphene.String(
        description='The host name of the domain.', required=True)
    last_digits = graphene.String(
        description='Last 4 digits of the card number.', required=True)
    exp_month = graphene.Int(
        description=(
            'Two-digit number representing the card’s expiration month.'),
        required=True)
    exp_year = graphene.Int(
        description=(
            'Four-digit number representing the card’s expiration year.'),
        required=True)


class Payment(CountableDjangoObjectType):
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
    available_capture_amount = graphene.Field(
        Money, description='Maximum amount of money that can be captured.')
    available_refund_amount = graphene.Field(
        Money, description='Maximum amount of money that can be refunded.')
    credit_card = graphene.Field(
        CreditCard,
        description='The details of the card used for this payment.')

    class Meta:
        description = 'Represents a payment of a given type.'
        interfaces = [relay.Node]
        model = models.Payment
        filter_fields = ['id']
        only_fields = [
            'id', 'gateway', 'is_active', 'created', 'modified', 'token',
            'checkout', 'order', 'billing_email', 'customer_ip_address',
            'extra_data']

    @gql_optimizer.resolver_hints(prefetch_related='transactions')
    def resolve_actions(self, _info):
        actions = []
        if self.can_capture():
            actions.append(OrderAction.CAPTURE)
        if self.can_refund():
            actions.append(OrderAction.REFUND)
        if self.can_void():
            actions.append(OrderAction.VOID)
        return actions

    def resolve_total(self, _info):
        return self.get_total()

    def resolve_captured_amount(self, _info):
        return self.get_captured_amount()

    def resolve_billing_address(self, _info):
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

    @gql_optimizer.resolver_hints(prefetch_related='transactions')
    def resolve_transactions(self, _info):
        return self.transactions.all()

    def resolve_available_refund_amount(self, _info):
        # FIXME TESTME
        if not self.can_refund():
            return None
        return self.get_captured_amount()

    @gql_optimizer.resolver_hints(prefetch_related='transactions')
    def resolve_available_capture_amount(self, _info):
        # FIXME TESTME
        if not self.can_capture():
            return None
        return self.get_charge_amount()

    def resolve_credit_card(self, _info):
        data = {
            'first_digits': self.cc_first_digits,
            'last_digits': self.cc_last_digits,
            'brand': self.cc_brand,
            'exp_month': self.cc_exp_month,
            'exp_year': self.cc_exp_year}
        if not any(data.values()):
            return None
        return CreditCard(**data)
