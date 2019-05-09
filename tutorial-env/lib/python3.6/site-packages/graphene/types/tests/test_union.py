import pytest

from ..field import Field
from ..objecttype import ObjectType
from ..union import Union
from ..unmountedtype import UnmountedType


class MyObjectType1(ObjectType):
    pass


class MyObjectType2(ObjectType):
    pass


def test_generate_union():
    class MyUnion(Union):
        """Documentation"""

        class Meta:
            types = (MyObjectType1, MyObjectType2)

    assert MyUnion._meta.name == "MyUnion"
    assert MyUnion._meta.description == "Documentation"
    assert MyUnion._meta.types == (MyObjectType1, MyObjectType2)


def test_generate_union_with_meta():
    class MyUnion(Union):
        class Meta:
            name = "MyOtherUnion"
            description = "Documentation"
            types = (MyObjectType1, MyObjectType2)

    assert MyUnion._meta.name == "MyOtherUnion"
    assert MyUnion._meta.description == "Documentation"


def test_generate_union_with_no_types():
    with pytest.raises(Exception) as exc_info:

        class MyUnion(Union):
            pass

    assert str(exc_info.value) == "Must provide types for Union MyUnion."


def test_union_can_be_mounted():
    class MyUnion(Union):
        class Meta:
            types = (MyObjectType1, MyObjectType2)

    my_union_instance = MyUnion()
    assert isinstance(my_union_instance, UnmountedType)
    my_union_field = my_union_instance.mount_as(Field)
    assert isinstance(my_union_field, Field)
    assert my_union_field.type == MyUnion
