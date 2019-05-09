from collections import OrderedDict

from graphql.type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLInt,
    GraphQLNonNull,
    GraphQLList,
    GraphQLObjectType,
    GraphQLString,
    GraphQLField
)
from ..utils import resolve_maybe_thunk


connection_args = OrderedDict((
    ('before', GraphQLArgument(GraphQLString)),
    ('after', GraphQLArgument(GraphQLString)),
    ('first', GraphQLArgument(GraphQLInt)),
    ('last', GraphQLArgument(GraphQLInt)),
))


def connection_definitions(name, node_type, resolve_node=None, resolve_cursor=None, edge_fields=None, connection_fields=None):
    edge_fields = edge_fields or OrderedDict()
    connection_fields = connection_fields or OrderedDict()
    edge_type = GraphQLObjectType(
        name + 'Edge',
        description='An edge in a connection.',
        fields=lambda: OrderedDict((
            ('node', GraphQLField(
                node_type,
                resolver=resolve_node,
                description='The item at the end of the edge',
            )),
            ('cursor', GraphQLField(
                GraphQLNonNull(GraphQLString),
                resolver=resolve_cursor,
                description='A cursor for use in pagination',
            )),
        ), **resolve_maybe_thunk(edge_fields))
    )

    connection_type = GraphQLObjectType(
        name + 'Connection',
        description='A connection to a list of items.',
        fields=lambda: OrderedDict((
            ('pageInfo', GraphQLField(
                GraphQLNonNull(page_info_type),
                description='The Information to aid in pagination',
            )),
            ('edges', GraphQLField(
                GraphQLList(edge_type),
                description='A list of edges.',
            )),
        ), **resolve_maybe_thunk(connection_fields))
    )

    return edge_type, connection_type


# The common page info type used by all connections.
page_info_type = GraphQLObjectType(
    'PageInfo',
    description='Information about pagination in a connection.',
    fields=lambda: OrderedDict((
        ('hasNextPage', GraphQLField(
            GraphQLNonNull(GraphQLBoolean),
            description='When paginating forwards, are there more items?',
        )),
        ('hasPreviousPage', GraphQLField(
            GraphQLNonNull(GraphQLBoolean),
            description='When paginating backwards, are there more items?',
        )),
        ('startCursor', GraphQLField(
            GraphQLString,
            description='When paginating backwards, the cursor to continue.',
        )),
        ('endCursor', GraphQLField(
            GraphQLString,
            description='When paginating forwards, the cursor to continue.',
        )),
    ))
)
