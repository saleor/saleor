import graphene
from graphene import relay

from ...core.exceptions import PermissionDenied
from ...core.permissions import OrderPermissions, PaymentPermissions
from ...core.tracing import traced_resolver
from ...payment import PaymentAction, models
from ..checkout.dataloaders import CheckoutByTokenLoader
from ..core.connection import CountableConnection
from ..core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_FIELD
from ..core.fields import JSONString
from ..core.types import ModelObjectType, Money
from ..decorators import one_of_permissions_required, permission_required
from ..meta.permissions import public_payment_permissions
from ..meta.resolvers import resolve_metadata
from ..meta.types import MetadataItem, ObjectWithMetadata
from ..utils import get_user_or_app_from_context
from .enums import PaymentActionEnum, PaymentChargeStatusEnum, TransactionKindEnum


class Transaction(ModelObjectType):
    id = graphene.GlobalID(required=True)
    created = graphene.DateTime(required=True)
    payment = graphene.Field(lambda: Payment, required=True)
    token = graphene.String(required=True)
    kind = TransactionKindEnum(required=True)
    is_success = graphene.Boolean(required=True)
    error = graphene.String()
    gateway_response = JSONString(required=True)
    amount = graphene.Field(Money, description="Total amount of the transaction.")

    class Meta:
        description = "An object representing a single payment."
        interfaces = [relay.Node]
        model = models.Transaction

    @staticmethod
    def resolve_amount(root: models.Transaction, _info):
        return root.get_amount()


class CreditCard(graphene.ObjectType):
    brand = graphene.String(description="Card brand.", required=True)
    first_digits = graphene.String(
        description="First 4 digits of the card number.", required=False
    )
    last_digits = graphene.String(
        description="Last 4 digits of the card number.", required=True
    )
    exp_month = graphene.Int(
        description="Two-digit number representing the card’s expiration month.",
        required=False,
    )
    exp_year = graphene.Int(
        description="Four-digit number representing the card’s expiration year.",
        required=False,
    )


class PaymentSource(graphene.ObjectType):
    class Meta:
        description = (
            "Represents a payment source stored "
            "for user in payment gateway, such as credit card."
        )

    gateway = graphene.String(description="Payment gateway name.", required=True)
    payment_method_id = graphene.String(description="ID of stored payment method.")
    credit_card_info = graphene.Field(
        CreditCard, description="Stored credit card details if available."
    )
    metadata = graphene.List(
        MetadataItem,
        required=True,
        description=(
            f"{ADDED_IN_31} List of public metadata items. "
            "Can be accessed without permissions."
        ),
    )


class Payment(ModelObjectType):
    id = graphene.GlobalID(required=True)
    checkout = graphene.Field("saleor.graphql.checkout.types.Checkout")
    order = graphene.Field("saleor.graphql.order.types.Order")
    actions = graphene.List(
        graphene.NonNull(PaymentActionEnum),
        description=(
            "List of actions that can be performed in the current state of a payment."
        ),
        required=True,
    )
    total = graphene.Field(Money, description="Total amount of the payment.")
    authorized_amount = graphene.Field(
        Money, required=True, description="Total amount authorized for this payment."
    )
    refunded_amount = graphene.Field(
        Money, required=True, description="Total amount refunded for this payment."
    )
    voided_amount = graphene.Field(
        Money, required=True, description="Total amount voided for this payment."
    )
    captured_amount = graphene.Field(
        Money, description="Total amount captured for this payment.", required=True
    )

    gateway = graphene.String(
        required=True,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )
    is_active = graphene.Boolean(
        required=True,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )
    created = graphene.DateTime(
        required=True,
    )
    modified = graphene.DateTime(required=True)
    token = graphene.String(
        required=True,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )
    payment_method_type = graphene.String(
        required=True,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )
    customer_ip_address = graphene.String(
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow."
    )
    charge_status = PaymentChargeStatusEnum(
        description="Internal payment status.",
        required=True,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )
    transactions = graphene.List(
        Transaction,
        description="List of all transactions within this payment.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )
    available_capture_amount = graphene.Field(
        Money,
        description="Maximum amount of money that can be captured.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )
    available_refund_amount = graphene.Field(
        Money,
        description="Maximum amount of money that can be refunded.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )
    credit_card = graphene.Field(
        CreditCard,
        description="The details of the card used for this payment.",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use new checkout flow.",
    )

    status = graphene.String(required=True)
    type = graphene.String(required=True)
    reference = graphene.String(required=True)

    class Meta:
        description = "Represents a payment of a given type."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Payment

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_customer_ip_address(root: models.Payment, _info):
        return root.customer_ip_address

    @staticmethod
    @one_of_permissions_required(
        [OrderPermissions.MANAGE_ORDERS, PaymentPermissions.HANDLE_PAYMENTS]
    )
    def resolve_actions(root: models.Payment, _info):
        if root.gateway:
            actions = []
            if root.can_capture():
                actions.append(PaymentAction.CAPTURE)
            if root.can_refund():
                actions.append(PaymentAction.REFUND)
            if root.can_void():
                actions.append(PaymentAction.VOID)
            return actions
        return root.available_actions

    @staticmethod
    @traced_resolver
    def resolve_total(root: models.Payment, _info):
        return root.get_total()

    @staticmethod
    @one_of_permissions_required(
        [OrderPermissions.MANAGE_ORDERS, PaymentPermissions.HANDLE_PAYMENTS]
    )
    def resolve_transactions(root: models.Payment, _info):
        return root.transactions.all()

    @staticmethod
    @one_of_permissions_required(
        [OrderPermissions.MANAGE_ORDERS, PaymentPermissions.HANDLE_PAYMENTS]
    )
    def resolve_available_refund_amount(root: models.Payment, _info):
        if not root.can_refund():
            return None
        return root.get_captured_amount()

    @staticmethod
    @one_of_permissions_required(
        [OrderPermissions.MANAGE_ORDERS, PaymentPermissions.HANDLE_PAYMENTS]
    )
    def resolve_available_capture_amount(root: models.Payment, _info):
        if not root.can_capture():
            return None
        return Money(amount=root.get_charge_amount(), currency=root.currency)

    @staticmethod
    def resolve_credit_card(root: models.Payment, _info):
        data = {
            "brand": root.cc_brand,
            "exp_month": root.cc_exp_month,
            "exp_year": root.cc_exp_year,
            "first_digits": root.cc_first_digits,
            "last_digits": root.cc_last_digits,
        }
        if not any(data.values()):
            return None
        return CreditCard(**data)

    @staticmethod
    def resolve_metadata(root: models.Payment, info):
        permissions = public_payment_permissions(info, root.pk)
        requester = get_user_or_app_from_context(info.context)
        if not requester.has_perms(permissions):
            raise PermissionDenied(permissions=permissions)
        return resolve_metadata(root.metadata)

    @staticmethod
    def resolve_checkout(root: models.Payment, info):
        if not root.checkout_id:
            return None
        return CheckoutByTokenLoader(info.context).load(root.checkout_id)

    @staticmethod
    def resolve_captured_amount(root: models.Payment, _info):
        return root.amount_captured

    @staticmethod
    def resolve_authorized_amount(root: models.Payment, _info):
        return root.amount_authorized

    @staticmethod
    def resolve_voided_amount(root: models.Payment, _info):
        return root.amount_voided

    @staticmethod
    def resolve_refunded_amount(root: models.Payment, _info):
        return root.amount_refunded


class PaymentCountableConnection(CountableConnection):
    class Meta:
        node = Payment


class PaymentInitialized(graphene.ObjectType):
    class Meta:
        description = (
            "Server-side data generated by a payment gateway. Optional step when the "
            "payment provider requires an additional action to initialize payment "
            "session."
        )

    gateway = graphene.String(description="ID of a payment gateway.", required=True)
    name = graphene.String(description="Payment gateway name.", required=True)
    data = JSONString(description="Initialized data by gateway.", required=False)
