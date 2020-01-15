from typing import Any, Dict, Union
import graphene
import opentracing as ot
from django.db.models import Manager, QuerySet
from graphene import Field, List, NonNull, ObjectType, String
from graphene.relay.connection import Connection
from graphene_django_optimizer.types import OptimizedDjangoObjectType
from graphql_relay.connection.connectiontypes import Edge, PageInfo

from ..core.enums import OrderDirection

ConnectionArguments = Dict[str, Any]


def connection_args_validation(args):
    first = args.get("first")
    last = args.get("last")

    if isinstance(first, int) and first < 0 or first and not isinstance(first, int):
        raise ValueError("Argument 'first' must be a non-negative integer.")
    if isinstance(last, int) and last < 0 or last and not isinstance(last, int):
        raise ValueError("Argument 'last' must be a non-negative integer.")
    if first and last:
        raise ValueError("Argument 'last' cannot be combined with 'first'.")
    if first and args.get("before"):
        raise ValueError("Argument 'first' cannot be combined with 'before'.")
    if last and args.get("after"):
        raise ValueError("Argument 'last' cannot be combined with 'after'.")


def connection_from_queryset_slice(
    qs: QuerySet,
    args: ConnectionArguments = None,
    connection_type: Any = Connection,
    edge_type: Any = Edge,
    page_info_type: Any = PageInfo,
) -> Connection:
    """Create a connection object from a QuerySet."""
    args = args or {}
    before = args.get("before")
    after = args.get("after")
    first = args.get("first")
    last = args.get("last")
    connection_args_validation(args)

    cursor_after = graphene.Node.from_global_id(after) if after else None
    cursor_before = graphene.Node.from_global_id(before) if before else None
    cursor = cursor_after or cursor_before
    cursor_offset = 1 if cursor else 0

    sort_by = args.get("sort_by", {})
    # TODO: check if qs have default orderby
    sort_by_field = sort_by.get("field", "pk")
    sort_by_direction = sort_by.get("direction", "")

    requested_count = first or last
    end_margin = requested_count + cursor_offset + 1 if requested_count else None

    if last:
        # reversed direction
        sort_by_direction = "" if sort_by_direction == OrderDirection.DESC else "-"
        sort_by_direction_kw = (
            "gte" if sort_by_direction == OrderDirection.DESC else "lte"
        )
    else:
        sort_by_direction_kw = (
            "lte" if sort_by_direction == OrderDirection.DESC else "gte"
        )

    filter_kwargs = {}

    if cursor:
        cursor_model = qs.model
        cursor = cursor_model.objects.get(pk=cursor[1])
        filter_kwargs[f"{sort_by_field}__{sort_by_direction_kw}"] = getattr(
            cursor, sort_by_field
        )

    sort_by_kw = [f"{sort_by_direction}{sort_by_field}"] if sort_by_field else None
    if sort_by_kw and not isinstance(qs, list):
        qs = qs.filter(**filter_kwargs).order_by(*sort_by_kw)[cursor_offset:end_margin]
    elif not isinstance(qs, list):
        qs = qs.filter(**filter_kwargs)[cursor_offset:end_margin]

    if last:
        matching_records = list(reversed(qs))
    else:
        matching_records = list(qs)

    has_previous_page = False
    has_next_page = False
    if requested_count is not None:
        if cursor_after:
            has_next_page = len(matching_records) > requested_count
            has_previous_page = True
        elif cursor_before:
            has_next_page = True
            has_previous_page = len(matching_records) > requested_count
        elif first:
            has_next_page = len(matching_records) > requested_count
        elif last:
            has_previous_page = len(matching_records) > requested_count
        matching_records = matching_records[
            cursor_offset : requested_count + cursor_offset
        ]

    edges = [
        edge_type(
            node=value,
            cursor=graphene.Node.to_global_id(value._meta.object_name, value.pk),
        )
        for index, value in enumerate(matching_records)
    ]

    first_edge_cursor = edges[0].cursor if edges else None
    last_edge_cursor = edges[-1].cursor if edges else None

    return connection_type(
        edges=edges,
        page_info=page_info_type(
            start_cursor=first_edge_cursor,
            end_cursor=last_edge_cursor,
            has_previous_page=has_previous_page,
            has_next_page=has_next_page,
        ),
    )


class NonNullConnection(Connection):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        super().__init_subclass_with_meta__(node=node, name=name, **options)

        # Override the original EdgeBase type to make to `node` field required.
        class EdgeBase:
            node = Field(
                cls._meta.node,
                description="The item at the end of the edge.",
                required=True,
            )
            cursor = String(
                required=True, description="A cursor for use in pagination."
            )

        # Create the edge type using the new EdgeBase.
        edge_name = cls.Edge._meta.name
        edge_bases = (EdgeBase, ObjectType)
        edge = type(edge_name, edge_bases, {})
        cls.Edge = edge

        # Override the `edges` field to make it non-null list
        # of non-null edges.
        cls._meta.fields["edges"] = Field(NonNull(List(NonNull(cls.Edge))))


class CountableConnection(NonNullConnection):
    class Meta:
        abstract = True

    total_count = graphene.Int(description="A total count of items in the collection.")

    @staticmethod
    def resolve_total_count(root, *_args, **_kwargs):
        return len(root.iterable)


class CountableDjangoObjectType(OptimizedDjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        # Force it to use the countable connection
        countable_conn = CountableConnection.create_type(
            "{}CountableConnection".format(cls.__name__), node=cls
        )
        super().__init_subclass_with_meta__(*args, connection=countable_conn, **kwargs)

    @classmethod
    def maybe_optimize(cls, info, qs: Union[QuerySet, Manager], pk):
        with ot.global_tracer().start_active_span("optimizer") as scope:
            span = scope.span
            span.set_tag("optimizer.pk", pk)
            span.set_tag("optimizer.model", cls._meta.model.__name__)
            return super().maybe_optimize(info, qs, pk)

    @classmethod
    def get_node(cls, info, id):
        with ot.global_tracer().start_active_span("node") as scope:
            span = scope.span
            span.set_tag("node.pk", id)
            span.set_tag("node.type", cls.__name__)
            return super().get_node(info, id)
