import pytest

from .. import deprecated
from ..deprecated import deprecated as deprecated_decorator
from ..deprecated import warn_deprecation


def test_warn_deprecation(mocker):
    mocker.patch.object(deprecated.warnings, "warn")

    warn_deprecation("OH!")
    deprecated.warnings.warn.assert_called_with(
        "OH!", stacklevel=2, category=DeprecationWarning
    )


def test_deprecated_decorator(mocker):
    mocker.patch.object(deprecated, "warn_deprecation")

    @deprecated_decorator
    def my_func():
        return True

    result = my_func()
    assert result
    deprecated.warn_deprecation.assert_called_with(
        "Call to deprecated function my_func."
    )


def test_deprecated_class(mocker):
    mocker.patch.object(deprecated, "warn_deprecation")

    @deprecated_decorator
    class X:
        pass

    result = X()
    assert result
    deprecated.warn_deprecation.assert_called_with("Call to deprecated class X.")


def test_deprecated_decorator_text(mocker):
    mocker.patch.object(deprecated, "warn_deprecation")

    @deprecated_decorator("Deprecation text")
    def my_func():
        return True

    result = my_func()
    assert result
    deprecated.warn_deprecation.assert_called_with(
        "Call to deprecated function my_func (Deprecation text)."
    )


def test_deprecated_class_text(mocker):
    mocker.patch.object(deprecated, "warn_deprecation")

    @deprecated_decorator("Deprecation text")
    class X:
        pass

    result = X()
    assert result
    deprecated.warn_deprecation.assert_called_with(
        "Call to deprecated class X (Deprecation text)."
    )


def test_deprecated_other_object(mocker):
    mocker.patch.object(deprecated, "warn_deprecation")

    with pytest.raises(TypeError):
        deprecated_decorator({})
