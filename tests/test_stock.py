from saleor.warehouse.models import Stock

COUNTRY_CODE = "US"


def test_stocks_for_country(variant_with_many_stocks):
    [stock1, stock2] = (
        Stock.objects.filter(product_variant=variant_with_many_stocks)
        .for_country(COUNTRY_CODE)
        .order_by("pk")
        .all()
    )
    warehouse1 = stock1.warehouse
    warehouse2 = stock2.warehouse
    assert stock1.quantity == 4
    assert COUNTRY_CODE in warehouse1.countries
    assert stock2.quantity == 3
    assert COUNTRY_CODE in warehouse2.countries


def test_stock_for_country_does_not_exists(product, warehouse):
    shipping_zone = warehouse.shipping_zones.first()
    shipping_zone.countries = [COUNTRY_CODE]
    shipping_zone.save(update_fields=["countries"])
    warehouse.refresh_from_db()
    fake_country_code = "PL"
    assert fake_country_code not in warehouse.countries
    stock_qs = Stock.objects.for_country(fake_country_code)
    assert not stock_qs.exists()
