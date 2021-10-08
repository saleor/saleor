from functools import partial

from django.db.models.query import QuerySet
from graphql_relay.connection.arrayconnection import (
    connection_from_array_slice,
    cursor_to_offset,
    get_offset_with_default,
    offset_to_cursor,
)
from promise import Promise

from graphene import Int, NonNull
from graphene.relay import ConnectionField
from graphene.relay.connection import connection_adapter, page_info_adapter
from graphene.types import Field, List

from .settings import graphene_settings
from .utils import maybe_queryset


class DjangoListField(Field):
    def __init__(self, _type, *args, **kwargs):
        from .types import DjangoObjectType

        if isinstance(_type, NonNull):
            _type = _type.of_type

        # Django would never return a Set of None  vvvvvvv
        super(DjangoListField, self).__init__(List(NonNull(_type)), *args, **kwargs)

        assert issubclass(
            self._underlying_type, DjangoObjectType
        ), "DjangoListField only accepts DjangoObjectType types"

    @property
    def _underlying_type(self):
        _type = self._type
        while hasattr(_type, "of_type"):
            _type = _type.of_type
        return _type

    @property
    def model(self):
        return self._underlying_type._meta.model

    def get_manager(self):
        return self.model._default_manager

    @staticmethod
    def list_resolver(
        django_object_type, resolver, default_manager, root, info, **args
    ):
        queryset = maybe_queryset(resolver(root, info, **args))
        if queryset is None:
            queryset = maybe_queryset(default_manager)

        if isinstance(queryset, QuerySet):
            # Pass queryset to the DjangoObjectType get_queryset method
            queryset = maybe_queryset(django_object_type.get_queryset(queryset, info))

        return queryset

    def wrap_resolve(self, parent_resolver):
        resolver = super(DjangoListField, self).wrap_resolve(parent_resolver)
        _type = self.type
        if isinstance(_type, NonNull):
            _type = _type.of_type
        django_object_type = _type.of_type.of_type
        return partial(
            self.list_resolver, django_object_type, resolver, self.get_manager(),
        )


class DjangoConnectionField(ConnectionField):
    def __init__(self, *args, **kwargs):
        self.on = kwargs.pop("on", False)
        self.max_limit = kwargs.pop(
            "max_limit", graphene_settings.RELAY_CONNECTION_MAX_LIMIT
        )
        self.enforce_first_or_last = kwargs.pop(
            "enforce_first_or_last",
            graphene_settings.RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST,
        )
        kwargs.setdefault("offset", Int())
        super(DjangoConnectionField, self).__init__(*args, **kwargs)

    @property
    def type(self):
        from .types import DjangoObjectType

        _type = super(ConnectionField, self).type
        non_null = False
        if isinstance(_type, NonNull):
            _type = _type.of_type
            non_null = True
        assert issubclass(
            _type, DjangoObjectType
        ), "DjangoConnectionField only accepts DjangoObjectType types"
        assert _type._meta.connection, "The type {} doesn't have a connection".format(
            _type.__name__
        )
        connection_type = _type._meta.connection
        if non_null:
            return NonNull(connection_type)
        return connection_type

    @property
    def connection_type(self):
        type = self.type
        if isinstance(type, NonNull):
            return type.of_type
        return type

    @property
    def node_type(self):
        return self.connection_type._meta.node

    @property
    def model(self):
        return self.node_type._meta.model

    def get_manager(self):
        if self.on:
            return getattr(self.model, self.on)
        else:
            return self.model._default_manager

    @classmethod
    def resolve_queryset(cls, connection, queryset, info, args):
        # queryset is the resolved iterable from ObjectType
        return connection._meta.node.get_queryset(queryset, info)

    @classmethod
    def resolve_connection(cls, connection, args, iterable, max_limit=None):
        # Remove the offset parameter and convert it to an after cursor.
        offset = args.pop("offset", None)
        after = args.get("after")
        if offset:
            if after:
                offset += cursor_to_offset(after) + 1
            # input offset starts at 1 while the graphene offset starts at 0
            args["after"] = offset_to_cursor(offset - 1)

        iterable = maybe_queryset(iterable)

        if isinstance(iterable, QuerySet):
            list_length = iterable.count()
        else:
            list_length = len(iterable)
        list_slice_length = (
            min(max_limit, list_length) if max_limit is not None else list_length
        )

        # If after is higher than list_length, connection_from_list_slice
        # would try to do a negative slicing which makes django throw an
        # AssertionError
        after = min(get_offset_with_default(args.get("after"), -1) + 1, list_length)

        if max_limit is not None and args.get("first", None) is None:
            if args.get("last", None) is not None:
                after = list_length - args["last"]
            else:
                args["first"] = max_limit

        connection = connection_from_array_slice(
            iterable[after:],
            args,
            slice_start=after,
            array_length=list_length,
            array_slice_length=list_slice_length,
            connection_type=partial(connection_adapter, connection),
            edge_type=connection.Edge,
            page_info_type=page_info_adapter,
        )
        connection.iterable = iterable
        connection.length = list_length
        return connection

    @classmethod
    def connection_resolver(
        cls,
        resolver,
        connection,
        default_manager,
        queryset_resolver,
        max_limit,
        enforce_first_or_last,
        root,
        info,
        **args
    ):
        first = args.get("first")
        last = args.get("last")
        offset = args.get("offset")
        before = args.get("before")

        if enforce_first_or_last:
            assert first or last, (
                "You must provide a `first` or `last` value to properly paginate the `{}` connection."
            ).format(info.field_name)

        if max_limit:
            if first:
                assert first <= max_limit, (
                    "Requesting {} records on the `{}` connection exceeds the `first` limit of {} records."
                ).format(first, info.field_name, max_limit)
                args["first"] = min(first, max_limit)

            if last:
                assert last <= max_limit, (
                    "Requesting {} records on the `{}` connection exceeds the `last` limit of {} records."
                ).format(last, info.field_name, max_limit)
                args["last"] = min(last, max_limit)

        if offset is not None:
            assert before is None, (
                "You can't provide a `before` value at the same time as an `offset` value to properly paginate the `{}` connection."
            ).format(info.field_name)

        # eventually leads to DjangoObjectType's get_queryset (accepts queryset)
        # or a resolve_foo (does not accept queryset)
        iterable = resolver(root, info, **args)
        if iterable is None:
            iterable = default_manager
        # thus the iterable gets refiltered by resolve_queryset
        # but iterable might be promise
        iterable = queryset_resolver(connection, iterable, info, args)
        on_resolve = partial(
            cls.resolve_connection, connection, args, max_limit=max_limit
        )

        if Promise.is_thenable(iterable):
            return Promise.resolve(iterable).then(on_resolve)

        return on_resolve(iterable)

    def wrap_resolve(self, parent_resolver):
        return partial(
            self.connection_resolver,
            parent_resolver,
            self.connection_type,
            self.get_manager(),
            self.get_queryset_resolver(),
            self.max_limit,
            self.enforce_first_or_last,
        )

    def get_queryset_resolver(self):
        return self.resolve_queryset
