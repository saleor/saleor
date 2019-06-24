import graphene_django_optimizer as gql_optimizer

from ...payment import models
from ...payment.interface import TokenConfig
from ...payment.utils import gateway_get_client_token
from ..utils import extract_id_for_payment_gateway, filter_by_query_param

PAYMENT_SEARCH_FIELDS = ["id"]


def resolve_payments(info, query):
    queryset = models.Payment.objects.all().distinct()
    queryset = filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
    return gql_optimizer.query(queryset, info)


def resolve_payment_client_token(gateway=None, user=None):
    token_config = TokenConfig()
    if user:
        token_config.customer_id = extract_id_for_payment_gateway(user, gateway)
    return gateway_get_client_token(gateway, token_config)
