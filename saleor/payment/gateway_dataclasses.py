from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional


@dataclass
class GatewayResponse:
    """Dataclass for storing gateway response"""

    is_success: bool
    kind: str
    amount: Decimal
    currency: str
    transaction_id: str
    error: Optional[str]
    raw_response: Optional[Dict[str, str]] = None
