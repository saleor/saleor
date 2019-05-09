import re
from collections import Iterable, OrderedDict
from functools import partial

from graphql_relay import connection_from_list
from promise import Promise, is_thenable

from ..types import Boolean, Enum, Int, Interface, List, NonNull, Scalar, String, Union
from ..types.field import Field
from ..types.objecttype import ObjectType, ObjectTypeOptions
from .node import is_node


class PageInfo(ObjectType):
    has_next_page = Boolean(
        required=True,
        name="hasNextPage",
        description="When paginating forwards, are there more items?",
    )

    has_previous_page = Boolean(
        required=True,
        name="hasPreviousPage",
        description="When paginating backwards, are there more items?",
    )

    start_cursor = String(
        name="startCursor",
        description="When paginating backwards, the cursor to continue.",
    )

    end_cursor = String(
        name="endCursor",
        description="When paginating forwards, the cursor to continue.",
    )


class ConnectionOptions(ObjectTypeOptions):
    node = None


class Connection(ObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        _meta = ConnectionOptions(cls)
        assert node, "You have to provide a node in {}.Meta".format(cls.__name__)
        assert issubclass(
            node, (Scalar, Enum, ObjectType, Interface, Union, NonNull)
        ), ('Received incompatible node "{}" for Connection {}.').format(
            node, cls.__name__
        )

        base_name = re.sub("Connection$", "", name or cls.__name__) or node._meta.name
        if not name:
            name = "{}Connection".format(base_name)

        edge_class = getattr(cls, "Edge", None)
        _node = node

        class EdgeBase(object):
            node = Field(_node, description="The item at the end of the edge")
            cursor = String(required=True, description="A cursor for use in pagination")

        edge_name = "{}Edge".format(base_name)
        if edge_class:
            edge_bases = (edge_class, EdgeBase, ObjectType)
        else:
            edge_bases = (EdgeBase, ObjectType)

        edge = type(edge_name, edge_bases, {})
        cls.Edge = edge

        options["name"] = name
        _meta.node = node
        _meta.fields = OrderedDict(
            [
                ("page_info", Field(PageInfo, name="pageInfo", required=True)),
                ("edges", Field(NonNull(List(edge)))),
            ]
        )
        return super(Connection, cls).__init_subclass_with_meta__(
            _meta=_meta, **options
        )


class IterableConnectionField(Field):
    def __init__(self, type, *args, **kwargs):
        kwargs.setdefault("before", String())
        kwargs.setdefault("after", String())
        kwargs.setdefault("first", Int())
        kwargs.setdefault("last", Int())
        super(IterableConnectionField, self).__init__(type, *args, **kwargs)

    @property
    def type(self):
        type = super(IterableConnectionField, self).type
        connection_type = type
        if isinstance(type, NonNull):
            connection_type = type.of_type

        if is_node(connection_type):
            raise Exception(
                "ConnectionField's now need a explicit ConnectionType for Nodes.\n"
                "Read more: https://github.com/graphql-python/graphene/blob/v2.0.0/UPGRADE-v2.0.md#node-connections"
            )

        assert issubclass(connection_type, Connection), (
            '{} type have to be a subclass of Connection. Received "{}".'
        ).format(self.__class__.__name__, connection_type)
        return type

    @classmethod
    def resolve_connection(cls, connection_type, args, resolved):
        if isinstance(resolved, connection_type):
            return resolved

        assert isinstance(resolved, Iterable), (
            "Resolved value from the connection field have to be iterable or instance of {}. "
            'Received "{}"'
        ).format(connection_type, resolved)
        connection = connection_from_list(
            resolved,
            args,
            connection_type=connection_type,
            edge_type=connection_type.Edge,
            pageinfo_type=PageInfo,
        )
        connection.iterable = resolved
        return connection

    @classmethod
    def connection_resolver(cls, resolver, connection_type, root, info, **args):
        resolved = resolver(root, info, **args)

        if isinstance(connection_type, NonNull):
            connection_type = connection_type.of_type

        on_resolve = partial(cls.resolve_connection, connection_type, args)
        if is_thenable(resolved):
            return Promise.resolve(resolved).then(on_resolve)

        return on_resolve(resolved)

    def get_resolver(self, parent_resolver):
        resolver = super(IterableConnectionField, self).get_resolver(parent_resolver)
        return partial(self.connection_resolver, resolver, self.type)


ConnectionField = IterableConnectionField
