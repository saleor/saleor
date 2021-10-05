from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from .const import (
    FILL_MISSING_ADDRESS,
    MERCHANT_CODE,
    SP_CODE,
    TERMINAL_ID,
    USE_SANDBOX,
)


@dataclass
class ApiConfig:
    test_mode: bool
    fill_missing_address: bool
    merchant_code: str
    terminal_id: str
    sp_code: str


class PaymentStatus(str, Enum):
    SUCCESS = "00"
    PENDING = "10"
    FAILED = "20"


@dataclass
class PaymentResult:
    status: PaymentStatus
    psp_reference: str = ""
    raw_response: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


def get_api_config(connection_params: dict) -> ApiConfig:
    return ApiConfig(
        test_mode=connection_params[USE_SANDBOX],
        fill_missing_address=connection_params[FILL_MISSING_ADDRESS],
        merchant_code=connection_params[MERCHANT_CODE],
        sp_code=connection_params[SP_CODE],
        terminal_id=connection_params[TERMINAL_ID],
    )
