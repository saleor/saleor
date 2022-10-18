import pytest
from django.conf import settings

from ....channel import AllocationStrategy
from ....channel.models import Channel
from ....tax import TaxCalculationStrategy
from ....tax.models import TaxConfiguration


def _create_channel_tax_configuration(channel):
    # Use TAX_APP strategy, to enable calculations with plugins by default.
    tax_configuration = TaxConfiguration.objects.create(
        channel=channel,
        metadata={"key": "value"},
        private_metadata={"key": "value"},
        tax_calculation_strategy=TaxCalculationStrategy.TAX_APP,
    )
    tax_configuration.country_exceptions.create(
        country="PL",
        tax_calculation_strategy=TaxCalculationStrategy.TAX_APP,
    )
    tax_configuration.country_exceptions.create(
        country="DE",
        tax_calculation_strategy=TaxCalculationStrategy.TAX_APP,
    )


@pytest.fixture
def channel_USD(db):
    slug = settings.DEFAULT_CHANNEL_SLUG
    channel = Channel.objects.create(
        name="Main Channel",
        slug=slug,
        currency_code="USD",
        default_country="US",
        is_active=True,
        allocation_strategy=AllocationStrategy.PRIORITIZE_HIGH_STOCK,
    )
    _create_channel_tax_configuration(channel)
    return channel


@pytest.fixture
def other_channel_USD(db):
    channel = Channel.objects.create(
        name="Other Channel USD",
        slug="other-usd",
        currency_code="USD",
        default_country="US",
        is_active=True,
        allocation_strategy=AllocationStrategy.PRIORITIZE_HIGH_STOCK,
    )
    _create_channel_tax_configuration(channel)
    return channel


@pytest.fixture
def channel_PLN(db):
    channel = Channel.objects.create(
        name="Channel PLN",
        slug="c-pln",
        currency_code="PLN",
        default_country="PL",
        is_active=True,
        allocation_strategy=AllocationStrategy.PRIORITIZE_HIGH_STOCK,
    )
    _create_channel_tax_configuration(channel)
    return channel


@pytest.fixture
def channel_JPY(db):
    channel = Channel.objects.create(
        name="Channel=JPY",
        slug="c-jpy",
        currency_code="JPY",
        default_country="JP",
        is_active=True,
        allocation_strategy=AllocationStrategy.PRIORITIZE_HIGH_STOCK,
    )
    _create_channel_tax_configuration(channel)
    return channel
