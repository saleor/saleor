from graphql_jwt.decorators import login_required

from ...account import models
from ..utils import filter_by_query_param, get_node
from .types import User

USER_SEARCH_FIELDS = (
    'email', 'default_shipping_address__first_name',
    'default_shipping_address__last_name', 'default_shipping_address__city',
    'default_shipping_address__country')

@login_required
def resolve_users(info, query):
    user = info.context.user
    if user.get_all_permissions() & {'account.view_user', 'account.edit_user'}:
        qs = models.User.objects.all().prefetch_related('addresses')
        qs = filter_by_query_param(
            queryset=qs, query=query, search_fields=USER_SEARCH_FIELDS)
        return qs
    return []


@login_required
def resolve_user(info, id):
    user = get_node(info, id, only_type=User)
    requesting_user = info.context.user
    if (user == requesting_user or requesting_user.get_all_permissions() & {
            'account.view_user', 'account.edit_user'}):
        return user
    return None
