from django.contrib.auth import models as auth_models
from graphql_jwt.decorators import permission_required, staff_member_required

from ...account import models
from ..utils import filter_by_query_param, get_node
from .types import User

USER_SEARCH_FIELDS = (
    'email', 'default_shipping_address__first_name',
    'default_shipping_address__last_name', 'default_shipping_address__city',
    'default_shipping_address__country')

GROUP_SEARCH_FIELDS = ('name', )


@permission_required(['account.view_user'])
def resolve_users(info, query):
    qs = models.User.objects.all().prefetch_related('addresses')
    return filter_by_query_param(
        queryset=qs, query=query, search_fields=USER_SEARCH_FIELDS)


@permission_required(['account.view_user'])
def resolve_user(info, id):
    return get_node(info, id, only_type=User)


@staff_member_required
def resolve_groups(info, query):
    qs = auth_models.Group.objects.prefetch_related('permissions')
    return filter_by_query_param(qs, query, GROUP_SEARCH_FIELDS)
