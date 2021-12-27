import pytest
from django.conf import settings

from ....channel.models import Channel


@pytest.fixture
def channel_USD(db):
    slug = settings.DEFAULT_CHANNEL_SLUG
    return Channel.objects.create(
        name="Main Channel",
        slug=slug,
        currency_code="USD",
        default_country="US",
        is_active=True,
    )


@pytest.fixture
def other_channel_USD(db):
    return Channel.objects.create(
        name="Other Channel USD",
        slug="other-usd",
        currency_code="USD",
        default_country="US",
        is_active=True,
    )


@pytest.fixture
def channel_PLN(db):
    return Channel.objects.create(
        name="Channel PLN",
        slug="c-pln",
        currency_code="PLN",
        default_country="PL",
        is_active=True,
    )


@pytest.fixture
def channel_JPY(db):
    return Channel.objects.create(
        name="Channel=JPY",
        slug="c-jpy",
        currency_code="JPY",
        default_country="JP",
        is_active=True,
    )
