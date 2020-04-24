import datetime
from unittest.mock import Mock

import pytest
from prices import Money, TaxedMoney, TaxedMoneyRange

from saleor.plugins.manager import PluginsManager
from saleor.product import ProductAvailabilityStatus, VariantAvailabilityStatus, models
from saleor.product.utils.availability import (
    get_product_availability,
    get_product_availability_status,
    get_variant_availability_status,
)
from saleor.warehouse.models import Stock


def test_product_availability_status(unavailable_product, warehouse):
    product = unavailable_product
    product.product_type.has_variants = True

    # product is not published
    status = get_product_availability_status(product, "US")
    assert status == ProductAvailabilityStatus.NOT_PUBLISHED

    product.is_published = True
    product.save()

    # product has no variants
    status = get_product_availability_status(product, "US")
    assert status == ProductAvailabilityStatus.VARIANTS_MISSSING

    variant_1 = product.variants.create(sku="test-1")
    variant_2 = product.variants.create(sku="test-2")
    # create empty stock records
    stock_1 = Stock.objects.create(
        product_variant=variant_1, warehouse=warehouse, quantity=0
    )
    stock_2 = Stock.objects.create(
        product_variant=variant_2, warehouse=warehouse, quantity=0
    )

    status = get_product_availability_status(product, "US")
    assert status == ProductAvailabilityStatus.OUT_OF_STOCK

    # assign quantity to only one stock record
    stock_1.quantity = 5
    stock_1.save()
    status = get_product_availability_status(product, "US")
    assert status == ProductAvailabilityStatus.LOW_STOCK

    # both stock records have some quantity
    stock_2.quantity = 5
    stock_2.save()
    status = get_product_availability_status(product, "US")
    assert status == ProductAvailabilityStatus.READY_FOR_PURCHASE

    # set product availability date from future
    product.publication_date = datetime.date.today() + datetime.timedelta(days=1)
    product.save()
    status = get_product_availability_status(product, "US")
    assert status == ProductAvailabilityStatus.NOT_YET_AVAILABLE


def test_variant_is_out_of_stock_when_product_is_unavalable(
    unavailable_product, warehouse
):
    product = unavailable_product
    product.product_type.has_variants = True

    variant = product.variants.create(sku="test")
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=0)

    status = get_variant_availability_status(variant, "US")
    assert status == VariantAvailabilityStatus.OUT_OF_STOCK


@pytest.mark.parametrize(
    "current_stock, expected_status",
    (
        (0, VariantAvailabilityStatus.OUT_OF_STOCK),
        (1, VariantAvailabilityStatus.AVAILABLE),
    ),
)
def test_variant_availability_status(stock, current_stock, expected_status):
    stock.quantity = current_stock
    stock.save(update_fields=["quantity"])
    variant = stock.product_variant

    status = get_variant_availability_status(variant, "US")
    assert status == expected_status


def test_variant_is_still_available_when_another_variant_is_unavailable(
    product_variant_list, warehouse
):
    """
    Ensure a variant is not incorrectly flagged as out of stock when another variant
    from the parent product is unavailable.
    """

    unavailable_variant, available_variant = product_variant_list[:2]
    Stock.objects.create(
        product_variant=unavailable_variant, warehouse=warehouse, quantity=0
    )
    Stock.objects.create(
        product_variant=available_variant, warehouse=warehouse, quantity=1,
    )

    status = get_variant_availability_status(available_variant, "US")
    assert status == VariantAvailabilityStatus.AVAILABLE

    status = get_variant_availability_status(unavailable_variant, "US")
    assert status == VariantAvailabilityStatus.OUT_OF_STOCK


def test_availability(stock, monkeypatch, settings):
    product = stock.product_variant.product
    taxed_price = TaxedMoney(Money("10.0", "USD"), Money("12.30", "USD"))
    monkeypatch.setattr(
        PluginsManager, "apply_taxes_to_product", Mock(return_value=taxed_price)
    )
    availability = get_product_availability(
        product=product,
        variants=product.variants.all(),
        collections=[],
        discounts=[],
        country="PL",
    )
    taxed_price_range = TaxedMoneyRange(start=taxed_price, stop=taxed_price)
    assert availability.price_range == taxed_price_range
    assert availability.price_range_local_currency is None

    monkeypatch.setattr(
        "django_prices_openexchangerates.models.get_rates",
        lambda c: {"PLN": Mock(rate=2)},
    )
    settings.DEFAULT_COUNTRY = "PL"
    settings.OPENEXCHANGERATES_API_KEY = "fake-key"
    availability = get_product_availability(
        product=product,
        variants=product.variants.all(),
        collections=[],
        discounts=[],
        local_currency="PLN",
        country="PL",
    )
    assert availability.price_range_local_currency.start.currency == "PLN"

    availability = get_product_availability(
        product=product,
        variants=product.variants.all(),
        collections=[],
        discounts=[],
        country="PL",
    )
    assert availability.price_range.start.tax.amount
    assert availability.price_range.stop.tax.amount
    assert availability.price_range_undiscounted.start.tax.amount
    assert availability.price_range_undiscounted.stop.tax.amount


def test_available_products_only_published(product_list):
    available_products = models.Product.objects.published()
    assert available_products.count() == 2
    assert all([product.is_published for product in available_products])


def test_available_products_only_available(product_list):
    product = product_list[0]
    date_tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    product.publication_date = date_tomorrow
    product.save()
    available_products = models.Product.objects.published()
    assert available_products.count() == 1
    assert all([product.is_visible for product in available_products])
