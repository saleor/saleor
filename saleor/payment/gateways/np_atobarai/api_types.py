from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple

from .const import (
    FILL_MISSING_ADDRESS,
    MERCHANT_CODE,
    NP_TEST_URL,
    NP_URL,
    SHIPPING_COMPANY,
    SKU_AS_NAME,
    SP_CODE,
    TERMINAL_ID,
    USE_SANDBOX,
)


class NPResponse(NamedTuple):
    result: dict
    error_codes: list[str]
    raw_response: dict


def error_np_response(error_message: str) -> NPResponse:
    return NPResponse({}, [error_message], {})


@dataclass
class ApiConfig:
    url: str
    fill_missing_address: bool
    merchant_code: str
    terminal_id: str
    sp_code: str
    shipping_company: str
    sku_as_name: bool


class PaymentStatus(str, Enum):
    SUCCESS = "00"
    PENDING = "10"
    FAILED = "20"
    FOR_REREGISTRATION = "RE"


@dataclass
class PaymentResult:
    status: PaymentStatus
    psp_reference: str | None = None
    raw_response: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def error_payment_result(error_message: str) -> PaymentResult:
    return PaymentResult(
        status=PaymentStatus.FAILED, errors=[error_message], raw_response={}
    )


def errors_payment_result(errors: list[str], response: dict) -> PaymentResult:
    return PaymentResult(
        status=PaymentStatus.FAILED, errors=errors, raw_response=response
    )


def get_api_config(connection_params: dict) -> ApiConfig:
    url = NP_TEST_URL if connection_params[USE_SANDBOX] else NP_URL
    return ApiConfig(
        url=url,
        fill_missing_address=connection_params[FILL_MISSING_ADDRESS],
        merchant_code=connection_params[MERCHANT_CODE],
        sp_code=connection_params[SP_CODE],
        terminal_id=connection_params[TERMINAL_ID],
        shipping_company=connection_params[SHIPPING_COMPANY],
        sku_as_name=connection_params[SKU_AS_NAME],
    )
