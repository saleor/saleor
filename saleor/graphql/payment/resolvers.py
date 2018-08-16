from graphql_jwt.decorators import login_required

from ...order import models
from ..utils import filter_by_query_param, get_node
from .types import Payment
from ...payments import braintree

PAYMENT_SEARCH_FIELDS = ['id']

# @login_required
def resolve_payments(info, query):
    queryset = models.Payment.objects.all().distinct()
    # if user.get_all_permissions() & {'order.manage_orders'}:
        # queryset = models.Order.objects.all().distinct()
    queryset = filter_by_query_param(queryset, query, PAYMENT_SEARCH_FIELDS)
    return queryset


# @login_required
def resolve_payment(info, id):
    payment = get_node(info, id, only_type=Payment)
    return payment


def resolve_payment_client_token(customer_id=None):
    return braintree.create_client_token(customer_id=customer_id)
