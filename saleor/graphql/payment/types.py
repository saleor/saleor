from typing import Any, Optional
from uuid import UUID

import graphene
from django.db.models import Q
from graphene import relay

from ...core.exceptions import PermissionDenied
from ...payment import models
from ...payment.interface import PaymentMethodData
from ...permission.enums import OrderPermissions
from ..account.dataloaders import UserByUserIdLoader
from ..app.dataloaders import AppByIdLoader, AppsByAppIdentifierLoader
from ..checkout.dataloaders import CheckoutByTokenLoader
from ..core import ResolveInfo
from ..core.connection import CountableConnection
from ..core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    ADDED_IN_36,
    ADDED_IN_313,
    ADDED_IN_315,
    PREVIEW_FEATURE,
)
from ..core.doc_category import DOC_CATEGORY_PAYMENTS
from ..core.fields import JSONString, PermissionsField
from ..core.scalars import JSON
from ..core.tracing import traced_resolver
from ..core.types import BaseObjectType, ModelObjectType, Money, NonNullList
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
    TokenizedPaymentFlowEnum,
    TransactionActionEnum,
    TransactionEventTypeEnum,
    TransactionKindEnum,
)


class Transaction(ModelObjectType[models.Transaction]):
    id = graphene.GlobalID(required=True, description="ID of the transaction.")
    created = graphene.DateTime(
        required=True, description="Date and time which transaction was created."
    )
    payment = graphene.Field(
        lambda: Payment,
        required=True,
        description="Determines the payment associated with a transaction.",
    )
    token = graphene.String(
        required=True, description="Unique token associated with a transaction."
    )
    kind = TransactionKindEnum(
        required=True, description="Determines the type of transaction."
    )
    is_success = graphene.Boolean(
        required=True, description="Determines if the transaction was successful."
    )
    error = graphene.String(description="Error associated with transaction, if any.")
    gateway_response = JSONString(
        required=True, description="Response returned by payment gateway."
    )
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


class CreditCard(BaseObjectType):
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

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentSource(BaseObjectType):
    class Meta:
        description = (
            "Represents a payment source stored "
            "for user in payment gateway, such as credit card."
        )
        doc_category = DOC_CATEGORY_PAYMENTS

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


class Payment(ModelObjectType[models.Payment]):
    id = graphene.GlobalID(required=True, description="ID of the payment.")
    gateway = graphene.String(
        required=True, description="Payment gateway used for payment."
    )
    is_active = graphene.Boolean(
        required=True, description="Determines if the payment is active or not."
    )
    created = graphene.DateTime(
        required=True, description="Date and time at which payment was created."
    )
    modified = graphene.DateTime(
        required=True, description="Date and time at which payment was modified."
    )
    token = graphene.String(
        required=True, description="Unique token associated with a payment."
    )
    checkout = graphene.Field(
        "saleor.graphql.checkout.types.Checkout",
        description="Checkout associated with a payment.",
    )
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="Order associated with a payment.",
    )
    payment_method_type = graphene.String(
        required=True, description="Type of method used for payment."
    )
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
        if not requester or not requester.has_perms(permissions):
            raise PermissionDenied(permissions=permissions)
        return resolve_metadata(root.metadata)

    def resolve_checkout(root: models.Payment, info):
        if not root.checkout_id:
            return None
        return CheckoutByTokenLoader(info.context).load(root.checkout_id)


class PaymentCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        node = Payment


class PaymentInitialized(BaseObjectType):
    class Meta:
        description = (
            "Server-side data generated by a payment gateway. Optional step when the "
            "payment provider requires an additional action to initialize payment "
            "session."
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    gateway = graphene.String(description="ID of a payment gateway.", required=True)
    name = graphene.String(description="Payment gateway name.", required=True)
    data = JSONString(description="Initialized data by gateway.", required=False)


class TransactionEvent(ModelObjectType[models.TransactionEvent]):
    created_at = graphene.DateTime(
        required=True,
        description="Date and time at which a transaction event was created.",
    )
    psp_reference = graphene.String(
        description="PSP reference of transaction." + ADDED_IN_313, required=True
    )
    message = graphene.String(
        description="Message related to the transaction's event." + ADDED_IN_313,
        required=True,
    )
    external_url = graphene.String(
        description=(
            "The url that will allow to redirect user to "
            "payment provider page with transaction details." + ADDED_IN_313
        ),
        required=True,
    )
    amount = graphene.Field(
        Money,
        required=True,
        description="The amount related to this event." + ADDED_IN_313,
    )
    type = graphene.Field(
        TransactionEventTypeEnum,
        description="The type of action related to this event." + ADDED_IN_313,
    )

    created_by = graphene.Field(
        "saleor.graphql.core.types.user_or_app.UserOrApp",
        description=("User or App that created the transaction event." + ADDED_IN_313),
    )

    class Meta:
        description = "Represents transaction's event."
        interfaces = [relay.Node]
        model = models.TransactionEvent

    @staticmethod
    def resolve_psp_reference(root: models.TransactionEvent, info):
        return root.psp_reference or ""

    @staticmethod
    def resolve_external_url(root: models.TransactionEvent, info):
        return root.external_url or ""

    @staticmethod
    def resolve_message(root: models.TransactionEvent, info):
        return root.message or ""

    @staticmethod
    def resolve_created_by(root: models.TransactionItem, info):
        """Resolve createdBy.

        Try to fetch the app by db relation first. This cover all apps created manually
        by staff user and the third-party app that was not re-installed.
        If the root.app_id is none, we're trying to fetch the app by `app.identifier`.
        This covers a case when a third-party app was re-installed, but we're still able
        to determine which one is the owner of the transaction.
        """
        if root.app_id:
            return AppByIdLoader(info.context).load(root.app_id)
        if root.app_identifier:

            def get_first_app(apps):
                if apps:
                    return apps[0]
                return None

            return (
                AppsByAppIdentifierLoader(info.context)
                .load(root.app_identifier)
                .then(get_first_app)
            )
        if root.user_id:
            return UserByUserIdLoader(info.context).load(root.user_id)
        return None


class TransactionItem(ModelObjectType[models.TransactionItem]):
    created_at = graphene.DateTime(
        required=True,
        description="Date and time at which payment transaction was created.",
    )
    modified_at = graphene.DateTime(
        required=True,
        description="Date and time at which payment transaction was modified.",
    )
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
    authorize_pending_amount = graphene.Field(
        Money,
        required=True,
        description=(
            "Total amount of ongoing authorization requests for the transaction."
            + ADDED_IN_313
        ),
    )
    refunded_amount = graphene.Field(
        Money, required=True, description="Total amount refunded for this payment."
    )
    refund_pending_amount = graphene.Field(
        Money,
        required=True,
        description=(
            "Total amount of ongoing refund requests for the transaction."
            + ADDED_IN_313
        ),
    )

    canceled_amount = graphene.Field(
        Money,
        required=True,
        description="Total amount canceled for this payment." + ADDED_IN_313,
    )
    cancel_pending_amount = graphene.Field(
        Money,
        required=True,
        description=(
            "Total amount of ongoing cancel requests for the transaction."
            + ADDED_IN_313
        ),
    )
    charged_amount = graphene.Field(
        Money, description="Total amount charged for this payment.", required=True
    )
    charge_pending_amount = graphene.Field(
        Money,
        required=True,
        description=(
            "Total amount of ongoing charge requests for the transaction."
            + ADDED_IN_313
        ),
    )
    name = graphene.String(
        description="Name of the transaction." + ADDED_IN_313, required=True
    )
    message = graphene.String(
        description="Message related to the transaction." + ADDED_IN_313, required=True
    )

    psp_reference = graphene.String(
        description="PSP reference of transaction." + ADDED_IN_313, required=True
    )
    order = graphene.Field(
        "saleor.graphql.order.types.Order",
        description="The related order." + ADDED_IN_36,
    )
    events = NonNullList(
        TransactionEvent, required=True, description="List of all transaction's events."
    )
    created_by = graphene.Field(
        "saleor.graphql.core.types.user_or_app.UserOrApp",
        description=("User or App that created the transaction." + ADDED_IN_313),
    )
    external_url = graphene.String(
        description=(
            "The url that will allow to redirect user to "
            "payment provider page with transaction details." + ADDED_IN_313
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
    def resolve_id(root: models.TransactionItem, _info: ResolveInfo):
        return root.token

    @staticmethod
    def resolve_actions(root: models.TransactionItem, _info):
        return root.available_actions

    @staticmethod
    def resolve_charged_amount(root: models.TransactionItem, _info):
        return root.amount_charged

    @staticmethod
    def resolve_charge_pending_amount(root: models.TransactionItem, _info):
        return root.amount_charge_pending

    @staticmethod
    def resolve_authorized_amount(root: models.TransactionItem, _info):
        return root.amount_authorized

    @staticmethod
    def resolve_authorize_pending_amount(root: models.TransactionItem, _info):
        return root.amount_authorize_pending

    @staticmethod
    def resolve_canceled_amount(root: models.TransactionItem, _info):
        return root.amount_canceled

    @staticmethod
    def resolve_cancel_pending_amount(root: models.TransactionItem, _info):
        return root.amount_cancel_pending

    @staticmethod
    def resolve_refunded_amount(root: models.TransactionItem, _info):
        return root.amount_refunded

    @staticmethod
    def resolve_refund_pending_amount(root: models.TransactionItem, _info):
        return root.amount_refund_pending

    @staticmethod
    def resolve_order(root: models.TransactionItem, info):
        if not root.order_id:
            return
        return OrderByIdLoader(info.context).load(root.order_id)

    @staticmethod
    def resolve_events(root: models.TransactionItem, info):
        return TransactionEventByTransactionIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_created_by(root: models.TransactionItem, info):
        """Resolve createdBy.

        Try to fetch the app by db relation first. This cover all apps created manually
        by staff user and the third-party app that was not re-installed.
        If the root.app_id is none, we're trying to fetch the app by `app.identifier`.
        This covers a case when a third-party app was re-installed, but we're still able
        to determine which one is the owner of the transaction.
        """

        if root.app_id:
            return AppByIdLoader(info.context).load(root.app_id)
        if root.app_identifier:

            def get_first_app(apps):
                if apps:
                    return apps[0]
                return None

            return (
                AppsByAppIdentifierLoader(info.context)
                .load(root.app_identifier)
                .then(get_first_app)
            )
        if root.user_id:
            return UserByUserIdLoader(info.context).load(root.user_id)
        return None

    @staticmethod
    def resolve_psp_reference(root: models.TransactionItem, info):
        return root.psp_reference or ""

    @staticmethod
    def resolve_external_url(root: models.TransactionItem, info):
        return root.external_url or ""

    @staticmethod
    def resolve_type(root: models.TransactionItem, info) -> str:
        return root.name or ""

    @staticmethod
    def resolve_name(root: models.TransactionItem, info) -> str:
        return root.name or ""

    @staticmethod
    def resolve_message(root: models.TransactionItem, info) -> str:
        return root.message or ""

    @classmethod
    def get_node(cls, _: Any, id: str) -> Optional[models.TransactionItem]:
        model = cls._meta.model
        lookup = Q(token=id)
        try:
            UUID(str(id))
        except ValueError:
            lookup = Q(pk=id) & Q(use_old_id=True)

        try:
            return model.objects.get(lookup)
        except model.DoesNotExist:
            return None


class GatewayConfigLine(BaseObjectType):
    field = graphene.String(required=True, description="Gateway config key.")
    value = graphene.String(description="Gateway config value for key.")

    class Meta:
        description = "Payment gateway client configuration key and value pair."
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentGateway(BaseObjectType):
    name = graphene.String(required=True, description="Payment gateway name.")
    id = graphene.ID(required=True, description="Payment gateway ID.")
    config = NonNullList(
        GatewayConfigLine,
        required=True,
        description="Payment gateway client configuration.",
    )
    currencies = NonNullList(
        graphene.String,
        required=True,
        description="Payment gateway supported currencies.",
    )

    class Meta:
        description = (
            "Available payment gateway backend with configuration "
            "necessary to setup client."
        )
        doc_category = DOC_CATEGORY_PAYMENTS


class StoredPaymentMethod(BaseObjectType):
    id = graphene.ID(required=True, description="Stored payment method ID.")

    gateway = graphene.Field(
        PaymentGateway,
        required=True,
        description="Payment gateway that stores this payment method.",
    )
    payment_method_id = graphene.String(
        description=(
            "ID of stored payment method used to make payment actions. "
            "Note: method ID is unique only within the payment gateway."
        ),
        required=True,
    )

    credit_card_info = graphene.Field(
        CreditCard,
        required=False,
        description="Stored credit card details if available.",
    )

    supported_payment_flows = graphene.Field(NonNullList(TokenizedPaymentFlowEnum))

    type = graphene.String(
        required=True,
        description="Type of the payment method. Example: credit card, wallet, etc.",
    )
    name = graphene.String(
        description=(
            "Payment method name. Example: last 4 digits of credit card, obfuscated "
            "email, etc."
        )
    )
    data = graphene.Field(
        JSON,
        description=(
            "JSON data returned by Payment Provider app for this payment method."
        ),
    )

    class Meta:
        description = (
            "Represents a payment method stored for user (tokenized) in payment "
            "gateway." + ADDED_IN_315 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS

    @staticmethod
    def resolve_payment_method_id(root: PaymentMethodData, _info: ResolveInfo):
        return root.external_id
