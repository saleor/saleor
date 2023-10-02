# This integration is currently supporting the settlement type 02 - NP Atobarai.
NP_ATOBARAI = "02"
NP_ATOBARAI_WIZ = "03"

# Custom timeout, as NetProtections recommends a timeout of around 30s.
REQUEST_TIMEOUT = 30

NP_PLUGIN_ID = "saleor.payments.np-atobarai"

NP_TEST_URL = "https://ctcp.np-payment-gateway.com/v1"
NP_URL = "https://cp.np-payment-gateway.com/v1"

MERCHANT_CODE = "merchant_code"
FILL_MISSING_ADDRESS = "fill_missing_address"
SP_CODE = "sp_code"
TERMINAL_ID = "terminal_id"
USE_SANDBOX = "use_sandbox"
SHIPPING_COMPANY = "shipping_company"
SKU_AS_NAME = "sku_in_invoice"

SHIPPING_COMPANY_CODES = [
    "50000",
    "59010",
    "59020",
    "59030",
    "59040",
    "59041",
    "59042",
    "59043",
    "59050",
    "59060",
    "59080",
    "59090",
    "59110",
    "59140",
    "59150",
    "59100",
    "59160",
    "55555",
]

PRE_FULFILLMENT_ERROR_CODE = "E0100115"
ALREADY_REREGISTERED_ERROR_CODE = "E0131006"
EXCEEDED_NUMBER_OF_REREGISTRATIONS_ERROR_CODE = "E0131011"

SHIPPING_COMPANY_CODE_METADATA_KEY = "np-atobarai.pd-company-code"
