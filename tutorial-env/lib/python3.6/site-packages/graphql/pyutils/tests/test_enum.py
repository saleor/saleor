from ..enum import _is_dunder, _is_sunder


def test__is_dunder():
    dunder_names = ["__i__", "__test__"]
    non_dunder_names = ["test", "__test", "_test", "_test_", "test__", ""]

    for name in dunder_names:
        assert _is_dunder(name) is True

    for name in non_dunder_names:
        assert _is_dunder(name) is False


def test__is_sunder():
    sunder_names = ["_i_", "_test_"]

    non_sunder_names = ["__i__", "_i__", "__i_", ""]

    for name in sunder_names:
        assert _is_sunder(name) is True

    for name in non_sunder_names:
        assert _is_sunder(name) is False
