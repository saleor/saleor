import pytest

from ... import WarehouseClickAndCollectOption
from ...models import Stock, Warehouse


@pytest.fixture
def warehouse(address, shipping_zone, channel_USD):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Example Warehouse",
        slug="example-warehouse",
        email="test@example.com",
    )
    warehouse.shipping_zones.add(shipping_zone)
    warehouse.channels.add(channel_USD)
    return warehouse


@pytest.fixture
def warehouse_with_external_ref(address, shipping_zone, channel_USD):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Example Warehouse With Ref",
        slug="example-warehouse-with-ref",
        email="test@example.com",
        external_reference="example-warehouse-with-ref",
    )
    warehouse.shipping_zones.add(shipping_zone)
    warehouse.channels.add(channel_USD)
    return warehouse


@pytest.fixture
def warehouse_JPY(address, shipping_zone_JPY, channel_JPY):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Example Warehouse JPY",
        slug="example-warehouse-jpy",
        email="test-jpy@example.com",
    )
    warehouse.shipping_zones.add(shipping_zone_JPY)
    warehouse.channels.add(channel_JPY)
    return warehouse


@pytest.fixture
def warehouses(address, address_usa, channel_USD):
    warehouses = Warehouse.objects.bulk_create(
        [
            Warehouse(
                address=address.get_copy(),
                name="Warehouse PL",
                slug="warehouse1",
                email="warehouse1@example.com",
                external_reference="warehouse1",
            ),
            Warehouse(
                address=address_usa.get_copy(),
                name="Warehouse USA",
                slug="warehouse2",
                email="warehouse2@example.com",
                external_reference="warehouse2",
            ),
        ]
    )
    for warehouse in warehouses:
        warehouse.channels.add(channel_USD)
    return warehouses


@pytest.fixture
def warehouses_for_cc(address, shipping_zones, channel_USD):
    warehouses = Warehouse.objects.bulk_create(
        [
            Warehouse(
                address=address.get_copy(),
                name="Warehouse1",
                slug="warehouse1",
                email="warehouse1@example.com",
            ),
            Warehouse(
                address=address.get_copy(),
                name="Warehouse2",
                slug="warehouse2",
                email="warehouse2@example.com",
                click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES,
            ),
            Warehouse(
                address=address.get_copy(),
                name="Warehouse3",
                slug="warehouse3",
                email="warehouse3@example.com",
                click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
                is_private=False,
            ),
            Warehouse(
                address=address.get_copy(),
                name="Warehouse4",
                slug="warehouse4",
                email="warehouse4@example.com",
                click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
                is_private=False,
            ),
        ]
    )
    # add to shipping zones only not click and collect warehouses
    warehouses[0].shipping_zones.add(*shipping_zones)
    channel_USD.warehouses.add(*warehouses)
    return warehouses


@pytest.fixture
def warehouse_for_cc(address, product_variant_list, channel_USD):
    warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="Local Warehouse",
        slug="local-warehouse",
        email="local@example.com",
        is_private=False,
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
    )
    warehouse.channels.add(channel_USD)

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=warehouse, product_variant=product_variant_list[0], quantity=1
            ),
            Stock(
                warehouse=warehouse, product_variant=product_variant_list[1], quantity=2
            ),
            Stock(
                warehouse=warehouse, product_variant=product_variant_list[2], quantity=2
            ),
        ]
    )
    return warehouse


@pytest.fixture
def warehouses_with_shipping_zone(warehouses, shipping_zone):
    warehouses[0].shipping_zones.add(shipping_zone)
    warehouses[1].shipping_zones.add(shipping_zone)
    return warehouses


@pytest.fixture
def warehouses_with_different_shipping_zone(warehouses, shipping_zones):
    warehouses[0].shipping_zones.add(shipping_zones[0])
    warehouses[1].shipping_zones.add(shipping_zones[1])
    return warehouses


@pytest.fixture
def warehouse_no_shipping_zone(address, channel_USD):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Warehouse without shipping zone",
        slug="warehouse-no-shipping-zone",
        email="test2@example.com",
        external_reference="warehouse-no-shipping-zone",
    )
    warehouse.channels.add(channel_USD)
    return warehouse
