import graphene

from ...core.permissions import OrderPermissions
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.fields import FilterConnectionField
from ..core.utils import from_global_id_or_error
from ..decorators import permission_required
from .filters import PaymentFilterInput
from .mutations import (
    PaymentCapture,
    PaymentCheckBalance,
    PaymentInitialize,
    PaymentRefund,
    PaymentVoid,
)
from .resolvers import resolve_payment_by_id, resolve_payments
from .types import Payment, PaymentCountableConnection


class PaymentQueries(graphene.ObjectType):
    payment = graphene.Field(
        Payment,
        description="Look up a payment by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the payment.", required=True
        ),
    )
    payments = FilterConnectionField(
        PaymentCountableConnection,
        filter=PaymentFilterInput(description="Filtering options for payments."),
        description="List of payments.",
    )

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_payment(self, info, **data):
        _, id = from_global_id_or_error(data["id"], Payment)
        return resolve_payment_by_id(id)

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_payments(self, info, **kwargs):
        qs = resolve_payments(info)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, PaymentCountableConnection)


class PaymentMutations(graphene.ObjectType):
    payment_capture = PaymentCapture.Field()
    payment_refund = PaymentRefund.Field()
    payment_void = PaymentVoid.Field()
    payment_initialize = PaymentInitialize.Field()
    payment_check_balance = PaymentCheckBalance.Field()
