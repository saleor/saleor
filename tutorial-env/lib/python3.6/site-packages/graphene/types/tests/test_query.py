import json
from functools import partial

from graphql import GraphQLError, ResolveInfo, Source, execute, parse

from ..context import Context
from ..dynamic import Dynamic
from ..field import Field
from ..inputfield import InputField
from ..inputobjecttype import InputObjectType
from ..interface import Interface
from ..objecttype import ObjectType
from ..scalars import Boolean, Int, String
from ..schema import Schema
from ..structures import List, NonNull
from ..union import Union


def test_query():
    class Query(ObjectType):
        hello = String(resolver=lambda *_: "World")

    hello_schema = Schema(Query)

    executed = hello_schema.execute("{ hello }")
    assert not executed.errors
    assert executed.data == {"hello": "World"}


def test_query_source():
    class Root(object):
        _hello = "World"

        def hello(self):
            return self._hello

    class Query(ObjectType):
        hello = String(source="hello")

    hello_schema = Schema(Query)

    executed = hello_schema.execute("{ hello }", Root())
    assert not executed.errors
    assert executed.data == {"hello": "World"}


def test_query_union():
    class one_object(object):
        pass

    class two_object(object):
        pass

    class One(ObjectType):
        one = String()

        @classmethod
        def is_type_of(cls, root, info):
            return isinstance(root, one_object)

    class Two(ObjectType):
        two = String()

        @classmethod
        def is_type_of(cls, root, info):
            return isinstance(root, two_object)

    class MyUnion(Union):
        class Meta:
            types = (One, Two)

    class Query(ObjectType):
        unions = List(MyUnion)

        def resolve_unions(self, info):
            return [one_object(), two_object()]

    hello_schema = Schema(Query)

    executed = hello_schema.execute("{ unions { __typename } }")
    assert not executed.errors
    assert executed.data == {"unions": [{"__typename": "One"}, {"__typename": "Two"}]}


def test_query_interface():
    class one_object(object):
        pass

    class two_object(object):
        pass

    class MyInterface(Interface):
        base = String()

    class One(ObjectType):
        class Meta:
            interfaces = (MyInterface,)

        one = String()

        @classmethod
        def is_type_of(cls, root, info):
            return isinstance(root, one_object)

    class Two(ObjectType):
        class Meta:
            interfaces = (MyInterface,)

        two = String()

        @classmethod
        def is_type_of(cls, root, info):
            return isinstance(root, two_object)

    class Query(ObjectType):
        interfaces = List(MyInterface)

        def resolve_interfaces(self, info):
            return [one_object(), two_object()]

    hello_schema = Schema(Query, types=[One, Two])

    executed = hello_schema.execute("{ interfaces { __typename } }")
    assert not executed.errors
    assert executed.data == {
        "interfaces": [{"__typename": "One"}, {"__typename": "Two"}]
    }


def test_query_dynamic():
    class Query(ObjectType):
        hello = Dynamic(lambda: String(resolver=lambda *_: "World"))
        hellos = Dynamic(lambda: List(String, resolver=lambda *_: ["Worlds"]))
        hello_field = Dynamic(lambda: Field(String, resolver=lambda *_: "Field World"))

    hello_schema = Schema(Query)

    executed = hello_schema.execute("{ hello hellos helloField }")
    assert not executed.errors
    assert executed.data == {
        "hello": "World",
        "hellos": ["Worlds"],
        "helloField": "Field World",
    }


def test_query_default_value():
    class MyType(ObjectType):
        field = String()

    class Query(ObjectType):
        hello = Field(MyType, default_value=MyType(field="something else!"))

    hello_schema = Schema(Query)

    executed = hello_schema.execute("{ hello { field } }")
    assert not executed.errors
    assert executed.data == {"hello": {"field": "something else!"}}


def test_query_wrong_default_value():
    class MyType(ObjectType):
        field = String()

        @classmethod
        def is_type_of(cls, root, info):
            return isinstance(root, MyType)

    class Query(ObjectType):
        hello = Field(MyType, default_value="hello")

    hello_schema = Schema(Query)

    executed = hello_schema.execute("{ hello { field } }")
    assert len(executed.errors) == 1
    assert (
        executed.errors[0].message
        == GraphQLError('Expected value of type "MyType" but got: str.').message
    )
    assert executed.data == {"hello": None}


def test_query_default_value_ignored_by_resolver():
    class MyType(ObjectType):
        field = String()

    class Query(ObjectType):
        hello = Field(
            MyType,
            default_value="hello",
            resolver=lambda *_: MyType(field="no default."),
        )

    hello_schema = Schema(Query)

    executed = hello_schema.execute("{ hello { field } }")
    assert not executed.errors
    assert executed.data == {"hello": {"field": "no default."}}


def test_query_resolve_function():
    class Query(ObjectType):
        hello = String()

        def resolve_hello(self, info):
            return "World"

    hello_schema = Schema(Query)

    executed = hello_schema.execute("{ hello }")
    assert not executed.errors
    assert executed.data == {"hello": "World"}


def test_query_arguments():
    class Query(ObjectType):
        test = String(a_str=String(), a_int=Int())

        def resolve_test(self, info, **args):
            return json.dumps([self, args], separators=(",", ":"))

    test_schema = Schema(Query)

    result = test_schema.execute("{ test }", None)
    assert not result.errors
    assert result.data == {"test": "[null,{}]"}

    result = test_schema.execute('{ test(aStr: "String!") }', "Source!")
    assert not result.errors
    assert result.data == {"test": '["Source!",{"a_str":"String!"}]'}

    result = test_schema.execute('{ test(aInt: -123, aStr: "String!") }', "Source!")
    assert not result.errors
    assert result.data in [
        {"test": '["Source!",{"a_str":"String!","a_int":-123}]'},
        {"test": '["Source!",{"a_int":-123,"a_str":"String!"}]'},
    ]


def test_query_input_field():
    class Input(InputObjectType):
        a_field = String()
        recursive_field = InputField(lambda: Input)

    class Query(ObjectType):
        test = String(a_input=Input())

        def resolve_test(self, info, **args):
            return json.dumps([self, args], separators=(",", ":"))

    test_schema = Schema(Query)

    result = test_schema.execute("{ test }", None)
    assert not result.errors
    assert result.data == {"test": "[null,{}]"}

    result = test_schema.execute('{ test(aInput: {aField: "String!"} ) }', "Source!")
    assert not result.errors
    assert result.data == {"test": '["Source!",{"a_input":{"a_field":"String!"}}]'}

    result = test_schema.execute(
        '{ test(aInput: {recursiveField: {aField: "String!"}}) }', "Source!"
    )
    assert not result.errors
    assert result.data == {
        "test": '["Source!",{"a_input":{"recursive_field":{"a_field":"String!"}}}]'
    }


def test_query_middlewares():
    class Query(ObjectType):
        hello = String()
        other = String()

        def resolve_hello(self, info):
            return "World"

        def resolve_other(self, info):
            return "other"

    def reversed_middleware(next, *args, **kwargs):
        p = next(*args, **kwargs)
        return p.then(lambda x: x[::-1])

    hello_schema = Schema(Query)

    executed = hello_schema.execute(
        "{ hello, other }", middleware=[reversed_middleware]
    )
    assert not executed.errors
    assert executed.data == {"hello": "dlroW", "other": "rehto"}


def test_objecttype_on_instances():
    class Ship:
        def __init__(self, name):
            self.name = name

    class ShipType(ObjectType):
        name = String(description="Ship name", required=True)

        def resolve_name(self, info):
            # Here self will be the Ship instance returned in resolve_ship
            return self.name

    class Query(ObjectType):
        ship = Field(ShipType)

        def resolve_ship(self, info):
            return Ship(name="xwing")

    schema = Schema(query=Query)
    executed = schema.execute("{ ship { name } }")
    assert not executed.errors
    assert executed.data == {"ship": {"name": "xwing"}}


def test_big_list_query_benchmark(benchmark):
    big_list = range(10000)

    class Query(ObjectType):
        all_ints = List(Int)

        def resolve_all_ints(self, info):
            return big_list

    hello_schema = Schema(Query)

    big_list_query = partial(hello_schema.execute, "{ allInts }")
    result = benchmark(big_list_query)
    assert not result.errors
    assert result.data == {"allInts": list(big_list)}


def test_big_list_query_compiled_query_benchmark(benchmark):
    big_list = range(100000)

    class Query(ObjectType):
        all_ints = List(Int)

        def resolve_all_ints(self, info):
            return big_list

    hello_schema = Schema(Query)
    source = Source("{ allInts }")
    query_ast = parse(source)

    big_list_query = partial(execute, hello_schema, query_ast)
    result = benchmark(big_list_query)
    assert not result.errors
    assert result.data == {"allInts": list(big_list)}


def test_big_list_of_containers_query_benchmark(benchmark):
    class Container(ObjectType):
        x = Int()

    big_container_list = [Container(x=x) for x in range(1000)]

    class Query(ObjectType):
        all_containers = List(Container)

        def resolve_all_containers(self, info):
            return big_container_list

    hello_schema = Schema(Query)

    big_list_query = partial(hello_schema.execute, "{ allContainers { x } }")
    result = benchmark(big_list_query)
    assert not result.errors
    assert result.data == {"allContainers": [{"x": c.x} for c in big_container_list]}


def test_big_list_of_containers_multiple_fields_query_benchmark(benchmark):
    class Container(ObjectType):
        x = Int()
        y = Int()
        z = Int()
        o = Int()

    big_container_list = [Container(x=x, y=x, z=x, o=x) for x in range(1000)]

    class Query(ObjectType):
        all_containers = List(Container)

        def resolve_all_containers(self, info):
            return big_container_list

    hello_schema = Schema(Query)

    big_list_query = partial(hello_schema.execute, "{ allContainers { x, y, z, o } }")
    result = benchmark(big_list_query)
    assert not result.errors
    assert result.data == {
        "allContainers": [
            {"x": c.x, "y": c.y, "z": c.z, "o": c.o} for c in big_container_list
        ]
    }


def test_big_list_of_containers_multiple_fields_custom_resolvers_query_benchmark(
    benchmark
):
    class Container(ObjectType):
        x = Int()
        y = Int()
        z = Int()
        o = Int()

        def resolve_x(self, info):
            return self.x

        def resolve_y(self, info):
            return self.y

        def resolve_z(self, info):
            return self.z

        def resolve_o(self, info):
            return self.o

    big_container_list = [Container(x=x, y=x, z=x, o=x) for x in range(1000)]

    class Query(ObjectType):
        all_containers = List(Container)

        def resolve_all_containers(self, info):
            return big_container_list

    hello_schema = Schema(Query)

    big_list_query = partial(hello_schema.execute, "{ allContainers { x, y, z, o } }")
    result = benchmark(big_list_query)
    assert not result.errors
    assert result.data == {
        "allContainers": [
            {"x": c.x, "y": c.y, "z": c.z, "o": c.o} for c in big_container_list
        ]
    }


def test_query_annotated_resolvers():
    context = Context(key="context")

    class Query(ObjectType):
        annotated = String(id=String())
        context = String()
        info = String()

        def resolve_annotated(self, info, id):
            return "{}-{}".format(self, id)

        def resolve_context(self, info):
            assert isinstance(info.context, Context)
            return "{}-{}".format(self, info.context.key)

        def resolve_info(self, info):
            assert isinstance(info, ResolveInfo)
            return "{}-{}".format(self, info.field_name)

    test_schema = Schema(Query)

    result = test_schema.execute('{ annotated(id:"self") }', "base")
    assert not result.errors
    assert result.data == {"annotated": "base-self"}

    result = test_schema.execute("{ context }", "base", context_value=context)
    assert not result.errors
    assert result.data == {"context": "base-context"}

    result = test_schema.execute("{ info }", "base")
    assert not result.errors
    assert result.data == {"info": "base-info"}


def test_default_as_kwarg_to_NonNull():
    # Related to https://github.com/graphql-python/graphene/issues/702
    class User(ObjectType):
        name = String()
        is_admin = NonNull(Boolean, default_value=False)

    class Query(ObjectType):
        user = Field(User)

        def resolve_user(self, *args, **kwargs):
            return User(name="foo")

    schema = Schema(query=Query)
    expected = {"user": {"name": "foo", "isAdmin": False}}
    result = schema.execute("{ user { name isAdmin } }")

    assert not result.errors
    assert result.data == expected
