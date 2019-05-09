import pytest

from ..annotate import annotate


def func(a, b, *c, **d):
    pass


annotations = {"a": int, "b": str, "c": list, "d": dict}


def func_with_annotations(a, b, *c, **d):
    pass


func_with_annotations.__annotations__ = annotations


def test_annotate_with_no_params():
    annotated_func = annotate(func, _trigger_warning=False)
    assert annotated_func.__annotations__ == {}


def test_annotate_with_params():
    annotated_func = annotate(_trigger_warning=False, **annotations)(func)
    assert annotated_func.__annotations__ == annotations


def test_annotate_with_wront_params():
    with pytest.raises(Exception) as exc_info:
        annotate(p=int, _trigger_warning=False)(func)

    assert (
        str(exc_info.value)
        == 'The key p is not a function parameter in the function "func".'
    )
