import pytest
from .. import get_default_backend, set_default_backend, GraphQLCoreBackend


def test_get_default_backend_returns_core_by_default():
    # type: () -> None
    backend = get_default_backend()
    assert isinstance(backend, GraphQLCoreBackend)


def test_set_default_backend():
    # type: () -> None
    default_backend = get_default_backend()
    new_backend = GraphQLCoreBackend()
    assert new_backend != default_backend
    set_default_backend(new_backend)
    assert get_default_backend() == new_backend


def test_set_default_backend_fails_if_invalid_backend():
    # type: () -> None
    default_backend = get_default_backend()
    with pytest.raises(Exception) as exc_info:
        set_default_backend(object())
    assert str(exc_info.value) == "backend must be an instance of GraphQLBackend."
    assert get_default_backend() == default_backend
