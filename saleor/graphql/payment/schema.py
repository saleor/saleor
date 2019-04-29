import graphene
from graphql_jwt.decorators import permission_required

from ..core.fields import PrefetchingConnectionField
from .enums import PaymentGatewayEnum
from .mutations import PaymentCapture, PaymentRefund, PaymentVoid
from .resolvers import resolve_payment_client_token, resolve_payments
from .types import Payment


class PaymentQueries(graphene.ObjectType):
    payment = graphene.Field(Payment, id=graphene.Argument(graphene.ID))
    payments = PrefetchingConnectionField(
        Payment, description='List of payments')
    payment_client_token = graphene.Field(
        graphene.String, args={'gateway': PaymentGatewayEnum()})

    @permission_required('order.manage_orders')
    def resolve_payment(self, info, **data):
        return graphene.Node.get_node_from_global_id(
            info, data.get('id'), Payment)

    @permission_required('order.manage_orders')
    def resolve_payments(self, info, query=None, **_kwargs):
        return resolve_payments(info, query)

    def resolve_payment_client_token(self, _info, gateway=None):
        return resolve_payment_client_token(gateway)


class PaymentMutations(graphene.ObjectType):
    payment_capture = PaymentCapture.Field()
    payment_refund = PaymentRefund.Field()
    payment_void = PaymentVoid.Field()
