from django.contrib.auth import models as auth_models
from graphql_jwt.decorators import staff_member_required, permission_required

from ...account import models
from ..utils import filter_by_query_param, get_node
from .types import User


CUSTOMER_SEARCH_FIELDS = (
    'email', 'default_shipping_address__first_name',
    'default_shipping_address__last_name', 'default_shipping_address__city',
    'default_shipping_address__country')

STAFF_SEARCH_FIELDS = ('email',)

GROUP_SEARCH_FIELDS = ('name', )


# @staff_member_required
def resolve_staff_users(info, query):
    qs = models.User.objects.staff()
    return filter_by_query_param(qs, query, STAFF_SEARCH_FIELDS)


@staff_member_required
def resolve_staff_user(info, id):
    # FIXME: lookup node in staff users only
    return get_node(info, id, only_type=User)


@permission_required(['account.view_user', 'account.edit_user'])
def resolve_customers(info, query):
    qs = models.User.objects.customers().prefetch_related('addresses')
    return filter_by_query_param(
        queryset=qs, query=query, search_fields=CUSTOMER_SEARCH_FIELDS)


@permission_required(['account.view_user', 'account.edit_user'])
def resolve_customer(info, id):
    # FIXME: lookup node in customers only
    return get_node(info, id, only_type=User)


@staff_member_required
def resolve_groups(info, query):
    qs = auth_models.Group.objects.prefetch_related('permissions')
    return filter_by_query_param(qs, query, GROUP_SEARCH_FIELDS)
