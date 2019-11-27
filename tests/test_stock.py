from saleor.stock.models import Stock


def test_stock_for_country(product):
    country_code = "US"
    stock = Stock.objects.get()
    warehouse = stock.warehouse
    assert country_code in warehouse.countries
    assert stock.warehouse == warehouse

    stock_qs = Stock.objects.for_country(country_code)
    assert stock_qs.count() == 1
    assert stock_qs.first() == stock
