import graphene
from django_countries.fields import Country
from graphene import relay

from ...payment import models
from ..account.types import Address
from ..core.connection import CountableDjangoObjectType
from ..core.types import Money
from .enums import OrderAction, PaymentChargeStatusEnum


class Transaction(CountableDjangoObjectType):
    amount = graphene.Field(Money, description="Total amount of the transaction.")

    class Meta:
        description = "An object representing a single payment."
        interfaces = [relay.Node]
        model = models.Transaction
        filter_fields = ["id"]
        only_fields = [
            "id",
            "created",
            "payment",
            "token",
            "kind",
            "is_success",
            "error",
            "gateway_response",
        ]

    @staticmethod
    def resolve_amount(root: models.Transaction, _info):
        return root.get_amount()


class CreditCard(graphene.ObjectType):
    brand = graphene.String(description="Card brand.", required=True)
    first_digits = graphene.String(
        description="The host name of the domain.", required=True
    )
    last_digits = graphene.String(
        description="Last 4 digits of the card number.", required=True
    )
    exp_month = graphene.Int(
        description=("Two-digit number representing the card’s expiration month."),
        required=True,
    )
    exp_year = graphene.Int(
        description=("Four-digit number representing the card’s expiration year."),
        required=True,
    )


class PaymentSource(graphene.ObjectType):
    class Meta:
        description = (
            "Represents a payment source stored "
            "for user in payment gateway, such as credit card."
        )

    gateway = graphene.String(description="Payment gateway name.", required=True)
    credit_card_info = graphene.Field(
        CreditCard, description="Stored credit card details if available."
    )


class Payment(CountableDjangoObjectType):
    charge_status = PaymentChargeStatusEnum(
        description="Internal payment status.", required=True
    )
    actions = graphene.List(
        OrderAction,
        description=(
            "List of actions that can be performed in the current state of a payment."
        ),
        required=True,
    )
    total = graphene.Field(Money, description="Total amount of the payment.")
    captured_amount = graphene.Field(
        Money, description="Total amount captured for this payment."
    )
    billing_address = graphene.Field(Address, description="Customer billing address.")
    transactions = graphene.List(
        Transaction, description="List of all transactions within this payment."
    )
    available_capture_amount = graphene.Field(
        Money, description="Maximum amount of money that can be captured."
    )
    available_refund_amount = graphene.Field(
        Money, description="Maximum amount of money that can be refunded."
    )
    credit_card = graphene.Field(
        CreditCard, description="The details of the card used for this payment."
    )

    class Meta:
        description = "Represents a payment of a given type."
        interfaces = [relay.Node]
        model = models.Payment
        filter_fields = ["id"]
        only_fields = [
            "id",
            "gateway",
            "is_active",
            "created",
            "modified",
            "token",
            "checkout",
            "order",
            "billing_email",
            "customer_ip_address",
            "extra_data",
        ]

    @staticmethod
    def resolve_actions(root: models.Payment, _info):
        actions = []
        if root.can_capture():
            actions.append(OrderAction.CAPTURE)
        if root.can_refund():
            actions.append(OrderAction.REFUND)
        if root.can_void():
            actions.append(OrderAction.VOID)
        return actions

    @staticmethod
    def resolve_total(root: models.Payment, _info):
        return root.get_total()

    @staticmethod
    def resolve_captured_amount(root: models.Payment, _info):
        return root.get_captured_amount()

    @staticmethod
    def resolve_billing_address(root: models.Payment, _info):
        return Address(
            first_name=root.billing_first_name,
            last_name=root.billing_last_name,
            company_name=root.billing_company_name,
            street_address_1=root.billing_address_1,
            street_address_2=root.billing_address_2,
            city=root.billing_city,
            city_area=root.billing_city_area,
            postal_code=root.billing_postal_code,
            country=Country(root.billing_country_code),
            country_area=root.billing_country_area,
        )

    @staticmethod
    def resolve_transactions(root: models.Payment, _info):
        return root.transactions.all()

    @staticmethod
    def resolve_available_refund_amount(root: models.Payment, _info):
        # FIXME TESTME
        if not root.can_refund():
            return None
        return root.get_captured_amount()

    @staticmethod
    def resolve_available_capture_amount(root: models.Payment, _info):
        # FIXME TESTME
        if not root.can_capture():
            return None
        return root.get_charge_amount()

    @staticmethod
    def resolve_credit_card(root: models.Payment, _info):
        data = {
            "first_digits": root.cc_first_digits,
            "last_digits": root.cc_last_digits,
            "brand": root.cc_brand,
            "exp_month": root.cc_exp_month,
            "exp_year": root.cc_exp_year,
        }
        if not any(data.values()):
            return None
        return CreditCard(**data)
