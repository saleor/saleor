from setuptools import setup

PLUGIN_PATH = "saleor.payment.gateways.tabby"

setup(
    name="tabby-payment-gateway",
    entry_points={
        "saleor.plugins": [
            f"{PLUGIN_PATH} = {PLUGIN_PATH}.plugin:TabbyGatewayPlugin",
        ],
    },
)
