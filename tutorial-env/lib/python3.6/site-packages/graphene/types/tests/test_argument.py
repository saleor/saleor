from functools import partial

import pytest

from ..argument import Argument, to_arguments
from ..field import Field
from ..inputfield import InputField
from ..scalars import String
from ..structures import NonNull


def test_argument():
    arg = Argument(String, default_value="a", description="desc", name="b")
    assert arg.type == String
    assert arg.default_value == "a"
    assert arg.description == "desc"
    assert arg.name == "b"


def test_argument_comparasion():
    arg1 = Argument(String, name="Hey", description="Desc", default_value="default")
    arg2 = Argument(String, name="Hey", description="Desc", default_value="default")

    assert arg1 == arg2
    assert arg1 != String()


def test_argument_required():
    arg = Argument(String, required=True)
    assert arg.type == NonNull(String)


def test_to_arguments():
    args = {"arg_string": Argument(String), "unmounted_arg": String(required=True)}

    my_args = to_arguments(args)
    assert my_args == {
        "arg_string": Argument(String),
        "unmounted_arg": Argument(String, required=True),
    }


def test_to_arguments_raises_if_field():
    args = {"arg_string": Field(String)}

    with pytest.raises(ValueError) as exc_info:
        to_arguments(args)

    assert str(exc_info.value) == (
        "Expected arg_string to be Argument, but received Field. Try using "
        "Argument(String)."
    )


def test_to_arguments_raises_if_inputfield():
    args = {"arg_string": InputField(String)}

    with pytest.raises(ValueError) as exc_info:
        to_arguments(args)

    assert str(exc_info.value) == (
        "Expected arg_string to be Argument, but received InputField. Try "
        "using Argument(String)."
    )


def test_argument_with_lazy_type():
    MyType = object()
    arg = Argument(lambda: MyType)
    assert arg.type == MyType


def test_argument_with_lazy_partial_type():
    MyType = object()
    arg = Argument(partial(lambda: MyType))
    assert arg.type == MyType
