import graphene

from ...payment import gateway as payment_gateway
from ...payment import models
from ...payment.utils import fetch_customer_id
from ..utils.filters import filter_by_query_param

PAYMENT_SEARCH_FIELDS = ["id"]


def resolve_client_token(user, gateway: str):
    gateway_customer_id = fetch_customer_id(user, gateway)
    customer_id = gateway_customer_id if gateway_customer_id else graphene.Node.to_global_id(
        "User", user.id) if user.id else None
    return {'clientToken': payment_gateway.get_client_token(gateway, customer_id)}


def resolve_payments(info, query):
    queryset = models.Payment.objects.all().distinct()
    return filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
