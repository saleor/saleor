import graphene

from ...permission.enums import OrderPermissions, PaymentPermissions
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_36, PREVIEW_FEATURE
from ..core.doc_category import DOC_CATEGORY_PAYMENTS
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.scalars import UUID
from ..core.utils import from_global_id_or_error
from .filters import PaymentFilterInput
from .mutations import (
    PaymentCapture,
    PaymentCheckBalance,
    PaymentGatewayInitialize,
    PaymentGatewayInitializeTokenization,
    PaymentInitialize,
    PaymentMethodInitializeTokenization,
    PaymentMethodProcessTokenization,
    PaymentRefund,
    PaymentVoid,
    StoredPaymentMethodRequestDelete,
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
            graphene.ID,
            description=(
                "ID of a transaction. Either it or token is required "
                "to fetch the transaction data."
            ),
            required=False,
        ),
        token=graphene.Argument(
            UUID,
            description=(
                "Token of a transaction. Either it or ID is required "
                "to fetch the transaction data."
            ),
            required=False,
        ),
        permissions=[
            PaymentPermissions.HANDLE_PAYMENTS,
        ],
        doc_category=DOC_CATEGORY_PAYMENTS,
    )

    @staticmethod
    def resolve_payment(_root, info: ResolveInfo, **data):
        _, id = from_global_id_or_error(data["id"], Payment)
        return resolve_payment_by_id(info, id)

    @staticmethod
    def resolve_payments(_root, info: ResolveInfo, **kwargs):
        qs = resolve_payments(info)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, PaymentCountableConnection)

    @staticmethod
    def resolve_transaction(_root, info: ResolveInfo, **kwargs):
        id = kwargs.get("id")
        token = kwargs.get("token")
        if id is None and token is None:
            return None
        # If token is provided we ignore the id input.
        if token:
            return resolve_transaction(info, str(token))
        _, id = from_global_id_or_error(
            global_id=str(id), only_type=TransactionItem, raise_error=True
        )
        return resolve_transaction(info, id)


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

    stored_payment_method_request_delete = StoredPaymentMethodRequestDelete.Field()
    payment_gateway_initialize_tokenization = (
        PaymentGatewayInitializeTokenization.Field()
    )
    payment_method_initialize_tokenization = PaymentMethodInitializeTokenization.Field()
    payment_method_process_tokenization = PaymentMethodProcessTokenization.Field()
