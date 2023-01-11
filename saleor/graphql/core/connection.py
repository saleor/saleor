import json
from decimal import Decimal, InvalidOperation
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)

import graphene
from django.conf import settings
from django.db.models import Model as DjangoModel
from django.db.models import Q, QuerySet
from graphene.relay import Connection
from graphql import GraphQLError
from graphql.language.ast import FragmentSpread
from graphql_relay.connection.arrayconnection import connection_from_list_slice
from graphql_relay.connection.connectiontypes import Edge, PageInfo
from graphql_relay.utils import base64, unbase64

from ...channel.exceptions import ChannelNotDefined, NoDefaultChannel
from ..channel import ChannelContext, ChannelQsContext
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..core.enums import OrderDirection
from ..core.types import NonNullList
from ..utils.sorting import sort_queryset_for_connection

if TYPE_CHECKING:
    from ..core import ResolveInfo

ConnectionArguments = Dict[str, Any]

EPSILON = Decimal("0.000001")
FILTERS_NAME = "_FILTERS_NAME"
FILTERSET_CLASS = "_FILTERSET_CLASS"


def to_global_cursor(values):
    if not isinstance(values, Iterable):
        values = [values]
    values = [value if value is None else str(value) for value in values]
    return base64(json.dumps(values))


def from_global_cursor(cursor) -> List[str]:
    values = unbase64(cursor)
    return json.loads(values)


def get_field_value(instance: DjangoModel, field_name: str):
    """Get field value for given field in filter format 'field__foreign_key_field'."""
    field_path = field_name.split("__")
    attr = instance
    for elem in field_path:
        attr = getattr(attr, elem, None)  # type:ignore

    if callable(attr):
        return f"{attr()}"
    return attr


def _prepare_filter_by_rank_expression(
    cursor: List[str],
    sorting_direction: str,
    coerce_id: Callable[[str], Any],
) -> Q:
    if len(cursor) != 2:
        raise GraphQLError("Received cursor is invalid.")
    try:
        rank = Decimal(cursor[0])
        id = coerce_id(cursor[1])
    except (InvalidOperation, ValueError, TypeError):
        raise GraphQLError("Received cursor is invalid.")

    # Because rank is float number, it gets mangled by PostgreSQL's query parser
    # making equal comparisons impossible. Instead we compare rank against small
    # range of values, constructed using epsilon.
    if sorting_direction == "gt":
        return Q(search_rank__range=(rank - EPSILON, rank + EPSILON), id__lt=id) | Q(
            search_rank__gt=rank + EPSILON
        )
    return Q(search_rank__range=(rank - EPSILON, rank + EPSILON), id__gt=id) | Q(
        search_rank__lt=rank - EPSILON
    )


def _prepare_filter_expression(
    field_name: str,
    index: int,
    cursor: List[str],
    sorting_fields: List[str],
    sorting_direction: str,
) -> Tuple[Q, Dict[str, Union[str, bool]]]:

    field_expression: Dict[str, Union[str, bool]] = {}
    extra_expression = Q()
    for cursor_id, cursor_value in enumerate(cursor[:index]):
        field_expression[sorting_fields[cursor_id]] = cursor_value

    if sorting_direction == "gt":
        extra_expression |= Q(**{f"{field_name}__{sorting_direction}": cursor[index]})
        extra_expression |= Q(**{f"{field_name}__isnull": True})
    elif cursor[index] is not None:
        field_expression[f"{field_name}__{sorting_direction}"] = cursor[index]
    else:
        field_expression[f"{field_name}__isnull"] = False

    return extra_expression, field_expression


def _prepare_filter(
    cursor: List[str],
    sorting_fields: List[str],
    sorting_direction: str,
    coerce_id: Callable[[str], Any],
) -> Q:
    """Create filter arguments based on sorting fields.

    :param cursor: list of values that are passed from page_info, used for filtering.
    :param sorting_fields: list of fields that were used for sorting.
    :param sorting_direction: keyword direction ('lt', gt').
    :return: Q() in following format
        (OR: ('first_field__gt', 'first_value_form_cursor'),
            (AND: ('second_field__gt', 'second_value_form_cursor'),
                ('first_field', 'first_value_form_cursor')),
            (AND: ('third_field__gt', 'third_value_form_cursor'),
                ('second_field', 'second_value_form_cursor'),
                ('first_field', 'first_value_form_cursor'))
        )
    """
    if sorting_fields == ["search_rank", "id"]:
        # Fast path for filtering by rank
        return _prepare_filter_by_rank_expression(cursor, sorting_direction, coerce_id)
    filter_kwargs = Q()
    for index, field_name in enumerate(sorting_fields):
        if cursor[index] is None and sorting_direction == "gt":
            continue

        extra_expression, field_expression = _prepare_filter_expression(
            field_name, index, cursor, sorting_fields, sorting_direction
        )
        filter_kwargs |= Q(extra_expression, **field_expression)

    return filter_kwargs


def _validate_connection_args(args):
    first = args.get("first")
    last = args.get("last")

    if first and not (isinstance(first, int) and first > 0):
        raise GraphQLError("Argument `first` must be a non-negative integer.")
    if last and not (isinstance(last, int) and last > 0):
        raise GraphQLError("Argument `last` must be a non-negative integer.")
    if first and last:
        raise GraphQLError("Argument `last` cannot be combined with `first`.")
    if first and args.get("before"):
        raise GraphQLError("Argument `first` cannot be combined with `before`.")
    if last and args.get("after"):
        raise GraphQLError("Argument `last` cannot be combined with `after`.")


def _get_sorting_fields(sort_by, qs):
    sorting_fields = sort_by.get("field")
    sorting_attribute = sort_by.get("attribute_id")
    if sorting_fields and not isinstance(sorting_fields, list):
        return [sorting_fields]
    elif not sorting_fields and sorting_attribute is not None:
        return qs.model.sort_by_attribute_fields()
    elif not sorting_fields:
        raise ValueError("Error while preparing cursor values.")
    return sorting_fields


def _get_sorting_direction(sort_by, last=None):
    direction = sort_by.get("direction", "")
    sorting_desc = direction == OrderDirection.DESC
    if last:
        sorting_desc = not sorting_desc
    return "lt" if sorting_desc else "gt"


def _get_page_info(matching_records, cursor, first, last):
    requested_count = first or last
    page_info = {
        "has_previous_page": False,
        "has_next_page": False,
        "start_cursor": None,
        "end_cursor": None,
    }
    records_left = False
    if requested_count is not None:
        records_left = len(matching_records) > requested_count
    has_other_pages = bool(cursor)
    if first:
        page_info["has_next_page"] = records_left
        page_info["has_previous_page"] = has_other_pages
    elif last:
        page_info["has_next_page"] = has_other_pages
        page_info["has_previous_page"] = records_left

    return page_info


def _get_edges_for_connection(edge_type, qs, args, sorting_fields):
    before = args.get("before")
    after = args.get("after")
    first = args.get("first")
    last = args.get("last")
    cursor = after or before
    requested_count = first or last

    # If we don't receive `first` and `last` we shouldn't build `edges` and `page_info`
    if not first and not last:
        return [], {"has_previous_page": False, "has_next_page": False}

    if last:
        start_slice, end_slice = 1, None
    else:
        start_slice, end_slice = 0, requested_count

    matching_records = list(qs)
    if last:
        matching_records = list(reversed(matching_records))
        if len(matching_records) <= requested_count:
            start_slice = 0
    page_info = _get_page_info(matching_records, cursor, first, last)
    matching_records = matching_records[start_slice:end_slice]

    edges = [
        edge_type(
            node=record,
            cursor=to_global_cursor(
                [get_field_value(record, field) for field in sorting_fields]
            ),
        )
        for record in matching_records
    ]
    if edges:
        page_info["start_cursor"] = edges[0].cursor
        page_info["end_cursor"] = edges[-1].cursor
    return edges, page_info


def _get_id_coercion(qs: QuerySet) -> Callable[[str], Any]:
    return qs.model.id.field.to_python if hasattr(qs.model, "id") else int


def connection_from_queryset_slice(
    qs: QuerySet,
    args: Optional[ConnectionArguments] = None,
    connection_type: Any = Connection,
    edge_type: Any = Edge,
    pageinfo_type: Any = PageInfo,
) -> Connection:
    """Create a connection object from a QuerySet."""
    args = args or {}
    before = args.get("before")
    after = args.get("after")
    first = args.get("first")
    last = args.get("last")
    _validate_connection_args(args)

    requested_count = first or last
    end_margin = requested_count + 1 if requested_count else None

    cursor = after or before
    try:
        cursor = from_global_cursor(cursor) if cursor else None
    except ValueError:
        raise GraphQLError("Received cursor is invalid.")

    sort_by = args.get("sort_by", {})
    sorting_fields = _get_sorting_fields(sort_by, qs)
    sorting_direction = _get_sorting_direction(sort_by, last)
    if cursor and len(cursor) != len(sorting_fields):
        raise GraphQLError("Received cursor is invalid.")
    filter_kwargs = (
        _prepare_filter(
            cursor,
            sorting_fields,
            sorting_direction,
            _get_id_coercion(qs),
        )
        if cursor
        else Q()
    )
    try:
        filtered_qs = qs.filter(filter_kwargs)
    except ValueError:
        raise GraphQLError("Received cursor is invalid.")
    filtered_qs = filtered_qs[:end_margin]
    edges, page_info = _get_edges_for_connection(
        edge_type, filtered_qs, args, sorting_fields
    )

    if "total_count" in connection_type._meta.fields:

        def get_total_count():
            return qs.count()

        return connection_type(
            edges=edges,
            page_info=pageinfo_type(**page_info),
            total_count=get_total_count,
        )

    return connection_type(
        edges=edges,
        page_info=pageinfo_type(**page_info),
    )


def create_connection_slice(
    iterable,
    info: "ResolveInfo",
    args,
    connection_type,
    edge_type=None,
    pageinfo_type=graphene.relay.PageInfo,
    max_limit: Optional[int] = None,
):
    _validate_slice_args(info, args, max_limit)

    if isinstance(iterable, list):
        return slice_connection_iterable(
            iterable,
            args,
            connection_type,
            edge_type,
            pageinfo_type,
        )

    if isinstance(iterable, ChannelQsContext):
        queryset = iterable.qs
    else:
        queryset = iterable

    queryset, sort_by = sort_queryset_for_connection(iterable=queryset, args=args)
    args["sort_by"] = sort_by

    slice = connection_from_queryset_slice(
        queryset,
        args,
        connection_type,
        edge_type or connection_type.Edge,
        pageinfo_type or graphene.relay.PageInfo,
    )

    if isinstance(iterable, ChannelQsContext):
        edges_with_context = []
        for edge in slice.edges:
            node = edge.node
            edge.node = ChannelContext(node=node, channel_slug=iterable.channel_slug)
            edges_with_context.append(edge)
        slice.edges = edges_with_context

    return slice


def _validate_slice_args(
    info: "ResolveInfo",
    args: dict,
    max_limit: Optional[int] = None,
):
    enforce_first_or_last = _is_first_or_last_required(info)

    first = args.get("first")
    last = args.get("last")

    if enforce_first_or_last and not (first or last):
        raise GraphQLError(
            f"You must provide a `first` or `last` value to properly paginate "
            f"the `{info.field_name}` connection."
        )

    if max_limit is None:
        max_limit = settings.GRAPHQL_PAGINATION_LIMIT

    if max_limit:
        if first:
            assert first <= max_limit, (
                "Requesting {} records on the `{}` connection exceeds the "
                "`first` limit of {} records."
            ).format(first, info.field_name, max_limit)
            args["first"] = min(first, max_limit)

        if last:
            assert last <= max_limit, (
                "Requesting {} records on the `{}` connection exceeds the "
                "`last` limit of {} records."
            ).format(last, info.field_name, max_limit)
            args["last"] = min(last, max_limit)


def _is_first_or_last_required(info):
    """Disable `enforce_first_or_last` if not querying for `edges`."""
    selections = info.field_asts[0].selection_set.selections
    values = [field.name.value for field in selections]
    if "edges" in values:
        return True

    fragments = [
        field.name.value for field in selections if isinstance(field, FragmentSpread)
    ]

    for fragment in fragments:
        fragment_values = [
            field.name.value
            for field in info.fragments[fragment].selection_set.selections
        ]
        if "edges" in fragment_values:
            return True

    return False


def slice_connection_iterable(
    iterable,
    args,
    connection_type,
    edge_type=None,
    pageinfo_type=None,
):
    _len = len(iterable)

    slice = connection_from_list_slice(
        iterable,
        args,
        slice_start=0,
        list_length=_len,
        list_slice_length=_len,
        connection_type=connection_type,
        edge_type=edge_type or connection_type.Edge,
        pageinfo_type=pageinfo_type or graphene.relay.PageInfo,
    )

    if "total_count" in connection_type._meta.fields:
        slice.total_count = _len

    return slice


def filter_connection_queryset(iterable, args, request=None, root=None):
    filterset_class = args[FILTERSET_CLASS]
    filter_field_name = args[FILTERS_NAME]
    filter_input = args.get(filter_field_name)

    if filter_input:
        # for nested filters get channel from ChannelContext object
        if "channel" not in args and root and hasattr(root, "channel_slug"):
            args["channel"] = root.channel_slug

        try:
            filter_channel = str(filter_input["channel"])
        except (NoDefaultChannel, ChannelNotDefined, GraphQLError, KeyError):
            filter_channel = None
        filter_input["channel"] = (
            args.get("channel")
            or filter_channel
            or get_default_channel_slug_or_graphql_error()
        )

        if isinstance(iterable, ChannelQsContext):
            queryset = iterable.qs
        else:
            queryset = iterable

        filterset = filterset_class(filter_input, queryset=queryset, request=request)
        if not filterset.is_valid():
            raise GraphQLError(json.dumps(filterset.errors.get_json_data()))

        if isinstance(iterable, ChannelQsContext):
            return ChannelQsContext(filterset.qs, iterable.channel_slug)

        return filterset.qs

    return iterable


class NonNullConnection(Connection):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        super().__init_subclass_with_meta__(node=node, name=name, **options)

        # Override the original EdgeBase type to make to `node` field required.
        class EdgeBase:
            node = graphene.Field(
                cls._meta.node,
                description="The item at the end of the edge.",
                required=True,
            )
            cursor = graphene.String(
                required=True, description="A cursor for use in pagination."
            )

        # Create the edge type using the new EdgeBase.
        edge_name = cls.Edge._meta.name
        edge_bases = (EdgeBase, graphene.ObjectType)
        edge = type(edge_name, edge_bases, {})
        cls.Edge = edge

        # Override the `edges` field to make it non-null list
        # of non-null edges.
        cls._meta.fields["edges"] = graphene.Field(
            graphene.NonNull(NonNullList(cls.Edge))
        )


class CountableConnection(NonNullConnection):
    class Meta:
        abstract = True

    total_count = graphene.Int(description="A total count of items in the collection.")

    @staticmethod
    def resolve_total_count(root, _info):
        try:
            if isinstance(root, dict):
                total_count = root["total_count"]
            else:
                total_count = root.total_count
        except (AttributeError, KeyError):
            return None

        if callable(total_count):
            return total_count()

        return total_count
