from itertools import chain

import graphene_django_optimizer as gql_optimizer

from saleor.payment import get_payment_gateway

from ...payment import models
from ...payment.interface import TokenConfig
from ...payment.utils import (
    extract_id_for_payment_gateway,
    gateway_get_client_token,
    list_enabled_gateways,
)
from ..utils import filter_by_query_param

PAYMENT_SEARCH_FIELDS = ["id"]


def resolve_payments(info, query):
    queryset = models.Payment.objects.all().distinct()
    queryset = filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
    return gql_optimizer.query(queryset, info)


def resolve_payment_client_token(gateway=None, user=None):
    token_config = TokenConfig()
    if user is not None:
        token_config.customer_id = extract_id_for_payment_gateway(user, gateway)
    return gateway_get_client_token(gateway, token_config)


def resolve_payment_sources(user):
    def retrieve_sources(gateway_name, customer_id):
        gateway, config = get_payment_gateway(gateway_name)
        return gateway.list_client_sources(config, customer_id)

    stored_customer_accounts = {
        gateway: extract_id_for_payment_gateway(user, gateway)
        for gateway in list_enabled_gateways()
    }
    return [
        chain(
            *[
                retrieve_sources(gateway, customer_id)
                for gateway, customer_id in stored_customer_accounts
                if customer_id is not None
            ]
        )
    ]
