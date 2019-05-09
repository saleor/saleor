
from ..resolver import (
    attr_resolver,
    dict_resolver,
    get_default_resolver,
    set_default_resolver,
)

args = {}
context = None
info = None

demo_dict = {"attr": "value"}


class demo_obj(object):
    attr = "value"


def test_attr_resolver():
    resolved = attr_resolver("attr", None, demo_obj, info, **args)
    assert resolved == "value"


def test_attr_resolver_default_value():
    resolved = attr_resolver("attr2", "default", demo_obj, info, **args)
    assert resolved == "default"


def test_dict_resolver():
    resolved = dict_resolver("attr", None, demo_dict, info, **args)
    assert resolved == "value"


def test_dict_resolver_default_value():
    resolved = dict_resolver("attr2", "default", demo_dict, info, **args)
    assert resolved == "default"


def test_get_default_resolver_is_attr_resolver():
    assert get_default_resolver() == attr_resolver


def test_set_default_resolver_workd():
    default_resolver = get_default_resolver()

    set_default_resolver(dict_resolver)
    assert get_default_resolver() == dict_resolver

    set_default_resolver(default_resolver)
