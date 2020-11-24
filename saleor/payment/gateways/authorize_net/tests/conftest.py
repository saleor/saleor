import pytest

from ....interface import GatewayConfig


@pytest.fixture
def authorize_net_gateway_config():
    return GatewayConfig(
        gateway_name="authorize_net",
        auto_capture=True,
        supported_currencies="USD",
        connection_params={
            "api_login_id": "public",
            "transaction_key": "secret",
            "client_key": "public",
            "use_sandbox": True
        }
    )


@pytest.fixture()
def authorize_net_payment(payment_dummy):
    return payment_dummy