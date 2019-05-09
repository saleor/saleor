import pytest
from graphql.type import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLString,
)

from ..dynamic import Dynamic
from ..enum import Enum
from ..field import Field
from ..inputfield import InputField
from ..inputobjecttype import InputObjectType
from ..interface import Interface
from ..objecttype import ObjectType
from ..scalars import Int, String
from ..structures import List, NonNull
from ..typemap import TypeMap, resolve_type


def test_enum():
    class MyEnum(Enum):
        """Description"""

        foo = 1
        bar = 2

        @property
        def description(self):
            return "Description {}={}".format(self.name, self.value)

        @property
        def deprecation_reason(self):
            if self == MyEnum.foo:
                return "Is deprecated"

    typemap = TypeMap([MyEnum])
    assert "MyEnum" in typemap
    graphql_enum = typemap["MyEnum"]
    assert isinstance(graphql_enum, GraphQLEnumType)
    assert graphql_enum.name == "MyEnum"
    assert graphql_enum.description == "Description"
    values = graphql_enum.values
    assert values == [
        GraphQLEnumValue(
            name="foo",
            value=1,
            description="Description foo=1",
            deprecation_reason="Is deprecated",
        ),
        GraphQLEnumValue(name="bar", value=2, description="Description bar=2"),
    ]


def test_objecttype():
    class MyObjectType(ObjectType):
        """Description"""

        foo = String(
            bar=String(description="Argument description", default_value="x"),
            description="Field description",
        )
        bar = String(name="gizmo")

        def resolve_foo(self, bar):
            return bar

    typemap = TypeMap([MyObjectType])
    assert "MyObjectType" in typemap
    graphql_type = typemap["MyObjectType"]
    assert isinstance(graphql_type, GraphQLObjectType)
    assert graphql_type.name == "MyObjectType"
    assert graphql_type.description == "Description"

    fields = graphql_type.fields
    assert list(fields.keys()) == ["foo", "gizmo"]
    foo_field = fields["foo"]
    assert isinstance(foo_field, GraphQLField)
    assert foo_field.description == "Field description"

    assert foo_field.args == {
        "bar": GraphQLArgument(
            GraphQLString,
            description="Argument description",
            default_value="x",
            out_name="bar",
        )
    }


def test_dynamic_objecttype():
    class MyObjectType(ObjectType):
        """Description"""

        bar = Dynamic(lambda: Field(String))
        own = Field(lambda: MyObjectType)

    typemap = TypeMap([MyObjectType])
    assert "MyObjectType" in typemap
    assert list(MyObjectType._meta.fields.keys()) == ["bar", "own"]
    graphql_type = typemap["MyObjectType"]

    fields = graphql_type.fields
    assert list(fields.keys()) == ["bar", "own"]
    assert fields["bar"].type == GraphQLString
    assert fields["own"].type == graphql_type


def test_interface():
    class MyInterface(Interface):
        """Description"""

        foo = String(
            bar=String(description="Argument description", default_value="x"),
            description="Field description",
        )
        bar = String(name="gizmo", first_arg=String(), other_arg=String(name="oth_arg"))
        own = Field(lambda: MyInterface)

        def resolve_foo(self, args, info):
            return args.get("bar")

    typemap = TypeMap([MyInterface])
    assert "MyInterface" in typemap
    graphql_type = typemap["MyInterface"]
    assert isinstance(graphql_type, GraphQLInterfaceType)
    assert graphql_type.name == "MyInterface"
    assert graphql_type.description == "Description"

    fields = graphql_type.fields
    assert list(fields.keys()) == ["foo", "gizmo", "own"]
    assert fields["own"].type == graphql_type
    assert list(fields["gizmo"].args.keys()) == ["firstArg", "oth_arg"]
    foo_field = fields["foo"]
    assert isinstance(foo_field, GraphQLField)
    assert foo_field.description == "Field description"
    assert not foo_field.resolver  # Resolver not attached in interfaces
    assert foo_field.args == {
        "bar": GraphQLArgument(
            GraphQLString,
            description="Argument description",
            default_value="x",
            out_name="bar",
        )
    }


def test_inputobject():
    class OtherObjectType(InputObjectType):
        thingy = NonNull(Int)

    class MyInnerObjectType(InputObjectType):
        some_field = String()
        some_other_field = List(OtherObjectType)

    class MyInputObjectType(InputObjectType):
        """Description"""

        foo_bar = String(description="Field description")
        bar = String(name="gizmo")
        baz = NonNull(MyInnerObjectType)
        own = InputField(lambda: MyInputObjectType)

        def resolve_foo_bar(self, args, info):
            return args.get("bar")

    typemap = TypeMap([MyInputObjectType])
    assert "MyInputObjectType" in typemap
    graphql_type = typemap["MyInputObjectType"]
    assert isinstance(graphql_type, GraphQLInputObjectType)
    assert graphql_type.name == "MyInputObjectType"
    assert graphql_type.description == "Description"

    other_graphql_type = typemap["OtherObjectType"]
    inner_graphql_type = typemap["MyInnerObjectType"]
    container = graphql_type.create_container(
        {
            "bar": "oh!",
            "baz": inner_graphql_type.create_container(
                {
                    "some_other_field": [
                        other_graphql_type.create_container({"thingy": 1}),
                        other_graphql_type.create_container({"thingy": 2}),
                    ]
                }
            ),
        }
    )
    assert isinstance(container, MyInputObjectType)
    assert "bar" in container
    assert container.bar == "oh!"
    assert "foo_bar" not in container
    assert container.foo_bar is None
    assert container.baz.some_field is None
    assert container.baz.some_other_field[0].thingy == 1
    assert container.baz.some_other_field[1].thingy == 2

    fields = graphql_type.fields
    assert list(fields.keys()) == ["fooBar", "gizmo", "baz", "own"]
    own_field = fields["own"]
    assert own_field.type == graphql_type
    foo_field = fields["fooBar"]
    assert isinstance(foo_field, GraphQLInputObjectField)
    assert foo_field.description == "Field description"


def test_objecttype_camelcase():
    class MyObjectType(ObjectType):
        """Description"""

        foo_bar = String(bar_foo=String())

    typemap = TypeMap([MyObjectType])
    assert "MyObjectType" in typemap
    graphql_type = typemap["MyObjectType"]
    assert isinstance(graphql_type, GraphQLObjectType)
    assert graphql_type.name == "MyObjectType"
    assert graphql_type.description == "Description"

    fields = graphql_type.fields
    assert list(fields.keys()) == ["fooBar"]
    foo_field = fields["fooBar"]
    assert isinstance(foo_field, GraphQLField)
    assert foo_field.args == {
        "barFoo": GraphQLArgument(GraphQLString, out_name="bar_foo")
    }


def test_objecttype_camelcase_disabled():
    class MyObjectType(ObjectType):
        """Description"""

        foo_bar = String(bar_foo=String())

    typemap = TypeMap([MyObjectType], auto_camelcase=False)
    assert "MyObjectType" in typemap
    graphql_type = typemap["MyObjectType"]
    assert isinstance(graphql_type, GraphQLObjectType)
    assert graphql_type.name == "MyObjectType"
    assert graphql_type.description == "Description"

    fields = graphql_type.fields
    assert list(fields.keys()) == ["foo_bar"]
    foo_field = fields["foo_bar"]
    assert isinstance(foo_field, GraphQLField)
    assert foo_field.args == {
        "bar_foo": GraphQLArgument(GraphQLString, out_name="bar_foo")
    }


def test_objecttype_with_possible_types():
    class MyObjectType(ObjectType):
        """Description"""

        class Meta:
            possible_types = (dict,)

        foo_bar = String()

    typemap = TypeMap([MyObjectType])
    graphql_type = typemap["MyObjectType"]
    assert graphql_type.is_type_of
    assert graphql_type.is_type_of({}, None) is True
    assert graphql_type.is_type_of(MyObjectType(), None) is False


def test_resolve_type_with_missing_type():
    class MyObjectType(ObjectType):
        foo_bar = String()

    class MyOtherObjectType(ObjectType):
        fizz_buzz = String()

    def resolve_type_func(root, info):
        return MyOtherObjectType

    typemap = TypeMap([MyObjectType])
    with pytest.raises(AssertionError) as excinfo:
        resolve_type(resolve_type_func, typemap, "MyOtherObjectType", {}, {})

    assert "MyOtherObjectTyp" in str(excinfo.value)
