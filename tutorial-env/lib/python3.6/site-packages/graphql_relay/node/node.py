from collections import OrderedDict
from graphql_relay.utils import base64, unbase64

from six import text_type

from graphql.type import (
    GraphQLArgument,
    GraphQLNonNull,
    GraphQLID,
    GraphQLField,
    GraphQLInterfaceType,
)


def node_definitions(id_fetcher, type_resolver=None, id_resolver=None):
    '''
    Given a function to map from an ID to an underlying object, and a function
    to map from an underlying object to the concrete GraphQLObjectType it
    corresponds to, constructs a `Node` interface that objects can implement,
    and a field config for a `node` root field.

    If the type_resolver is omitted, object resolution on the interface will be
    handled with the `isTypeOf` method on object types, as with any GraphQL
    interface without a provided `resolveType` method.
    '''
    node_interface = GraphQLInterfaceType(
        'Node',
        description='An object with an ID',
        fields=lambda: OrderedDict((
            ('id', GraphQLField(
                GraphQLNonNull(GraphQLID),
                description='The id of the object.',
                resolver=id_resolver,
            )),
        )),
        resolve_type=type_resolver
    )
    node_field = GraphQLField(
        node_interface,
        description='Fetches an object given its ID',
        args=OrderedDict((
            ('id', GraphQLArgument(
                GraphQLNonNull(GraphQLID),
                description='The ID of an object'
            )),
        )),
        resolver=lambda obj, args, *_: id_fetcher(args.get('id'), *_)
    )
    return node_interface, node_field


def to_global_id(type, id):
    '''
    Takes a type name and an ID specific to that type name, and returns a
    "global ID" that is unique among all types.
    '''
    return base64(':'.join([type, text_type(id)]))


def from_global_id(global_id):
    '''
    Takes the "global ID" created by toGlobalID, and retuns the type name and ID
    used to create it.
    '''
    unbased_global_id = unbase64(global_id)
    _type, _id = unbased_global_id.split(':', 1)
    return _type, _id


def global_id_field(type_name, id_fetcher=None):
    '''
    Creates the configuration for an id field on a node, using `to_global_id` to
    construct the ID from the provided typename. The type-specific ID is fetcher
    by calling id_fetcher on the object, or if not provided, by accessing the `id`
    property on the object.
    '''
    return GraphQLField(
        GraphQLNonNull(GraphQLID),
        description='The ID of an object',
        resolver=lambda obj, args, context, info: to_global_id(
            type_name or info.parent_type.name,
            id_fetcher(obj, context, info) if id_fetcher else obj.id
        )
    )
