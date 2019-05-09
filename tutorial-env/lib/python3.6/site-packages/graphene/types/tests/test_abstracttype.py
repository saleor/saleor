from .. import abstracttype
from ..abstracttype import AbstractType
from ..field import Field
from ..objecttype import ObjectType
from ..unmountedtype import UnmountedType


class MyType(ObjectType):
    pass


class MyScalar(UnmountedType):
    def get_type(self):
        return MyType


def test_abstract_objecttype_warn_deprecation(mocker):
    mocker.patch.object(abstracttype, "warn_deprecation")

    class MyAbstractType(AbstractType):
        field1 = MyScalar()

    assert abstracttype.warn_deprecation.called


def test_generate_objecttype_inherit_abstracttype():
    class MyAbstractType(AbstractType):
        field1 = MyScalar()

    class MyObjectType(ObjectType, MyAbstractType):
        field2 = MyScalar()

    assert MyObjectType._meta.description is None
    assert MyObjectType._meta.interfaces == ()
    assert MyObjectType._meta.name == "MyObjectType"
    assert list(MyObjectType._meta.fields.keys()) == ["field1", "field2"]
    assert list(map(type, MyObjectType._meta.fields.values())) == [Field, Field]
