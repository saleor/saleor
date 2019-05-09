from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)


class GrapheneGraphQLType(object):
    """
    A class for extending the base GraphQLType with the related
    graphene_type
    """

    def __init__(self, *args, **kwargs):
        self.graphene_type = kwargs.pop("graphene_type")
        super(GrapheneGraphQLType, self).__init__(*args, **kwargs)


class GrapheneInterfaceType(GrapheneGraphQLType, GraphQLInterfaceType):
    pass


class GrapheneUnionType(GrapheneGraphQLType, GraphQLUnionType):
    pass


class GrapheneObjectType(GrapheneGraphQLType, GraphQLObjectType):
    pass


class GrapheneScalarType(GrapheneGraphQLType, GraphQLScalarType):
    pass


class GrapheneEnumType(GrapheneGraphQLType, GraphQLEnumType):
    pass


class GrapheneInputObjectType(GrapheneGraphQLType, GraphQLInputObjectType):
    pass
