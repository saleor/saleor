import pytest

from .....discount.models import Sale, SaleChannelListing
from .....product.models import Category


@pytest.fixture
def sales_list(channel_USD):
    sales = Sale.objects.bulk_create([Sale(name="Sale1"), Sale(name="Sale2")])
    values = [15, 5]
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                channel=channel_USD,
                discount_value=values[i],
                currency=channel_USD.currency_code,
            )
            for i, sale in enumerate(sales)
        ]
    )
    return list(sales)


@pytest.fixture
def homepage_collection(
    site_settings,
    collection,
    product_list_published,
    product_with_image,
    product_with_variant_with_two_attributes,
    product_with_multiple_values_attributes,
    product_without_shipping,
    non_default_category,
    sales_list,
):
    product_with_image.category = non_default_category
    product_with_image.save()

    collection.products.set(product_list_published)

    collection.products.add(product_with_image)
    collection.products.add(product_with_variant_with_two_attributes)
    collection.products.add(product_with_multiple_values_attributes)
    collection.products.add(product_without_shipping)

    site_settings.homepage_collection = collection
    site_settings.save(update_fields=["homepage_collection"])
    return collection


@pytest.fixture
def category_with_products(
    product_with_image,
    product_list_published,
    product_with_variant_with_two_attributes,
    product_with_multiple_values_attributes,
    product_without_shipping,
    sales_list,
):
    category = Category.objects.create(name="Category", slug="cat")

    product_list_published.update(category=category)

    product_with_image.category = category
    product_with_image.save()
    product_with_variant_with_two_attributes.category = category
    product_with_variant_with_two_attributes.save()
    product_with_multiple_values_attributes.category = category
    product_with_multiple_values_attributes.save()
    product_without_shipping.category = category
    product_without_shipping.save()

    return category
