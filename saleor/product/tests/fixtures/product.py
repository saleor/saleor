import datetime
import itertools
import random
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.core.files import File
from django.db import connection

from ....attribute import AttributeInputType, AttributeType
from ....attribute.models import Attribute, AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....core.postgres import FlatConcatSearchVector
from ....warehouse.models import Stock
from ... import ProductMediaTypes, ProductTypeKind
from ...models import (
    Product,
    ProductChannelListing,
    ProductMedia,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ...search import prepare_product_search_vector_value


@pytest.fixture
def product_with_product_attributes(
    product_type_with_product_attributes, non_default_category
):
    return Product.objects.create(
        name="product_with_product_attributes",
        slug="product-with-product-attributes",
        product_type=product_type_with_product_attributes,
        category=non_default_category,
    )


@pytest.fixture
def product_with_variant_attributes(
    product_type_with_variant_attributes, non_default_category
):
    return Product.objects.create(
        name="product_with_variant_attributes",
        slug="product-with-variant-attributes",
        product_type=product_type_with_variant_attributes,
        category=non_default_category,
    )


@pytest.fixture
def product(product_type, category, warehouse, channel_USD, default_tax_class):
    product_attr = product_type.product_attributes.first()
    product_attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-11",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="10.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )

    associate_attribute_values_to_instance(
        product, {product_attr.pk: [product_attr_value]}
    )

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(product=product, sku="123")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    associate_attribute_values_to_instance(
        variant, {variant_attr.pk: [variant_attr_value]}
    )

    return product


@pytest.fixture
def product_with_translations(product):
    product.translations.create(language_code="pl", name="OldProduct PL")
    product.translations.create(language_code="de", name="OldProduct DE")

    return product


@pytest.fixture
def shippable_gift_card_product(
    shippable_gift_card_product_type, category, warehouse, channel_USD
):
    product_type = shippable_gift_card_product_type

    product = Product.objects.create(
        name="Shippable gift card",
        slug="shippable-gift-card",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="100.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )

    variant = ProductVariant.objects.create(
        product=product, sku="958", track_inventory=False
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(100),
        discounted_price_amount=Decimal(100),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=1)

    return product


@pytest.fixture
def product_price_0(category, warehouse, channel_USD):
    product_type = ProductType.objects.create(
        name="Type with no shipping",
        slug="no-shipping",
        has_variants=False,
        is_shipping_required=False,
    )
    product = Product.objects.create(
        name="Test product",
        slug="test-product-4",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_C")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(0),
        discounted_price_amount=Decimal(0),
        cost_price_amount=Decimal(0),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=1)
    return product


@pytest.fixture
def product_in_channel_JPY(product, channel_JPY, warehouse_JPY):
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_JPY,
        is_published=True,
        discounted_price_amount="1200",
        currency=channel_JPY.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )
    variant = product.variants.get()
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_JPY,
        price_amount=Decimal(1200),
        discounted_price_amount=Decimal(1200),
        cost_price_amount=Decimal(300),
        currency=channel_JPY.currency_code,
    )
    Stock.objects.create(warehouse=warehouse_JPY, product_variant=variant, quantity=10)
    return product


@pytest.fixture
def non_shippable_gift_card_product(
    non_shippable_gift_card_product_type, category, warehouse, channel_USD
):
    product_type = non_shippable_gift_card_product_type

    product = Product.objects.create(
        name="Non shippable gift card",
        slug="non-shippable-gift-card",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="200.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )

    variant = ProductVariant.objects.create(
        product=product, sku="785", track_inventory=False
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(250),
        discounted_price_amount=Decimal(250),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=1)

    return product


@pytest.fixture
def product_with_rich_text_attribute(
    product_type_with_rich_text_attribute, category, warehouse, channel_USD
):
    product_attr = product_type_with_rich_text_attribute.product_attributes.first()
    product_attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-11",
        product_type=product_type_with_rich_text_attribute,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="10.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )

    associate_attribute_values_to_instance(
        product, {product_attr.pk: [product_attr_value]}
    )

    variant_attr = product_type_with_rich_text_attribute.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(product=product, sku="123")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    associate_attribute_values_to_instance(
        variant, {variant_attr.pk: [variant_attr_value]}
    )
    return [product, variant]


@pytest.fixture
def product_with_collections(
    product, published_collection, unpublished_collection, collection
):
    product.collections.add(*[published_collection, unpublished_collection, collection])
    return product


@pytest.fixture
def product_available_in_many_channels(product, channel_PLN, channel_USD):
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_PLN,
        is_published=True,
    )
    variant = product.variants.get()
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(50),
        discounted_price_amount=Decimal(50),
        cost_price_amount=Decimal(1),
        currency=channel_PLN.currency_code,
    )
    return product


@pytest.fixture
def product_with_single_variant(product_type, category, warehouse, channel_USD):
    product = Product.objects.create(
        name="Test product with single variant",
        slug="test-product-with-single-variant",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_SINGLE_VARIANT")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(1.99),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=101)
    return product


@pytest.fixture
def product_with_two_variants(product_type, category, warehouse, channel_USD):
    product = Product.objects.create(
        name="Test product with two variants",
        slug="test-product-with-two-variant",
        product_type=product_type,
        category=category,
    )

    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )

    variants = [
        ProductVariant(
            product=product,
            sku=f"Product variant #{i}",
        )
        for i in (1, 2)
    ]
    ProductVariant.objects.bulk_create(variants)
    variants_channel_listing = [
        ProductVariantChannelListing(
            variant=variant,
            channel=channel_USD,
            price_amount=Decimal(10),
            discounted_price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )
        for variant in variants
    ]
    ProductVariantChannelListing.objects.bulk_create(variants_channel_listing)
    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=warehouse,
                product_variant=variant,
                quantity=10,
            )
            for variant in variants
        ]
    )
    product.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product)
    )
    product.save(update_fields=["search_vector"])

    return product


@pytest.fixture
def product_with_variant_with_two_attributes(
    color_attribute, size_attribute, category, warehouse, channel_USD
):
    product_type = ProductType.objects.create(
        name="Type with two variants",
        slug="two-variants",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.variant_attributes.add(color_attribute)
    product_type.variant_attributes.add(size_attribute)

    product = Product.objects.create(
        name="Test product with two variants",
        slug="test-product-with-two-variant",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )

    variant = ProductVariant.objects.create(product=product, sku="prodVar1")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )

    associate_attribute_values_to_instance(
        variant, {color_attribute.pk: [color_attribute.values.first()]}
    )
    associate_attribute_values_to_instance(
        variant, {size_attribute.pk: [size_attribute.values.first()]}
    )

    return product


@pytest.fixture
def product_with_variant_with_external_media(
    color_attribute,
    size_attribute,
    category,
    warehouse,
    channel_USD,
):
    product_type = ProductType.objects.create(
        name="Type with two variants",
        slug="two-variants",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.variant_attributes.add(color_attribute)
    product_type.variant_attributes.add(size_attribute)

    product = Product.objects.create(
        name="Test product with two variants",
        slug="test-product-with-two-variant",
        product_type=product_type,
        category=category,
    )
    media_obj = ProductMedia.objects.create(
        product=product,
        external_url="https://www.youtube.com/watch?v=di8_dJ3Clyo",
        alt="video_1",
        type=ProductMediaTypes.VIDEO,
        oembed_data="{}",
    )
    product.media.add(media_obj)

    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )

    variant = ProductVariant.objects.create(product=product, sku="prodVar1")
    variant.media.add(media_obj)
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )

    associate_attribute_values_to_instance(
        variant, {color_attribute.pk: [color_attribute.values.first()]}
    )
    associate_attribute_values_to_instance(
        variant, {size_attribute.pk: [size_attribute.values.first()]}
    )

    return product


@pytest.fixture
def product_with_variant_with_file_attribute(
    color_attribute, file_attribute, category, warehouse, channel_USD
):
    product_type = ProductType.objects.create(
        name="Type with variant and file attribute",
        slug="type-with-file-attribute",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.variant_attributes.add(file_attribute)

    product = Product.objects.create(
        name="Test product with variant and file attribute",
        slug="test-product-with-variant-and-file-attribute",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )

    variant = ProductVariant.objects.create(
        product=product,
        sku="prodVarTest",
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )

    associate_attribute_values_to_instance(
        variant, {file_attribute.pk: [file_attribute.values.first()]}
    )

    return product


@pytest.fixture
def product_with_multiple_values_attributes(product, product_type) -> Product:
    attribute = Attribute.objects.create(
        slug="modes",
        name="Available Modes",
        input_type=AttributeInputType.MULTISELECT,
        type=AttributeType.PRODUCT_TYPE,
    )

    attr_val_1 = AttributeValue.objects.create(
        attribute=attribute, name="Eco Mode", slug="eco"
    )
    attr_val_2 = AttributeValue.objects.create(
        attribute=attribute, name="Performance Mode", slug="power"
    )

    product_type.product_attributes.clear()
    product_type.product_attributes.add(attribute)

    associate_attribute_values_to_instance(
        product, {attribute.pk: [attr_val_1, attr_val_2]}
    )
    return product


@pytest.fixture
def product_with_default_variant(
    product_type_without_variant, category, warehouse, channel_USD
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-3",
        product_type=product_type_without_variant,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )
    variant = ProductVariant.objects.create(
        product=product, sku="1234", track_inventory=True
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=100)

    product.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product)
    )
    product.save(update_fields=["search_vector"])

    return product


@pytest.fixture
def product_without_shipping(category, warehouse, channel_USD):
    product_type = ProductType.objects.create(
        name="Type with no shipping",
        slug="no-shipping",
        kind=ProductTypeKind.NORMAL,
        has_variants=False,
        is_shipping_required=False,
    )
    product = Product.objects.create(
        name="Test product",
        slug="test-product-4",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_E")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=1)
    return product


@pytest.fixture
def product_without_category(product):
    product.category = None
    product.save()
    product.channel_listings.all().update(is_published=False)
    return product


@pytest.fixture
def product_list(
    product_type, category, warehouse, channel_USD, channel_PLN, default_tax_class
):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    products = list(
        Product.objects.bulk_create(
            [
                Product(
                    name="Test product 1",
                    slug="test-product-a",
                    description_plaintext="big blue product",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
                Product(
                    name="Test product 2",
                    slug="test-product-b",
                    description_plaintext="big orange product",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
                Product(
                    name="Test product 3",
                    slug="test-product-c",
                    description_plaintext="small red",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
            ]
        )
    )
    ProductChannelListing.objects.bulk_create(
        [
            ProductChannelListing(
                product=products[0],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=10,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
                available_for_purchase_at=(
                    datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC)
                ),
            ),
            ProductChannelListing(
                product=products[1],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=20,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
                available_for_purchase_at=(
                    datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC)
                ),
            ),
            ProductChannelListing(
                product=products[2],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=30,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
                available_for_purchase_at=(
                    datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC)
                ),
            ),
        ]
    )
    variants = list(
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(
                    product=products[0],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
                ProductVariant(
                    product=products[1],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
                ProductVariant(
                    product=products[2],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
            ]
        )
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=variants[0],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                discounted_price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(20),
                discounted_price_amount=Decimal(20),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(30),
                discounted_price_amount=Decimal(30),
                currency=channel_USD.currency_code,
            ),
        ]
    )
    stocks = []
    for variant in variants:
        stocks.append(Stock(warehouse=warehouse, product_variant=variant, quantity=100))
    Stock.objects.bulk_create(stocks)

    for product in products:
        associate_attribute_values_to_instance(product, {product_attr.pk: [attr_value]})
        product.search_vector = FlatConcatSearchVector(
            *prepare_product_search_vector_value(product)
        )

    Product.objects.bulk_update(products, ["search_vector"])

    return products


@pytest.fixture
def product_list_with_variants_many_channel(
    product_type, category, channel_USD, channel_PLN, default_tax_class
):
    products = list(
        Product.objects.bulk_create(
            [
                Product(
                    name="Test product 1",
                    slug="test-product-a",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
                Product(
                    name="Test product 2",
                    slug="test-product-b",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
                Product(
                    name="Test product 3",
                    slug="test-product-c",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
            ]
        )
    )
    ProductChannelListing.objects.bulk_create(
        [
            # Channel: USD
            ProductChannelListing(
                product=products[0],
                channel=channel_USD,
                is_published=True,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
            ),
            # Channel: PLN
            ProductChannelListing(
                product=products[1],
                channel=channel_PLN,
                is_published=True,
                currency=channel_PLN.currency_code,
                visible_in_listings=True,
            ),
            ProductChannelListing(
                product=products[2],
                channel=channel_PLN,
                is_published=True,
                currency=channel_PLN.currency_code,
                visible_in_listings=True,
            ),
        ]
    )
    variants = list(
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(
                    product=products[0],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
                ProductVariant(
                    product=products[1],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
                ProductVariant(
                    product=products[2],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
            ]
        )
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            # Channel: USD
            ProductVariantChannelListing(
                variant=variants[0],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            # Channel: PLN
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_PLN,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(20),
                currency=channel_PLN.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_PLN,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(30),
                currency=channel_PLN.currency_code,
            ),
        ]
    )
    return products


@pytest.fixture
def product_list_with_many_channels(product_list, channel_PLN):
    ProductChannelListing.objects.bulk_create(
        [
            ProductChannelListing(
                product=product_list[0],
                channel=channel_PLN,
                is_published=True,
            ),
            ProductChannelListing(
                product=product_list[1],
                channel=channel_PLN,
                is_published=True,
            ),
            ProductChannelListing(
                product=product_list[2],
                channel=channel_PLN,
                is_published=True,
            ),
        ]
    )
    return product_list


@pytest.fixture
def product_list_unpublished(product_list, channel_USD):
    products = Product.objects.filter(pk__in=[product.pk for product in product_list])
    ProductChannelListing.objects.filter(
        product__in=products, channel=channel_USD
    ).update(is_published=False)
    return products


@pytest.fixture
def product_list_published(product_list, channel_USD):
    products = Product.objects.filter(pk__in=[product.pk for product in product_list])
    ProductChannelListing.objects.filter(
        product__in=products, channel=channel_USD
    ).update(is_published=True)
    return products


@pytest.fixture
def product_with_image(product, image, media_root):
    ProductMedia.objects.create(product=product, image=image)
    return product


@pytest.fixture
def product_with_image_list(product, image_list, media_root):
    ProductMedia.objects.create(product=product, image=image_list[0])
    ProductMedia.objects.create(product=product, image=image_list[1])
    return product


@pytest.fixture
def product_with_image_list_and_one_null_sort_order(product_with_image_list):
    """Return a product with mixed sorting order.

    As we allow to have `null` in `sort_order` in database, but our logic
    covers changing any new `null` values to proper `int` need to execute
    raw SQL query on database to test behavior of `null` `sort_order`.

    SQL query behavior:
    Updates one of the product media `sort_order` to `null`.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE PRODUCT_PRODUCTMEDIA
            SET SORT_ORDER = NULL
            WHERE ID IN (
                SELECT ID FROM PRODUCT_PRODUCTMEDIA
                WHERE PRODUCT_ID = %s
                ORDER BY ID
                LIMIT 1
            )
            """,
            [product_with_image_list.pk],
        )
    product_with_image_list.refresh_from_db()
    return product_with_image_list


@pytest.fixture
def unavailable_product(product_type, category, channel_USD, default_tax_class):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-5",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=False,
        visible_in_listings=False,
    )
    return product


@pytest.fixture
def unavailable_product_with_variant(
    product_type, category, warehouse, channel_USD, default_tax_class
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-6",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=False,
        visible_in_listings=False,
    )

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(
        product=product,
        sku="123",
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    associate_attribute_values_to_instance(
        variant, {variant_attr.pk: [variant_attr_value]}
    )
    return product


@pytest.fixture
def product_with_images(
    product_type, category, media_root, channel_USD, default_tax_class
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-7",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    file_mock_0 = MagicMock(spec=File, name="FileMock0")
    file_mock_0.name = "image0.jpg"
    file_mock_1 = MagicMock(spec=File, name="FileMock1")
    file_mock_1.name = "image1.jpg"
    product.media.create(image=file_mock_0)
    product.media.create(image=file_mock_1)
    return product


@pytest.fixture
def lots_of_products_with_variants(product_type, channel_USD):
    def chunks(iterable, size):
        it = iter(iterable)
        chunk = tuple(itertools.islice(it, size))
        while chunk:
            yield chunk
            chunk = tuple(itertools.islice(it, size))

    variants_per_product = 4
    products_count = 10000
    slug_generator = (f"test-slug-{i}" for i in range(products_count))

    for batch in chunks(range(products_count), 500):
        batch_len = len(batch)
        variants = []
        product_listings = []
        products = [
            Product(
                name=i,
                slug=next(slug_generator),
                product_type_id=product_type.pk,
            )
            for i in range(batch_len)
        ]
        for product in Product.objects.bulk_create(products):
            product_listings.append(
                ProductChannelListing(
                    channel=channel_USD,
                    product=product,
                    visible_in_listings=True,
                    available_for_purchase_at="2022-01-01",
                    currency=channel_USD.currency_code,
                )
            )
            for x in range(variants_per_product):
                variant = ProductVariant(name=x, product_id=product.id)
                variants.append(variant)
        ProductVariant.objects.bulk_create(variants)
        variant_listings = []
        for variant in variants:
            price = random.randint(1, 100)
            variant_listings.append(
                ProductVariantChannelListing(
                    variant=variant,
                    channel=channel_USD,
                    currency=channel_USD.currency_code,
                    price_amount=price,
                    discounted_price_amount=price,
                )
            )
        ProductVariantChannelListing.objects.bulk_create(variant_listings)
        ProductChannelListing.objects.bulk_create(product_listings)
    return Product.objects.all()
