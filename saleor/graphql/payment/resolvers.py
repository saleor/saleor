from graphql_jwt.decorators import login_required

from ...payment import models
from ...payment.utils import gateway_get_client_token
from ..utils import filter_by_query_param

PAYMENT_SEARCH_FIELDS = ['id']


# @login_required
def resolve_payment_methods(info, query):
    queryset = models.PaymentMethod.objects.all().distinct()
    queryset = filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
    return queryset


def resolve_payment_client_token(gateway=None):
    return gateway_get_client_token(gateway)
