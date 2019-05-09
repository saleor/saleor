from functools import partial

import pytest

from ..argument import Argument
from ..field import Field
from ..scalars import String
from ..structures import NonNull
from .utils import MyLazyType


class MyInstance(object):
    value = "value"
    value_func = staticmethod(lambda: "value_func")

    def value_method(self):
        return "value_method"


def test_field_basic():
    MyType = object()
    args = {"my arg": Argument(True)}

    def resolver():
        return None

    deprecation_reason = "Deprecated now"
    description = "My Field"
    my_default = "something"
    field = Field(
        MyType,
        name="name",
        args=args,
        resolver=resolver,
        description=description,
        deprecation_reason=deprecation_reason,
        default_value=my_default,
    )
    assert field.name == "name"
    assert field.args == args
    assert field.resolver == resolver
    assert field.deprecation_reason == deprecation_reason
    assert field.description == description
    assert field.default_value == my_default


def test_field_required():
    MyType = object()
    field = Field(MyType, required=True)
    assert isinstance(field.type, NonNull)
    assert field.type.of_type == MyType


def test_field_default_value_not_callable():
    MyType = object()
    try:
        Field(MyType, default_value=lambda: True)
    except AssertionError as e:
        # substring comparison for py 2/3 compatibility
        assert "The default value can not be a function but received" in str(e)


def test_field_source():
    MyType = object()
    field = Field(MyType, source="value")
    assert field.resolver(MyInstance(), None) == MyInstance.value


def test_field_with_lazy_type():
    MyType = object()
    field = Field(lambda: MyType)
    assert field.type == MyType


def test_field_with_lazy_partial_type():
    MyType = object()
    field = Field(partial(lambda: MyType))
    assert field.type == MyType


def test_field_with_string_type():
    field = Field("graphene.types.tests.utils.MyLazyType")
    assert field.type == MyLazyType


def test_field_not_source_and_resolver():
    MyType = object()
    with pytest.raises(Exception) as exc_info:
        Field(MyType, source="value", resolver=lambda: None)
    assert (
        str(exc_info.value)
        == "A Field cannot have a source and a resolver in at the same time."
    )


def test_field_source_func():
    MyType = object()
    field = Field(MyType, source="value_func")
    assert field.resolver(MyInstance(), None) == MyInstance.value_func()


def test_field_source_method():
    MyType = object()
    field = Field(MyType, source="value_method")
    assert field.resolver(MyInstance(), None) == MyInstance().value_method()


def test_field_source_as_argument():
    MyType = object()
    field = Field(MyType, source=String())
    assert "source" in field.args
    assert field.args["source"].type == String


def test_field_name_as_argument():
    MyType = object()
    field = Field(MyType, name=String())
    assert "name" in field.args
    assert field.args["name"].type == String


def test_field_source_argument_as_kw():
    MyType = object()
    field = Field(MyType, b=NonNull(True), c=Argument(None), a=NonNull(False))
    assert list(field.args.keys()) == ["b", "c", "a"]
    assert isinstance(field.args["b"], Argument)
    assert isinstance(field.args["b"].type, NonNull)
    assert field.args["b"].type.of_type is True
    assert isinstance(field.args["c"], Argument)
    assert field.args["c"].type is None
    assert isinstance(field.args["a"], Argument)
    assert isinstance(field.args["a"].type, NonNull)
    assert field.args["a"].type.of_type is False
