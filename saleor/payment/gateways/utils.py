import warnings
from typing import TYPE_CHECKING, List

from django.conf import settings

if TYPE_CHECKING:
    from ..interface import GatewayConfig


def get_supported_currencies(config: "GatewayConfig", gateway_name: str) -> List[str]:
    currencies = config.supported_currencies
    print(config)
    if not currencies:
        currencies = [settings.DEFAULT_CURRENCY]
        warnings.warn(f"Default currency for {gateway_name} is used.")
    return currencies
