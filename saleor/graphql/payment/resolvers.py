from ...payment import gateway as payment_gateway, models
from ...payment.utils import fetch_customer_id
from ..utils.filters import filter_by_query_param

PAYMENT_SEARCH_FIELDS = ["id"]


def resolve_client_token(user, gateway: str):
    customer_id = fetch_customer_id(user, gateway)
    return payment_gateway.get_client_token(gateway, customer_id)


def resolve_payments(info, query):
    queryset = models.Payment.objects.all().distinct()
    return filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
