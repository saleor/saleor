import re
import warnings
from typing import TYPE_CHECKING, List

from django.conf import settings

if TYPE_CHECKING:
    from ..interface import GatewayConfig


def get_supported_currencies(config: "GatewayConfig", gateway_name: str) -> List[str]:
    supp_currencies = config.supported_currencies
    if not supp_currencies:
        currencies = [settings.DEFAULT_CURRENCY]
        warnings.warn(
            f"Default currency used for {gateway_name}. "
            "DEFAULT_CURRENCY setting is deprecated, "
            "please configure supported currencies for this gateway."
        )
    else:
        currencies = [c.strip() for c in supp_currencies.split(",")]

    return currencies
