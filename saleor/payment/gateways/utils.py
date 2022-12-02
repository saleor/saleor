import warnings
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..interface import GatewayConfig


def require_active_plugin(fn):
    def wrapped(self, *args, **kwargs):
        previous = kwargs.get("previous_value", None)
        if not self.active:
            return previous
        return fn(self, *args, **kwargs)

    return wrapped


def get_supported_currencies(config: "GatewayConfig", gateway_name: str) -> List[str]:
    """Return supported currencies for given gateway configuration.

    If supported currencies are not specified, the default currency is used
    and a warning is raised.
    """
    supp_currencies = config.supported_currencies
    if not supp_currencies:
        currencies: List[str] = []
        warnings.warn(
            f"Supported currencies not configured for {gateway_name}, "
            "please configure supported currencies for this gateway."
        )
    else:
        currencies = [c.strip() for c in supp_currencies.split(",")]

    return currencies
