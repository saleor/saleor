from graphql_jwt.decorators import login_required

from ...payment import models
from ...payment.utils import gateway_get_client_token
from ..utils import filter_by_query_param, get_node
from .types import PaymentMethod

PAYMENT_SEARCH_FIELDS = ['id']

# @login_required
def resolve_payment_methods(info, query):
    queryset = models.PaymentMethod.objects.all().distinct()
    queryset = filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
    return queryset


# @login_required
def resolve_payment_method(info, id):
    payment = get_node(info, id, only_type=PaymentMethod)
    return payment


def resolve_payment_client_token(gateway=None):
    return gateway_get_client_token(gateway)
