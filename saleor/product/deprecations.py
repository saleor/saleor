import functools
import warnings

from saleor.core.deprecations import SaleorDeprecationWarning

DEPRECATION_WARNING_MESSAGE = (
    "Support for Digital Content is deprecated and will be removed in Saleor v3.23.0. "
    "This functionality is legacy and undocumented, and is not part of the supported "
    "API. Users should not rely on this behavior."
)


def deprecated_digital_content(func):
    @functools.wraps(func)
    def _inner(*args, **kwargs):
        warnings.warn(
            message=DEPRECATION_WARNING_MESSAGE,
            category=SaleorDeprecationWarning,
            stacklevel=1,
        )
        return func(*args, **kwargs)

    return _inner
