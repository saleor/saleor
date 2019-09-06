import graphene

from ..core.fields import PrefetchingConnectionField
from ..decorators import permission_required
from .enums import PaymentGatewayEnum
from .mutations import PaymentCapture, PaymentRefund, PaymentSecureConfirm, PaymentVoid
from .resolvers import resolve_payments
from .types import Payment


class PaymentQueries(graphene.ObjectType):
    payment = graphene.Field(Payment, id=graphene.Argument(graphene.ID))
    payments = PrefetchingConnectionField(Payment, description="List of payments")

    @permission_required("order.manage_orders")
    def resolve_payment(self, info, **data):
        return graphene.Node.get_node_from_global_id(info, data.get("id"), Payment)

    @permission_required("order.manage_orders")
    def resolve_payments(self, info, query=None, **_kwargs):
        return resolve_payments(info, query)


class PaymentMutations(graphene.ObjectType):
    payment_capture = PaymentCapture.Field()
    payment_refund = PaymentRefund.Field()
    payment_void = PaymentVoid.Field()
    payment_secure_confirm = PaymentSecureConfirm.Field()
