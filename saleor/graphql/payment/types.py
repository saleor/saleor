import graphene
from graphene import relay

from ...core.exceptions import PermissionDenied
from ...core.permissions import (
    AccountPermissions,
    AuthorizationFilters,
    OrderPermissions,
)
from ...core.tracing import traced_resolver
from ...payment import models
from ..account.dataloaders import UserByUserIdLoader
from ..app.dataloaders import AppByIdLoader
from ..checkout.dataloaders import CheckoutByTokenLoader
from ..core.connection import CountableConnection
from ..core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    ADDED_IN_36,
    ADDED_IN_38,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ..core.fields import JSONString, PermissionsField
from ..core.types import ModelObjectType, Money, NonNullList
from ..meta.permissions import public_payment_permissions
from ..meta.resolvers import resolve_metadata
from ..meta.types import MetadataItem, ObjectWithMetadata
from ..order.dataloaders import OrderByIdLoader
from ..utils import get_user_or_app_from_context
from .dataloaders import (
    TransactionByPaymentIdLoader,
    TransactionEventByTransactionIdLoader,
)
from .enums import (
    OrderAction,
    PaymentChargeStatusEnum,
    TransactionActionEnum,
    TransactionEventStatusEnum,
    TransactionEventTypeEnum,
    TransactionKindEnum,
)


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
    def resolve_created(root: models.Transaction, _info):
        return root.created_at

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
    metadata = NonNullList(
        MetadataItem,
        required=True,
        description=(
            "List of public metadata items."
            + ADDED_IN_31
            + "\n\nCan be accessed without permissions."
        ),
    )


class Payment(ModelObjectType):
    id = graphene.GlobalID(required=True)
    gateway = graphene.String(required=True)
    is_active = graphene.Boolean(required=True)
    created = graphene.DateTime(required=True)
    modified = graphene.DateTime(required=True)
    token = graphene.String(required=True)
    checkout = graphene.Field("saleor.graphql.checkout.types.Checkout")
    order = graphene.Field("saleor.graphql.order.types.Order")
    payment_method_type = graphene.String(required=True)
    customer_ip_address = PermissionsField(
        graphene.String,
        description="IP address of the user who created the payment.",
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    charge_status = PaymentChargeStatusEnum(
        description="Internal payment status.", required=True
    )
    actions = PermissionsField(
        NonNullList(OrderAction),
        description=(
            "List of actions that can be performed in the current state of a payment."
        ),
        required=True,
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    total = graphene.Field(Money, description="Total amount of the payment.")
    captured_amount = graphene.Field(
        Money, description="Total amount captured for this payment."
    )
    transactions = PermissionsField(
        NonNullList(Transaction),
        description="List of all transactions within this payment.",
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    available_capture_amount = PermissionsField(
        Money,
        description="Maximum amount of money that can be captured.",
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    available_refund_amount = PermissionsField(
        Money,
        description="Maximum amount of money that can be refunded.",
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    credit_card = graphene.Field(
        CreditCard, description="The details of the card used for this payment."
    )

    class Meta:
        description = "Represents a payment of a given type."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Payment

    @staticmethod
    def resolve_created(root: models.Payment, _info):
        return root.created_at

    @staticmethod
    def resolve_modified(root: models.Payment, _info):
        return root.modified_at

    @staticmethod
    def resolve_customer_ip_address(root: models.Payment, _info):
        return root.customer_ip_address

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
    @traced_resolver
    def resolve_total(root: models.Payment, _info):
        return root.get_total()

    @staticmethod
    def resolve_captured_amount(root: models.Payment, _info):
        return root.get_captured_amount()

    @staticmethod
    def resolve_transactions(root: models.Payment, info):
        return TransactionByPaymentIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_available_refund_amount(root: models.Payment, _info):
        if not root.can_refund():
            return None
        return root.get_captured_amount()

    @staticmethod
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

    def resolve_checkout(root: models.Payment, info):
        if not root.checkout_id:
            return None
        return CheckoutByTokenLoader(info.context).load(root.checkout_id)


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


class TransactionEvent(ModelObjectType):
    created_at = graphene.DateTime(required=True)
    status = graphene.Field(
        TransactionEventStatusEnum,
        description="Status of transaction's event.",
        required=True,
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use `type` instead.",
    )
    reference = graphene.String(
        description="Reference of transaction's event.",
        required=True,
        deprecation_reason=(
            "This field will be removed in Saleor 3.9 (Feature Preview). "
            "Use `pspReference` instead."
        ),
    )
    psp_reference = graphene.String(
        description="PSP reference of transaction." + ADDED_IN_38, required=True
    )
    name = graphene.String(
        description="Name of the transaction's event.",
        deprecation_reason=(f"{DEPRECATED_IN_3X_FIELD} Use `message` instead."),
    )
    message = graphene.String(
        description="Message related to the transaction's event.",
    )
    external_url = graphene.String(
        description=(
            "The url that will allow to redirect user to "
            "payment provider page with transaction details." + ADDED_IN_38
        ),
        required=True,
    )
    amount = graphene.Field(
        Money,
        required=True,
        description="The amount related to this event." + ADDED_IN_38,
    )
    type = graphene.Field(
        TransactionEventTypeEnum,
        description="The type of action related to this event." + ADDED_IN_38,
    )

    class Meta:
        description = "Represents transaction's event."
        interfaces = [relay.Node]
        model = models.TransactionEvent

    @staticmethod
    def resolve_reference(root: models.TransactionEvent, info):
        return root.psp_reference or ""

    @staticmethod
    def resolve_psp_reference(root: models.TransactionEvent, info):
        return root.psp_reference or ""

    @staticmethod
    def resolve_external_url(root: models.TransactionEvent, info):
        return root.external_url or ""

    @staticmethod
    def resolve_name(root: models.TransactionEvent, info):
        return root.message


class TransactionItem(ModelObjectType):
    created_at = graphene.DateTime(required=True)
    modified_at = graphene.DateTime(required=True)
    actions = NonNullList(
        TransactionActionEnum,
        description=(
            "List of actions that can be performed in the current state of a payment."
        ),
        required=True,
    )
    authorized_amount = graphene.Field(
        Money, required=True, description="Total amount authorized for this payment."
    )
    refunded_amount = graphene.Field(
        Money, required=True, description="Total amount refunded for this payment."
    )
    voided_amount = graphene.Field(
        Money, required=True, description="Total amount voided for this payment."
    )
    charged_amount = graphene.Field(
        Money, description="Total amount charged for this payment.", required=True
    )
    status = graphene.String(description="Status of transaction.", required=True)
    type = graphene.String(description="Type of transaction.", required=True)
    reference = graphene.String(
        description="Reference of transaction.",
        required=True,
        deprecation_reason=(
            "This field will be removed in Saleor 3.9 (Feature Preview). "
            "Use `pspReference` instead."
        ),
    )
    psp_reference = graphene.String(
        description="PSP reference of transaction." + ADDED_IN_38, required=True
    )
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="The related order." + ADDED_IN_36,
    )
    events = NonNullList(
        TransactionEvent, required=True, description="List of all transaction's events."
    )
    user = graphene.Field(
        "saleor.graphql.account.types.User",
        description=(
            "User who created the transaction."
            + ADDED_IN_38
            + PREVIEW_FEATURE
            + "\n\nRequires one of the following permissions: "
            f"{AccountPermissions.MANAGE_USERS.name}, "
            f"{AccountPermissions.MANAGE_STAFF.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    app = PermissionsField(
        "saleor.graphql.app.types.App",
        description=(
            "App that created the transaction." + ADDED_IN_38 + PREVIEW_FEATURE
        ),
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )
    external_url = graphene.String(
        description=(
            "The url that will allow to redirect user to "
            "payment provider page with transaction details." + ADDED_IN_38
        ),
        required=True,
    )

    class Meta:
        description = (
            "Represents a payment transaction." + ADDED_IN_34 + PREVIEW_FEATURE
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.TransactionItem

    @staticmethod
    def resolve_actions(root: models.TransactionItem, _info):
        return root.available_actions

    @staticmethod
    def resolve_charged_amount(root: models.TransactionItem, _info):
        return root.amount_charged

    @staticmethod
    def resolve_authorized_amount(root: models.TransactionItem, _info):
        return root.amount_authorized

    @staticmethod
    def resolve_voided_amount(root: models.TransactionItem, _info):
        return root.amount_voided

    @staticmethod
    def resolve_refunded_amount(root: models.TransactionItem, _info):
        return root.amount_refunded

    @staticmethod
    def resolve_order(root: models.TransactionItem, info):
        if not root.order_id:
            return
        return OrderByIdLoader(info.context).load(root.order_id)

    @staticmethod
    def resolve_events(root: models.TransactionItem, info):
        return TransactionEventByTransactionIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_user(root: models.TransactionItem, info):
        def _resolve_user(event_user):
            requester = get_user_or_app_from_context(info.context)
            if (
                requester == event_user
                or requester.has_perm(AccountPermissions.MANAGE_USERS)
                or requester.has_perm(AccountPermissions.MANAGE_STAFF)
            ):
                return event_user
            return None

        if not root.user_id:
            return None

        return UserByUserIdLoader(info.context).load(root.user_id).then(_resolve_user)

    @staticmethod
    def resolve_app(root: models.TransactionItem, info):
        if root.app_id:
            return AppByIdLoader(info.context).load(root.app_id)
        return None

    @staticmethod
    def resolve_reference(root: models.TransactionItem, info):
        return root.psp_reference or ""

    @staticmethod
    def resolve_psp_reference(root: models.TransactionItem, info):
        return root.psp_reference or ""

    @staticmethod
    def resolve_external_url(root: models.TransactionItem, info):
        return root.external_url or ""
