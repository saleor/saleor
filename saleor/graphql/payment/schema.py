import graphene

from ...core.permissions import OrderPermissions
from ..core.fields import PrefetchingConnectionField
from ..decorators import permission_required
from .mutations import PaymentCapture, PaymentInitialize, PaymentRefund, PaymentVoid
from .resolvers import resolve_payments, resolve_client_token
from .types import Payment, PaymentClientToken


class PaymentQueries(graphene.ObjectType):
    payment = graphene.Field(
        Payment,
        description="Look up a payment by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the payment.", required=True
        ),
    )
    payments = PrefetchingConnectionField(Payment, description="List of payments.")
    payment_client_token = graphene.Field(
        PaymentClientToken,
        args={'gateway': graphene.String()},
        required=True
    )

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_payment(self, info, **data):
        return graphene.Node.get_node_from_global_id(info, data.get("id"), Payment)

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_payments(self, info, query=None, **_kwargs):
        return resolve_payments(info, query)

    def resolve_payment_client_token(self, info, gateway=None):
        user = info.context.user if info.context.user.is_authenticated else None
        return resolve_client_token(user=user, gateway=gateway)


class PaymentMutations(graphene.ObjectType):
    payment_capture = PaymentCapture.Field()
    payment_refund = PaymentRefund.Field()
    payment_void = PaymentVoid.Field()
    payment_initialize = PaymentInitialize.Field()
