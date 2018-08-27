from ...account import models
from ..utils import filter_by_query_param

USER_SEARCH_FIELDS = (
    'email', 'default_shipping_address__first_name',
    'default_shipping_address__last_name', 'default_shipping_address__city',
    'default_shipping_address__country')


def resolve_users(info, query):
    qs = models.User.objects.all().prefetch_related('addresses')
    return filter_by_query_param(
        queryset=qs, query=query, search_fields=USER_SEARCH_FIELDS)
