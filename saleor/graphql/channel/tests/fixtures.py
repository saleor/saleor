import pytest

from ....channel.models import Channel


@pytest.fixture
def channel(db):
    return Channel.objects.create(name="Main Channel", slug="main", currency_code="USD")
