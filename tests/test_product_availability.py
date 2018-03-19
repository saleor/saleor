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

    variant_1 = product.variants.create(sku='test-1')
    variant_2 = product.variants.create(sku='test-2')

    # create empty stock records
    variant_1.quantity = 0
    variant_2.quantity = 0
    variant_1.save()
    variant_2.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.OUT_OF_STOCK

    # assign quantity to only one stock record
    variant_1.quantity = 5
    variant_1.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.LOW_STOCK

    # both stock records have some quantity
    variant_2.quantity = 5
    variant_2.save()
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
    variant.quantity = 0
    variant.save()
    status = get_variant_availability_status(variant)
    assert status == VariantAvailabilityStatus.OUT_OF_STOCK

    variant.quantity = 5
    variant.save()
    status = get_variant_availability_status(variant)


def test_availability(product, monkeypatch, settings, taxes):
    availability = get_availability(product)
    assert availability.price_range == product.get_price_range()
    assert availability.price_range_local_currency is None

    monkeypatch.setattr(
        'django_prices_openexchangerates.models.get_rates',
        lambda c: {'PLN': Mock(rate=2)})
    settings.DEFAULT_COUNTRY = 'PL'
    settings.OPENEXCHANGERATES_API_KEY = 'fake-key'
    availability = get_availability(product, local_currency='PLN')
    assert availability.price_range_local_currency.start.currency == 'PLN'
    assert availability.available

    availability = get_availability(product, taxes=taxes)
    assert availability.price_range.start.tax.amount
    assert availability.price_range.stop.tax.amount
    assert availability.price_range_undiscounted.start.tax.amount
    assert availability.price_range_undiscounted.stop.tax.amount
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
