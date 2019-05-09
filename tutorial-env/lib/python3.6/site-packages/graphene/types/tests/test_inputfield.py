from functools import partial

from ..inputfield import InputField
from ..structures import NonNull
from .utils import MyLazyType


def test_inputfield_required():
    MyType = object()
    field = InputField(MyType, required=True)
    assert isinstance(field.type, NonNull)
    assert field.type.of_type == MyType


def test_inputfield_with_lazy_type():
    MyType = object()
    field = InputField(lambda: MyType)
    assert field.type == MyType


def test_inputfield_with_lazy_partial_type():
    MyType = object()
    field = InputField(partial(lambda: MyType))
    assert field.type == MyType


def test_inputfield_with_string_type():
    field = InputField("graphene.types.tests.utils.MyLazyType")
    assert field.type == MyLazyType
