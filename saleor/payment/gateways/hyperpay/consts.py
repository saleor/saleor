"""Constants for HyperPay payment gateway."""

PLUGIN_ID = "saleor.payments.hyperpay"
PLUGIN_NAME = "HyperPay"
PLUGIN_DESCRIPTION = """
HyperPay Payment Gateway integration.

Supports credit card, debit card, MADA, and other payment methods available in the MENA region.
"""

# API Endpoints
TEST_API_URL = "https://eu-test.oppwa.com"
PRODUCTION_API_URL = "https://eu-prod.oppwa.com"

# API Paths
CHECKOUT_PATH = "/v1/checkouts"
PAYMENT_STATUS_PATH = "/v1/checkouts/{checkout_id}/payment"
REFUND_PATH = "/v1/payments/{payment_id}"
BACKOFFICE_PATH = "/v1/payments"

# Payment Types
PAYMENT_TYPE_DEBIT = "DB"  # Debit (immediate capture)
PAYMENT_TYPE_PREAUTH = "PA"  # Pre-authorization
PAYMENT_TYPE_CAPTURE = "CP"  # Capture
PAYMENT_TYPE_REVERSAL = "RV"  # Reversal (void)
PAYMENT_TYPE_REFUND = "RF"  # Refund

# Result Codes - Success patterns
SUCCESS_CODES_PATTERN = r"^(000\.000\.|000\.100\.1|000\.[36])"
PENDING_CODES_PATTERN = r"^(000\.200)"
REVIEW_CODES_PATTERN = r"^(000\.400\.0[^3]|000\.400\.100)"

# Successful transaction result code prefixes
RESULT_CODE_SUCCESS = "000.000."
RESULT_CODE_SUCCESS_MANUAL_REVIEW = "000.400."
RESULT_CODE_PENDING = "000.200."

# Error result code prefixes
RESULT_CODE_FAILED = "800."
RESULT_CODE_REJECTED = "100."
RESULT_CODE_REJECTED_BANK = "200."
RESULT_CODE_REJECTED_COMMUNICATION = "300."
RESULT_CODE_REJECTED_SYSTEM = "400."
RESULT_CODE_REJECTED_ASYNC = "500."
RESULT_CODE_REJECTED_RISK = "600."
RESULT_CODE_REJECTED_CONFIG = "700."
RESULT_CODE_REJECTED_REFERENCE = "800."
RESULT_CODE_REJECTED_ADDRESS = "900."

# 3D Secure status codes
THREEDS_RESULT_CODES = [
    "000.200.000",  # Transaction pending (waiting for 3DS)
    "000.200.100",  # Successfully created checkout
]

# Default supported currencies
DEFAULT_SUPPORTED_CURRENCIES = "SAR, AED, BHD, QAR, OMR, KWD, EGP, USD, EUR"

# Default payment brands
DEFAULT_PAYMENT_BRANDS = "VISA MASTER MADA"
