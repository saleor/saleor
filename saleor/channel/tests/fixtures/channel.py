import pytest
from django.conf import settings

from ....channel import AllocationStrategy
from ....channel.models import Channel
from ....graphql.channel.tests.benchmark import CHANNEL_COUNT_IN_BENCHMARKS
from ....tax.tests.fixtures.utils import create_channel_tax_configuration
from ....warehouse.models import Warehouse


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
    create_channel_tax_configuration(channel)
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
    create_channel_tax_configuration(channel)
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
    create_channel_tax_configuration(channel)
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
    create_channel_tax_configuration(channel)
    return channel


@pytest.fixture
def channels_for_benchmark(address):
    warehouses = [
        Warehouse(
            address=address,
            name=f"Example Warehouse {i}",
            slug=f"example-warehouse-{i}",
            email="test@example.com",
        )
        for i in range(CHANNEL_COUNT_IN_BENCHMARKS)
    ]
    created_warehouses = Warehouse.objects.bulk_create(warehouses)

    channels = [
        Channel(
            name=f"channel {i}",
            slug=f"channel-{i}",
        )
        for i in range(CHANNEL_COUNT_IN_BENCHMARKS)
    ]
    created_channels = Channel.objects.bulk_create(channels)

    for channel, warehouse in zip(created_channels, created_warehouses):
        channel.warehouses.add(warehouse)

    return created_channels
