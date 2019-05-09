
from ..argument import Argument
from ..field import Field
from ..inputfield import InputField
from ..inputobjecttype import InputObjectType
from ..objecttype import ObjectType
from ..scalars import Boolean, String
from ..schema import Schema
from ..unmountedtype import UnmountedType


class MyType(object):
    pass


class MyScalar(UnmountedType):
    def get_type(self):
        return MyType


def test_generate_inputobjecttype():
    class MyInputObjectType(InputObjectType):
        """Documentation"""

    assert MyInputObjectType._meta.name == "MyInputObjectType"
    assert MyInputObjectType._meta.description == "Documentation"
    assert MyInputObjectType._meta.fields == {}


def test_generate_inputobjecttype_with_meta():
    class MyInputObjectType(InputObjectType):
        class Meta:
            name = "MyOtherInputObjectType"
            description = "Documentation"

    assert MyInputObjectType._meta.name == "MyOtherInputObjectType"
    assert MyInputObjectType._meta.description == "Documentation"


def test_generate_inputobjecttype_with_fields():
    class MyInputObjectType(InputObjectType):
        field = Field(MyType)

    assert "field" in MyInputObjectType._meta.fields


def test_ordered_fields_in_inputobjecttype():
    class MyInputObjectType(InputObjectType):
        b = InputField(MyType)
        a = InputField(MyType)
        field = MyScalar()
        asa = InputField(MyType)

    assert list(MyInputObjectType._meta.fields.keys()) == ["b", "a", "field", "asa"]


def test_generate_inputobjecttype_unmountedtype():
    class MyInputObjectType(InputObjectType):
        field = MyScalar(MyType)

    assert "field" in MyInputObjectType._meta.fields
    assert isinstance(MyInputObjectType._meta.fields["field"], InputField)


def test_generate_inputobjecttype_as_argument():
    class MyInputObjectType(InputObjectType):
        field = MyScalar()

    class MyObjectType(ObjectType):
        field = Field(MyType, input=MyInputObjectType())

    assert "field" in MyObjectType._meta.fields
    field = MyObjectType._meta.fields["field"]
    assert isinstance(field, Field)
    assert field.type == MyType
    assert "input" in field.args
    assert isinstance(field.args["input"], Argument)
    assert field.args["input"].type == MyInputObjectType


def test_generate_inputobjecttype_inherit_abstracttype():
    class MyAbstractType(object):
        field1 = MyScalar(MyType)

    class MyInputObjectType(InputObjectType, MyAbstractType):
        field2 = MyScalar(MyType)

    assert list(MyInputObjectType._meta.fields.keys()) == ["field1", "field2"]
    assert [type(x) for x in MyInputObjectType._meta.fields.values()] == [
        InputField,
        InputField,
    ]


def test_generate_inputobjecttype_inherit_abstracttype_reversed():
    class MyAbstractType(object):
        field1 = MyScalar(MyType)

    class MyInputObjectType(MyAbstractType, InputObjectType):
        field2 = MyScalar(MyType)

    assert list(MyInputObjectType._meta.fields.keys()) == ["field1", "field2"]
    assert [type(x) for x in MyInputObjectType._meta.fields.values()] == [
        InputField,
        InputField,
    ]


def test_inputobjecttype_of_input():
    class Child(InputObjectType):
        first_name = String()
        last_name = String()

        @property
        def full_name(self):
            return "{} {}".format(self.first_name, self.last_name)

    class Parent(InputObjectType):
        child = InputField(Child)

    class Query(ObjectType):
        is_child = Boolean(parent=Parent())

        def resolve_is_child(self, info, parent):
            return (
                isinstance(parent.child, Child)
                and parent.child.full_name == "Peter Griffin"
            )

    schema = Schema(query=Query)
    result = schema.execute(
        """query basequery {
        isChild(parent: {child: {firstName: "Peter", lastName: "Griffin"}})
    }
    """
    )
    assert not result.errors
    assert result.data == {"isChild": True}
