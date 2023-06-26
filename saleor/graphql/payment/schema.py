import graphene

from ...permission.enums import OrderPermissions, PaymentPermissions
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_36, PREVIEW_FEATURE
from ..core.doc_category import DOC_CATEGORY_PAYMENTS
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.utils import from_global_id_or_error
from .filters import PaymentFilterInput
from .mutations import (
    PaymentCapture,
    PaymentCheckBalance,
    PaymentGatewayInitialize,
    PaymentInitialize,
    PaymentRefund,
    PaymentVoid,
    TransactionCreate,
    TransactionEventReport,
    TransactionInitialize,
    TransactionProcess,
    TransactionRequestAction,
    TransactionRequestRefundForGrantedRefund,
    TransactionUpdate,
)
from .resolvers import resolve_payment_by_id, resolve_payments, resolve_transaction
from .types import Payment, PaymentCountableConnection, TransactionItem


class PaymentQueries(graphene.ObjectType):
    payment = PermissionsField(
        Payment,
        description="Look up a payment by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the payment.", required=True
        ),
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
        doc_category=DOC_CATEGORY_PAYMENTS,
    )
    payments = FilterConnectionField(
        PaymentCountableConnection,
        filter=PaymentFilterInput(description="Filtering options for payments."),
        description="List of payments.",
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
        doc_category=DOC_CATEGORY_PAYMENTS,
    )
    transaction = PermissionsField(
        TransactionItem,
        description="Look up a transaction by ID." + ADDED_IN_36 + PREVIEW_FEATURE,
        id=graphene.Argument(
            graphene.ID, description="ID of a transaction.", required=True
        ),
        permissions=[
            PaymentPermissions.HANDLE_PAYMENTS,
        ],
        doc_category=DOC_CATEGORY_PAYMENTS,
    )

    @staticmethod
    def resolve_payment(_root, _info: ResolveInfo, **data):
        _, id = from_global_id_or_error(data["id"], Payment)
        return resolve_payment_by_id(id)

    @staticmethod
    def resolve_payments(_root, info: ResolveInfo, **kwargs):
        qs = resolve_payments(info)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, PaymentCountableConnection)

    @staticmethod
    def resolve_transaction(_root, info: ResolveInfo, **kwargs):
        _, id = from_global_id_or_error(kwargs["id"], TransactionItem)
        if not id:
            return None
        return resolve_transaction(id)


class PaymentMutations(graphene.ObjectType):
    payment_capture = PaymentCapture.Field()
    payment_refund = PaymentRefund.Field()
    payment_void = PaymentVoid.Field()
    payment_initialize = PaymentInitialize.Field()
    payment_check_balance = PaymentCheckBalance.Field()

    transaction_create = TransactionCreate.Field()
    transaction_update = TransactionUpdate.Field()
    transaction_request_action = TransactionRequestAction.Field()
    transaction_request_refund_for_granted_refund = (
        TransactionRequestRefundForGrantedRefund.Field()
    )
    transaction_event_report = TransactionEventReport.Field()

    payment_gateway_initialize = PaymentGatewayInitialize.Field()
    transaction_initialize = TransactionInitialize.Field()
    transaction_process = TransactionProcess.Field()
