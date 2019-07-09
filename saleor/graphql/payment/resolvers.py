from itertools import chain

import graphene_django_optimizer as gql_optimizer

from ...payment import models
from ...payment.interface import TokenConfig
from ...payment.utils import (
    fetch_customer_id,
    gateway_get_client_token,
    list_enabled_gateways,
    retrieve_customer_sources,
)
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


def resolve_payment_sources(user):
    stored_customer_accounts = {
        gateway: fetch_customer_id(user, gateway) for gateway in list_enabled_gateways()
    }
    return list(
        chain(
            *[
                prepare_graphql_payment_sources_type(
                    retrieve_customer_sources(gateway, customer_id)
                )
                for gateway, customer_id in stored_customer_accounts.items()
                if customer_id is not None
            ]
        )
    )


def prepare_graphql_payment_sources_type(payment_sources):
    sources = []
    for src in payment_sources:
        sources.append(
            {
                "gateway": src.gateway,
                "credit_card_info": {
                    "last_digits": src.credit_card_info.last_4,
                    "exp_year": src.credit_card_info.exp_year,
                    "exp_month": src.credit_card_info.exp_month,
                    "brand": "",
                    "first_digits": "",
                },
            }
        )
    return sources
