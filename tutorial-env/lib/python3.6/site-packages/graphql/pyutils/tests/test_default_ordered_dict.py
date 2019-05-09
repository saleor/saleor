import copy
import pickle

from pytest import raises

from graphql.pyutils.default_ordered_dict import DefaultOrderedDict


def test_will_missing_will_set_value_from_factory():
    d = DefaultOrderedDict(list)
    f = d["foo"]
    assert isinstance(f, list)
    assert d["foo"] is f


def test_preserves_input_order():
    d = DefaultOrderedDict(list)
    d["a"].append(1)
    d["b"].append(2)
    d["c"].append(3)
    d["a"].append(4)

    assert list(d.keys()) == ["a", "b", "c"]
    assert list(d.values()) == [[1, 4], [2], [3]]


def test_will_act_list_default_dict_if_no_factory_defined():
    d = DefaultOrderedDict()

    with raises(KeyError) as excinfo:
        assert d["test"]

    assert str(excinfo.value) == "'test'"


def test_will_repr_properly():
    d = DefaultOrderedDict(list, [("a", 1), ("b", 2)])
    assert repr(d) == "DefaultOrderedDict({}, [('a', 1), ('b', 2)])".format(list)


def test_requires_callable_default_factory():
    with raises(TypeError) as excinfo:
        DefaultOrderedDict("not callable")

    assert str(excinfo.value) == "first argument must be callable"


def test_picklable():
    d = DefaultOrderedDict(list, [("a", 1), ("b", 2)])
    d_copied = pickle.loads(pickle.dumps(d))

    assert d_copied == d
    assert d.default_factory == d_copied.default_factory

    d = DefaultOrderedDict(None, [("a", 1), ("b", 2)])
    d_copied = pickle.loads(pickle.dumps(d))

    assert d_copied == d
    assert d.default_factory == d_copied.default_factory


def test_copy():
    d = DefaultOrderedDict(list, [("a", [1, 2]), ("b", [3, 4])])
    d_copied = copy.copy(d)

    assert d_copied == d
    assert d.default_factory == d_copied.default_factory
    assert d_copied["a"] is d["a"]
    assert d_copied["b"] is d["b"]

    d_copied = d.copy()

    assert d_copied == d
    assert d.default_factory == d_copied.default_factory
    assert d_copied["a"] is d["a"]
    assert d_copied["b"] is d["b"]


def test_deep_copy():
    d = DefaultOrderedDict(list, [("a", [1, 2]), ("b", [3, 4])])
    d_copied = copy.deepcopy(d)

    assert d_copied == d
    assert d.default_factory == d_copied.default_factory
    assert d_copied["a"] == d["a"]
    assert d_copied["a"] is not d["a"]
    assert d_copied["b"] == d["b"]
    assert d_copied["b"] is not d["b"]
