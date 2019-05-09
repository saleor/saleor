from functools import partial

import pytest

from ..scalars import String
from ..structures import List, NonNull
from .utils import MyLazyType


def test_list():
    _list = List(String)
    assert _list.of_type == String
    assert str(_list) == "[String]"


def test_list_with_unmounted_type():
    with pytest.raises(Exception) as exc_info:
        List(String())

    assert (
        str(exc_info.value)
        == "List could not have a mounted String() as inner type. Try with List(String)."
    )


def test_list_with_lazy_type():
    MyType = object()
    field = List(lambda: MyType)
    assert field.of_type == MyType


def test_list_with_lazy_partial_type():
    MyType = object()
    field = List(partial(lambda: MyType))
    assert field.of_type == MyType


def test_list_with_string_type():
    field = List("graphene.types.tests.utils.MyLazyType")
    assert field.of_type == MyLazyType


def test_list_inherited_works_list():
    _list = List(List(String))
    assert isinstance(_list.of_type, List)
    assert _list.of_type.of_type == String


def test_list_inherited_works_nonnull():
    _list = List(NonNull(String))
    assert isinstance(_list.of_type, NonNull)
    assert _list.of_type.of_type == String


def test_nonnull():
    nonnull = NonNull(String)
    assert nonnull.of_type == String
    assert str(nonnull) == "String!"


def test_nonnull_with_lazy_type():
    MyType = object()
    field = NonNull(lambda: MyType)
    assert field.of_type == MyType


def test_nonnull_with_lazy_partial_type():
    MyType = object()
    field = NonNull(partial(lambda: MyType))
    assert field.of_type == MyType


def test_nonnull_with_string_type():
    field = NonNull("graphene.types.tests.utils.MyLazyType")
    assert field.of_type == MyLazyType


def test_nonnull_inherited_works_list():
    _list = NonNull(List(String))
    assert isinstance(_list.of_type, List)
    assert _list.of_type.of_type == String


def test_nonnull_inherited_dont_work_nonnull():
    with pytest.raises(Exception) as exc_info:
        NonNull(NonNull(String))

    assert (
        str(exc_info.value)
        == "Can only create NonNull of a Nullable GraphQLType but got: String!."
    )


def test_nonnull_with_unmounted_type():
    with pytest.raises(Exception) as exc_info:
        NonNull(String())

    assert (
        str(exc_info.value)
        == "NonNull could not have a mounted String() as inner type. Try with NonNull(String)."
    )


def test_list_comparasion():
    list1 = List(String)
    list2 = List(String)
    list3 = List(None)

    list1_argskwargs = List(String, None, b=True)
    list2_argskwargs = List(String, None, b=True)

    assert list1 == list2
    assert list1 != list3
    assert list1_argskwargs == list2_argskwargs
    assert list1 != list1_argskwargs


def test_nonnull_comparasion():
    nonnull1 = NonNull(String)
    nonnull2 = NonNull(String)
    nonnull3 = NonNull(None)

    nonnull1_argskwargs = NonNull(String, None, b=True)
    nonnull2_argskwargs = NonNull(String, None, b=True)

    assert nonnull1 == nonnull2
    assert nonnull1 != nonnull3
    assert nonnull1_argskwargs == nonnull2_argskwargs
    assert nonnull1 != nonnull1_argskwargs
