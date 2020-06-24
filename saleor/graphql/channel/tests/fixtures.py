import pytest

from ....channel.models import Channel


@pytest.fixture
def channel_USD(db):
    return Channel.objects.create(name="Main Channel", slug="main", currency_code="USD")


@pytest.fixture
def channel_PLN(db):
    return Channel.objects.create(name="Channel PLN", slug="c-pln", currency_code="PLN")
