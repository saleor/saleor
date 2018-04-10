import datetime
from unittest.mock import Mock

from saleor.product import (
    ProductAvailabilityStatus, VariantAvailabilityStatus, models)
from saleor.product.utils.availability import (
    get_availability, get_product_availability_status,
    get_variant_availability_status)


def test_product_availability_status(unavailable_product):
    product = unavailable_product
    product.product_type.has_variants = True

    # product is not published
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.NOT_PUBLISHED

    product.is_published = True
    product.save()

    # product has no variants
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.VARIANTS_MISSSING

    # product has variant but not stock records
    variant_1 = product.variants.create(sku='test-1')
    variant_2 = product.variants.create(sku='test-2')
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.NOT_CARRIED

    # create empty stock records
    stock_1 = variant_1.stock.create(quantity=0)
    stock_2 = variant_2.stock.create(quantity=0)
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.OUT_OF_STOCK

    # assign quantity to only one stock record
    stock_1.quantity = 5
    stock_1.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.LOW_STOCK

    # both stock records have some quantity
    stock_2.quantity = 5
    stock_2.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.READY_FOR_PURCHASE

    # set product availability date from future
    product.available_on = datetime.date.today() + datetime.timedelta(days=1)
    product.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.NOT_YET_AVAILABLE


def test_variant_availability_status(unavailable_product):
    product = unavailable_product
    product.product_type.has_variants = True

    variant = product.variants.create(sku='test')
    status = get_variant_availability_status(variant)
    assert status == VariantAvailabilityStatus.NOT_CARRIED

    stock = variant.stock.create(quantity=0)
    status = get_variant_availability_status(variant)
    assert status == VariantAvailabilityStatus.OUT_OF_STOCK

    stock.quantity = 5
    stock.save()
    status = get_variant_availability_status(variant)
    assert status == VariantAvailabilityStatus.AVAILABLE


def test_availability(product_in_stock, monkeypatch, settings):
    availability = get_availability(product_in_stock)
    assert availability.price_range == product_in_stock.get_price_range()
    assert availability.price_range_local_currency is None
    monkeypatch.setattr(
        'django_prices_openexchangerates.models.get_rates',
        lambda c: {'PLN': Mock(rate=2)})
    settings.DEFAULT_COUNTRY = 'PL'
    settings.OPENEXCHANGERATES_API_KEY = 'fake-key'
    availability = get_availability(product_in_stock, local_currency='PLN')
    assert availability.price_range_local_currency.start.currency == 'PLN'
    assert availability.available


def test_available_products_only_published(product_list):
    available_products = models.Product.objects.available_products()
    assert available_products.count() == 2
    assert all([product.is_published for product in available_products])


def test_available_products_only_available(product_list):
    product = product_list[0]
    date_tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    product.available_on = date_tomorrow
    product.save()
    available_products = models.Product.objects.available_products()
    assert available_products.count() == 1
    assert all([product.is_available() for product in available_products])
