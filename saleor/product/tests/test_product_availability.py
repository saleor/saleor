import datetime
from unittest.mock import Mock

from prices import Money, TaxedMoney, TaxedMoneyRange

from ...plugins.manager import PluginsManager
from .. import models
from ..utils.availability import get_product_availability


def test_availability(stock, monkeypatch, settings):
    product = stock.product_variant.product
    channel_listing = product.channel_listing.first()
    taxed_price = TaxedMoney(Money("10.0", "USD"), Money("12.30", "USD"))
    monkeypatch.setattr(
        PluginsManager, "apply_taxes_to_product", Mock(return_value=taxed_price)
    )
    availability = get_product_availability(
        product=product,
        channel_listing=channel_listing,
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
        channel_listing=channel_listing,
        variants=product.variants.all(),
        collections=[],
        discounts=[],
        local_currency="PLN",
        country="PL",
    )
    assert availability.price_range_local_currency.start.currency == "PLN"

    availability = get_product_availability(
        product=product,
        channel_listing=channel_listing,
        variants=product.variants.all(),
        collections=[],
        discounts=[],
        country="PL",
    )
    assert availability.price_range.start.tax.amount
    assert availability.price_range.stop.tax.amount
    assert availability.price_range_undiscounted.start.tax.amount
    assert availability.price_range_undiscounted.stop.tax.amount


def test_available_products_only_published(product_list, channel_USD):
    channel_listing = product_list[0].channel_listing.get()
    channel_listing.is_published = False
    channel_listing.save(update_fields=["is_published"])

    available_products = models.Product.objects.published(channel_USD.slug)
    assert available_products.count() == 2
    assert all(
        [
            product.channel_listing.get(channel__slug=channel_USD.slug).is_published
            for product in available_products
        ]
    )


def test_available_products_only_available(product_list, channel_USD):
    channel_listing = product_list[0].channel_listing.get()
    date_tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    channel_listing.publication_date = date_tomorrow
    channel_listing.save(update_fields=["publication_date"])

    available_products = models.Product.objects.published(channel_USD.slug)
    assert available_products.count() == 2
    assert all(
        [
            product.channel_listing.get(channel__slug=channel_USD.slug).is_published
            for product in available_products
        ]
    )


def test_available_products_available_from_yesterday(product_list, channel_USD):
    channel_listing = product_list[0].channel_listing.get()
    date_tomorrow = datetime.date.today() - datetime.timedelta(days=1)
    channel_listing.publication_date = date_tomorrow
    channel_listing.save(update_fields=["publication_date"])

    available_products = models.Product.objects.published(channel_USD.slug)
    assert available_products.count() == 3
    assert all(
        [
            product.channel_listing.get(channel__slug=channel_USD.slug).is_published
            for product in available_products
        ]
    )


def test_available_products_available_without_channel_listings(
    product_list, channel_PLN
):
    available_products = models.Product.objects.published(channel_PLN.slug)
    assert available_products.count() == 0


def test_available_products_available_with_many_channels(
    product_list_with_many_channels, channel_USD, channel_PLN
):
    models.ProductChannelListing.objects.filter(
        product__in=product_list_with_many_channels, channel=channel_PLN
    ).update(is_published=False)

    available_products = models.Product.objects.published(channel_PLN.slug)
    assert available_products.count() == 0
    available_products = models.Product.objects.published(channel_USD.slug)
    assert available_products.count() == 3


def test_available_products_with_variants(product_list, channel_USD):
    product = product_list[0]
    product.variants.all().delete()

    available_products = models.Product.objects.published_with_variants(
        channel_USD.slug
    )
    assert available_products.count() == 2


def test_visible_to_customer_user(customer_user, product_list, channel_USD):
    product = product_list[0]
    product.variants.all().delete()

    available_products = models.Product.objects.visible_to_user(
        customer_user, channel_USD.slug
    )
    assert available_products.count() == 2


def test_visible_to_staff_user(
    customer_user, product_list, channel_USD, permission_manage_products
):
    product = product_list[0]
    product.variants.all().delete()
    customer_user.user_permissions.add(permission_manage_products)

    available_products = models.Product.objects.visible_to_user(
        customer_user, channel_USD.slug
    )
    assert available_products.count() == 3
