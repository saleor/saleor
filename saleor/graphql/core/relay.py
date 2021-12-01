import json
from functools import wraps
from typing import Optional

import graphene
from django.conf import settings
from graphql import GraphQLError, ResolveInfo
from graphql_relay.connection.arrayconnection import connection_from_list_slice

from ...channel.exceptions import ChannelNotDefined, NoDefaultChannel
from ..channel import ChannelContext, ChannelQsContext
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..utils.sorting import sort_queryset_for_connection
from .connection import NonNullConnection, connection_from_queryset_slice
from .fields import patch_pagination_args


FILTERSET_CLASS = "_FILTERSET_CLASS"
FILTERS_NAME = "_FILTERS_NAME"


class RelayConnectionField(graphene.Field):
    def __init__(self, type_, *args, **kwargs):
        kwargs.setdefault("before", graphene.String())
        kwargs.setdefault("after", graphene.String())
        kwargs.setdefault("first", graphene.Int())
        kwargs.setdefault("last", graphene.Int())
        super(RelayConnectionField, self).__init__(type_, *args, **kwargs)
        patch_pagination_args(self)


class RelayFilteredConnectionField(RelayConnectionField):
    def __init__(self, type_, *args, **kwargs):
        self.filter_field_name = kwargs.pop("filter_field_name", "filter")
        self.filter_input = kwargs.get(self.filter_field_name)
        self.FILTERSET_CLASS = None
        if self.filter_input:
            self.filterset_class = self.filter_input.filterset_class
        super(RelayFilteredConnectionField, self).__init__(type_, *args, **kwargs)

    def get_resolver(self, parent_resolver):
        wrapped_resolver = super().get_resolver(parent_resolver)

        @wraps(wrapped_resolver)
        def new_resolver(obj, info, **kwargs):
            kwargs[FILTERSET_CLASS] = self.filterset_class
            kwargs[FILTERS_NAME] = self.filter_field_name
            return wrapped_resolver(obj, info, **kwargs)

        return new_resolver


class RelayCountableConnection(NonNullConnection):
    class Meta:
        abstract = True

    total_count = graphene.Int(description="A total count of items in the collection.")

    def resolve_total_count(root, *_):
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


def create_connection_slice(
    iterable,
    info,
    args,
    connection_type,
    edge_type=None,
    pageinfo_type=graphene.relay.PageInfo,
    enforce_first_or_last: Optional[bool] = None,
    max_limit: Optional[int] = None,
):
    validate_slice_args(info, args, enforce_first_or_last, max_limit)

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


def validate_slice_args(
    info: ResolveInfo,
    args: dict,
    enforce_first_or_last: Optional[bool] = None,
    max_limit: Optional[int] = None,
):
    # Disable `enforce_first_or_last` if not querying for `edges`.
    values = [field.name.value for field in info.field_asts[0].selection_set.selections]
    if "edges" not in values:
        enforce_first_or_last = False
    elif enforce_first_or_last is None:
        enforce_first_or_last = settings.GRAPHENE.get(
            "RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST", True
        )

    first = args.get("first")
    last = args.get("last")

    if enforce_first_or_last and not (first or last):
        raise GraphQLError(
            f"You must provide a `first` or `last` value to properly paginate "
            f"the `{info.field_name}` connection."
        )

    if max_limit is None:
        max_limit = settings.GRAPHENE.get("RELAY_CONNECTION_MAX_LIMIT", 0)

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
    print("filter_connection_queryset")
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
