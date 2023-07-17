import pytest
from django.conf import settings

from ....channel import AllocationStrategy
from ....channel.models import Channel
from ....tax import TaxCalculationStrategy
from ....tax.models import TaxConfiguration


@pytest.fixture
def channel_generator(db):
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

    def create_channel(
        name=None,
        slug=None,
        currency_code=None,
        default_country=None,
        is_active=True,
        allocation_strategy=AllocationStrategy.PRIORITIZE_HIGH_STOCK,
        create_tax_config=True,
    ):
        channel = Channel.objects.create(
            name=name,
            slug=slug,
            currency_code=currency_code,
            default_country=default_country,
            is_active=is_active,
            allocation_strategy=allocation_strategy,
        )
        if create_tax_config:
            _create_channel_tax_configuration(channel)
        return channel

    return create_channel


@pytest.fixture
def channel_USD(channel_generator):
    return channel_generator(
        name="Main Channel",
        slug=settings.DEFAULT_CHANNEL_SLUG,
        currency_code="USD",
        default_country="US",
    )


@pytest.fixture
def other_channel_USD(channel_generator):
    return channel_generator(
        name="Other Channel USD",
        slug="other-usd",
        currency_code="USD",
        default_country="US",
    )


@pytest.fixture
def channel_PLN(channel_generator):
    return channel_generator(
        name="Channel PLN",
        slug="c-pln",
        currency_code="PLN",
        default_country="PL",
    )


@pytest.fixture
def channel_JPY(channel_generator):
    return channel_generator(
        name="Channel=JPY",
        slug="c-jpy",
        currency_code="JPY",
        default_country="JP",
    )
