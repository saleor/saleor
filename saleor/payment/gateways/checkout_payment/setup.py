from setuptools import setup

PLUGIN_PATH = "saleor.payment.gateways.checkout_payment"

setup(
    name="checkout-payment-gateway",
    entry_points={
        "saleor.plugins": [
            f"{PLUGIN_PATH} = {PLUGIN_PATH}.plugin:CheckoutGatewayPlugin",
        ],
    },
)
