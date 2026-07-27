import pytest


@pytest.fixture(autouse=True)
def setup_dummy_gateways(settings):
    settings.PLUGINS = [
        "saleor.plugins.tests.gateways.dummy.DummyGatewayPlugin",
        "saleor.plugins.tests.gateways.dummy_credit_card.DummyCreditCardGatewayPlugin",
    ]
    return settings


@pytest.fixture
def sample_gateway(settings):
    settings.PLUGINS += [
        "saleor.plugins.tests.sample_plugins.ActiveDummyPaymentGateway"
    ]
    return settings
