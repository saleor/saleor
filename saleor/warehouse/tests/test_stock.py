import pytest

from ..models import Stock

COUNTRY_CODE = "US"


@pytest.fixture
def variant_with_stocks_in_two_channels(
    variant, warehouses, shipping_zone, channel_USD, channel_PLN
):
    """Variant with stocks in warehouses across two channels.

    - warehouse_usd (warehouses[0]): linked to channel_USD and shipping_zone,
      has stock qty=10
    - warehouse_pln (warehouses[1]): linked to channel_PLN, no shipping zone,
      has stock qty=5
    """
    warehouse_usd = warehouses[0]
    warehouse_pln = warehouses[1]

    warehouse_usd.channels.set([channel_USD])
    warehouse_usd.shipping_zones.set([shipping_zone])

    warehouse_pln.channels.set([channel_PLN])
    warehouse_pln.shipping_zones.clear()

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=warehouse_usd,
                product_variant=variant,
                quantity=10,
            ),
            Stock(
                warehouse=warehouse_pln,
                product_variant=variant,
                quantity=5,
            ),
        ]
    )
    return variant


def test_stocks_for_country(variant_with_many_stocks, channel_USD):
    # when
    [stock1, stock2] = (
        Stock.objects.filter(product_variant=variant_with_many_stocks)
        .for_channel_and_country(channel_USD.slug, COUNTRY_CODE)
        .order_by("pk")
        .all()
    )

    # then
    warehouse1 = stock1.warehouse
    warehouse2 = stock2.warehouse
    assert stock1.quantity == 4
    assert COUNTRY_CODE in warehouse1.countries
    assert stock2.quantity == 3
    assert COUNTRY_CODE in warehouse2.countries


def test_stock_for_country_does_not_exists(product, warehouse, channel_PLN):
    # given
    shipping_zone = warehouse.shipping_zones.first()
    shipping_zone.countries = [COUNTRY_CODE]
    shipping_zone.save(update_fields=["countries"])
    warehouse.refresh_from_db()
    fake_country_code = "PL"
    assert fake_country_code not in warehouse.countries

    # when
    stock_qs = Stock.objects.for_channel_and_country(
        channel_PLN.slug,
        fake_country_code,
    )

    # then
    assert not stock_qs.exists()


def test_stocks_for_country_warehouse_with_given_channel_do_not_exist(
    variant_with_many_stocks, channel_PLN
):
    # when
    stock_qs = (
        Stock.objects.filter(product_variant=variant_with_many_stocks)
        .for_channel_and_country(channel_PLN.slug, COUNTRY_CODE)
        .order_by("pk")
        .all()
    )

    # then
    assert not stock_qs.exists()


def test_for_channel_returns_stocks_from_channel_warehouses(
    variant_with_stocks_in_two_channels, channel_USD
):
    # given
    variant = variant_with_stocks_in_two_channels

    # when
    result = list(
        Stock.objects.filter(product_variant=variant)
        .for_channel(channel_USD.slug)
        .all()
    )

    # then
    assert len(result) == 1
    assert result[0].quantity == 10


def test_for_channel_excludes_stocks_from_other_channel(
    variant_with_stocks_in_two_channels, channel_PLN
):
    # given
    variant = variant_with_stocks_in_two_channels

    # when
    result = list(
        Stock.objects.filter(product_variant=variant)
        .for_channel(channel_PLN.slug)
        .all()
    )

    # then
    assert len(result) == 1
    assert result[0].quantity == 5


def test_for_channel_not_available(variant_with_stocks_in_two_channels, channel_JPY):
    # given
    variant = variant_with_stocks_in_two_channels

    # when
    result = list(
        Stock.objects.filter(product_variant=variant)
        .for_channel(channel_JPY.slug)
        .all()
    )

    # then
    assert not result


# Tests for get_variant_stocks


def test_get_variant_stocks_with_shipping_zones(
    variant_with_stocks_in_two_channels, channel_USD
):
    # given
    variant = variant_with_stocks_in_two_channels

    # when
    result = list(
        Stock.objects.get_variant_stocks(
            channel_USD.slug,
            variant,
            country_code=COUNTRY_CODE,
            include_shipping_zones=True,
        )
    )

    # then
    assert len(result) == 1
    assert result[0].quantity == 10
    assert result[0].product_variant == variant


def test_get_variant_stocks_with_shipping_zones_no_zone_match(
    variant_with_stocks_in_two_channels, channel_USD, shipping_zone
):
    # given - restrict shipping zone to only one country, then query another
    variant = variant_with_stocks_in_two_channels
    shipping_zone.countries = ["PL"]
    shipping_zone.save(update_fields=["countries"])
    non_matching_country = "DE"

    # when
    result = list(
        Stock.objects.get_variant_stocks(
            channel_USD.slug,
            variant,
            country_code=non_matching_country,
            include_shipping_zones=True,
        )
    )

    # then - shipping zone only covers PL, so DE returns no stocks
    assert len(result) == 0


def test_get_variant_stocks_without_shipping_zones(
    variant_with_stocks_in_two_channels, channel_USD
):
    # given - clear shipping zones to prove they don't matter
    variant = variant_with_stocks_in_two_channels
    for warehouse in variant.stocks.all():
        warehouse = warehouse.warehouse
        warehouse.shipping_zones.clear()

    # when
    result = list(
        Stock.objects.get_variant_stocks(
            channel_USD.slug, variant, include_shipping_zones=False
        )
    )

    # then - still returned because only channel link matters
    assert len(result) == 1
    assert result[0].quantity == 10
    assert result[0].product_variant == variant


# Tests for get_variants_stocks


def test_get_variants_stocks_with_shipping_zones(
    variant_with_stocks_in_two_channels, channel_USD
):
    # given
    variant = variant_with_stocks_in_two_channels

    # when
    result = list(
        Stock.objects.get_variants_stocks(
            channel_USD.slug,
            [variant],
            country_code=COUNTRY_CODE,
            include_shipping_zones=True,
        )
    )

    # then
    assert len(result) == 1
    assert result[0].product_variant == variant
    assert result[0].quantity == 10


def test_get_variants_stocks_without_shipping_zones(
    variant_with_stocks_in_two_channels, channel_USD
):
    # given - clear shipping zones to prove they don't matter
    variant = variant_with_stocks_in_two_channels
    for stock in variant.stocks.all():
        stock.warehouse.shipping_zones.clear()

    # when
    result = list(
        Stock.objects.get_variants_stocks(
            channel_USD.slug, [variant], include_shipping_zones=False
        )
    )

    # then - still returned because only channel link matters
    assert len(result) == 1
    assert result[0].product_variant == variant
    assert result[0].quantity == 10


# Tests for get_product_stocks


def test_get_product_stocks_with_shipping_zones(
    variant_with_stocks_in_two_channels, channel_USD
):
    # given
    variant = variant_with_stocks_in_two_channels
    product = variant.product

    expected_count = Stock.objects.filter(
        product_variant__product=product,
        warehouse__channels=channel_USD,
    ).count()

    # when
    result = list(
        Stock.objects.get_product_stocks(
            channel_USD.slug,
            product,
            country_code=COUNTRY_CODE,
            include_shipping_zones=True,
        )
    )

    # then
    assert len(result) == expected_count
    for stock in result:
        assert stock.product_variant.product_id == product.pk


def test_get_product_stocks_without_shipping_zones(
    variant_with_stocks_in_two_channels, channel_USD
):
    # given - clear shipping zones to prove they don't matter
    variant = variant_with_stocks_in_two_channels
    product = variant.product
    for stock in variant.stocks.all():
        stock.warehouse.shipping_zones.clear()

    expected_count = Stock.objects.filter(
        product_variant__product=product,
        warehouse__channels=channel_USD,
    ).count()

    # when
    result = list(
        Stock.objects.get_product_stocks(
            channel_USD.slug, product, include_shipping_zones=False
        )
    )

    # then - still returned because only channel link matters
    assert len(result) == expected_count
    for stock in result:
        assert stock.product_variant.product_id == product.pk
