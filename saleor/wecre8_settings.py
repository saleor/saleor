from saleor.settings import *  # noqa F405

LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

PLUGINS.append(  # noqa F405
    "saleor.payment.gateways.cod.plugin.CashGatewayPlugin",
)
