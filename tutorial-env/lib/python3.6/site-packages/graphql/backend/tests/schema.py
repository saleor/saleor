from graphql.type import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString


Query = GraphQLObjectType(
    "Query", lambda: {"hello": GraphQLField(GraphQLString, resolver=lambda *_: "World")}
)

schema = GraphQLSchema(Query)
