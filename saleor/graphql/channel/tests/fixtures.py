import pytest
from django.conf import settings

from ....channel.models import Channel
from ....tax.models import TaxConfiguration


def _create_channel_tax_configuration(channel):
    tax_configuration = TaxConfiguration.objects.create(
        channel=channel, metadata={"key": "value"}, private_metadata={"key": "value"}
    )
    tax_configuration.country_exceptions.create(country="PL")
    tax_configuration.country_exceptions.create(country="DE")


@pytest.fixture
def channel_USD(db):
    slug = settings.DEFAULT_CHANNEL_SLUG
    channel = Channel.objects.create(
        name="Main Channel",
        slug=slug,
        currency_code="USD",
        default_country="US",
        is_active=True,
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
    )
    _create_channel_tax_configuration(channel)
    return channel
