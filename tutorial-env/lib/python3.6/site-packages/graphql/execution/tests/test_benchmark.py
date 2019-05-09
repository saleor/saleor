# type: ignore
from collections import namedtuple
from functools import partial

from graphql import (
    GraphQLField,
    GraphQLInt,
    GraphQLList,
    GraphQLObjectType,
    GraphQLSchema,
    Source,
    execute,
    parse,
)

# from graphql.execution import executor

# executor.use_experimental_executor = True

SIZE = 10000
# set global fixtures
Container = namedtuple("Container", "x y z o")
big_int_list = [x for x in range(SIZE)]
big_container_list = [Container(x=x, y=x, z=x, o=x) for x in range(SIZE)]

ContainerType = GraphQLObjectType(
    "Container",
    fields={
        "x": GraphQLField(GraphQLInt),
        "y": GraphQLField(GraphQLInt),
        "z": GraphQLField(GraphQLInt),
        "o": GraphQLField(GraphQLInt),
    },
)


def resolve_all_containers(root, info, **args):
    return big_container_list


def resolve_all_ints(root, info, **args):
    return big_int_list


def test_big_list_of_ints(benchmark):
    Query = GraphQLObjectType(
        "Query",
        fields={
            "allInts": GraphQLField(GraphQLList(GraphQLInt), resolver=resolve_all_ints)
        },
    )
    schema = GraphQLSchema(Query)
    source = Source("{ allInts }")
    ast = parse(source)

    @benchmark
    def b():
        return execute(schema, ast)


def test_big_list_of_ints_serialize(benchmark):
    from ..executor import complete_leaf_value

    @benchmark
    def serialize():
        map(GraphQLInt.serialize, big_int_list)


def test_big_list_objecttypes_with_one_int_field(benchmark):
    Query = GraphQLObjectType(
        "Query",
        fields={
            "allContainers": GraphQLField(
                GraphQLList(ContainerType), resolver=resolve_all_containers
            )
        },
    )
    schema = GraphQLSchema(Query)
    source = Source("{ allContainers { x } }")
    ast = parse(source)

    @benchmark
    def b():
        return execute(schema, ast)


def test_big_list_objecttypes_with_two_int_fields(benchmark):
    Query = GraphQLObjectType(
        "Query",
        fields={
            "allContainers": GraphQLField(
                GraphQLList(ContainerType), resolver=resolve_all_containers
            )
        },
    )

    schema = GraphQLSchema(Query)
    source = Source("{ allContainers { x, y } }")
    ast = parse(source)

    @benchmark
    def b():
        return execute(schema, ast)
