from graphql_jwt.decorators import login_required

from ...order import models
from ...payment.utils import gateway_get_client_token
from ..utils import filter_by_query_param, get_node
from .types import Payment

PAYMENT_SEARCH_FIELDS = ['id']

# @login_required
def resolve_payments(info, query):
    queryset = models.Payment.objects.all().distinct()
    queryset = filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
    return queryset


# @login_required
def resolve_payment(info, id):
    payment = get_node(info, id, only_type=Payment)
    return payment


def resolve_payment_client_token(gateway=None):
    return gateway_get_client_token(gateway)
