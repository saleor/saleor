import graphene
from django.db.models import Q
from django.utils import timezone
from graphene_django.registry import get_global_registry
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from .core.enums import PermissionEnum, ReportingPeriod
from .core.types import PermissionDisplay

ERROR_COULD_NO_RESOLVE_GLOBAL_ID = (
    'Could not resolve to a node with the global id list of \'%s\'.')
registry = get_global_registry()


def get_database_id(info, node_id, only_type):
    """Get a database ID from a node ID of given type."""
    _type, _id = graphene.relay.Node.from_global_id(node_id)
    graphene_type = info.schema.get_type(_type).graphene_type
    if graphene_type != only_type:
        raise AssertionError('Must receive a %s id.' % only_type._meta.name)
    return _id


def _check_graphene_type(requested_graphene_type, received_type):
    if requested_graphene_type:
        assert str(requested_graphene_type) == received_type, (
            'Must receive an {} id.'
        ).format(str(requested_graphene_type))


def _resolve_nodes(ids, graphene_type=None):
    pks = []
    invalid_ids = []
    used_type = graphene_type

    for graphql_id in ids:
        if not graphql_id:
            continue

        try:
            node_type, _id = from_global_id(graphql_id)
        except Exception:
            invalid_ids.append(graphql_id)
            continue

        _check_graphene_type(used_type, node_type)
        used_type = node_type
        pks.append(_id)

    if invalid_ids:
        raise GraphQLError(
            ERROR_COULD_NO_RESOLVE_GLOBAL_ID % invalid_ids)

    return used_type, pks


def _resolve_graphene_type(type_name):
    for _, _type in registry._registry.items():
        if _type._meta.name == type_name:
            return _type
    raise AssertionError('Could not resolve the type {}'.format(type_name))


def get_nodes(ids, graphene_type=None):
    """Return a list of nodes.

    If the `graphene_type` argument is provided, the IDs will be validated
    against this type. If the type was not provided, it will be looked up in
    the Graphene's registry. Raises an error if not all IDs are of the same
    type.
    """
    nodes_type, pks = _resolve_nodes(ids, graphene_type)

    # If `graphene_type` was not provided, check if all resolved types are
    # the same. This prevents from accidentally mismatching IDs of different
    # types.
    if nodes_type and not graphene_type:
        graphene_type = _resolve_graphene_type(nodes_type)

    nodes = list(graphene_type._meta.model.objects.filter(pk__in=pks))
    nodes.sort(key=lambda e: pks.index(str(e.pk)))  # preserve order in pks

    if not nodes:
        raise GraphQLError(
            ERROR_COULD_NO_RESOLVE_GLOBAL_ID % ids)

    nodes_pk_list = [str(node.pk) for node in nodes]
    for pk in pks:
        assert pk in nodes_pk_list, (
            'There is no node of type {} with pk {}'.format(graphene_type, pk))
    return nodes


def filter_by_query_param(queryset, query, search_fields):
    """Filter queryset according to given parameters.

    Keyword arguments:
    queryset - queryset to be filtered
    query - search string
    search_fields - fields considered in filtering
    """
    if query:
        query_by = {
            '{0}__{1}'.format(
                field, 'icontains'): query for field in search_fields}
        query_objects = Q()
        for q in query_by:
            query_objects |= Q(**{q: query_by[q]})
        return queryset.filter(query_objects).distinct()
    return queryset


def reporting_period_to_date(period):
    now = timezone.now()
    if period == ReportingPeriod.TODAY:
        start_date = now.replace(
            hour=0, minute=0, second=0, microsecond=0)
    elif period == ReportingPeriod.THIS_MONTH:
        start_date = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError('Unknown period: %s' % period)
    return start_date


def filter_by_period(queryset, period, field_name):
    start_date = reporting_period_to_date(period)
    return queryset.filter(**{'%s__gte' % field_name: start_date})


def generate_query_argument_description(search_fields):
    header = 'Supported filter parameters:\n'
    supported_list = ''
    for field in search_fields:
        supported_list += '* {0}\n'.format(field)
    return header + supported_list


def format_permissions_for_display(permissions):
    """Transform permissions queryset into PermissionDisplay list.

    Keyword arguments:
    permissions - queryset with permissions
    """
    formatted_permissions = []
    for permission in permissions:
        codename = '.'.join(
            [permission.content_type.app_label, permission.codename])
        formatted_permissions.append(
            PermissionDisplay(
                code=PermissionEnum.get(codename),
                name=permission.name))
    return formatted_permissions
