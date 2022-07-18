import pytest

from .....channel.models import Channel
from .....warehouse.models import Warehouse

CHANNEL_COUNT_IN_BENCHMARKS = 10


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
