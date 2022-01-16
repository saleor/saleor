from setuptools import setup

PLUGIN_PATH = "saleor.payment.gateways.cod"

setup(
    name="cod-payment-gateway",
    entry_points={
        "saleor.plugins": [
            f"{PLUGIN_PATH} = {PLUGIN_PATH}.plugin:CashGatewayPlugin",
        ],
    },
)
