import graphene_django_optimizer as gql_optimizer

from ...payment import models
from ...payment.interface import TokenConfig
from ...payment.utils import fetch_customer_id, gateway_get_client_token
from ..utils import filter_by_query_param

PAYMENT_SEARCH_FIELDS = ["id"]


def resolve_payments(info, query):
    queryset = models.Payment.objects.all().distinct()
    queryset = filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
    return gql_optimizer.query(queryset, info)


def resolve_payment_client_token(gateway=None, user=None):
    if user is not None:
        customer_id = fetch_customer_id(user, gateway)
        if customer_id:
            token_config = TokenConfig(customer_id=customer_id)
            return gateway_get_client_token(gateway, token_config)
    return gateway_get_client_token(gateway)
