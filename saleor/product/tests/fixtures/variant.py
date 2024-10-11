import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from ....warehouse.models import Stock
from ... import ProductTypeKind
from ...models import (
    Product,
    ProductChannelListing,
    ProductMedia,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
    VariantMedia,
)


@pytest.fixture
def variant_without_inventory_tracking(
    product_type_without_variant, category, warehouse, channel_USD
):
    product = Product.objects.create(
        name="Test product without inventory tracking",
        slug="test-product-without-tracking",
        product_type=product_type_without_variant,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime.now(tz=datetime.UTC),
    )
    variant = ProductVariant.objects.create(
        product=product,
        sku="tracking123",
        track_inventory=False,
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=0)
    return variant


@pytest.fixture
def variant(product, channel_USD) -> ProductVariant:
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_A", external_reference="SKU_A"
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    return product_variant


@pytest.fixture
def variant_with_translations(variant):
    variant.translations.create(language_code="pl", name="OldVariant PL")
    variant.translations.create(language_code="de", name="OldVariant DE")
    return variant


@pytest.fixture
def variant_with_image(variant, image_list, media_root):
    media = ProductMedia.objects.create(product=variant.product, image=image_list[0])
    VariantMedia.objects.create(variant=variant, media=media)
    return variant


@pytest.fixture
def variant_with_many_stocks(variant, warehouses_with_shipping_zone):
    warehouses = warehouses_with_shipping_zone
    Stock.objects.bulk_create(
        [
            Stock(warehouse=warehouses[0], product_variant=variant, quantity=4),
            Stock(warehouse=warehouses[1], product_variant=variant, quantity=3),
        ]
    )
    return variant


@pytest.fixture
def variant_on_promotion(
    product, channel_USD, promotion_rule, warehouse
) -> ProductVariant:
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_A", external_reference="SKU_A"
    )
    price_amount = Decimal(10)
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=price_amount,
        discounted_price_amount=price_amount,
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(
        warehouse=warehouse, product_variant=product_variant, quantity=10
    )

    promotion_rule.variants.add(product_variant)
    reward_value = promotion_rule.reward_value
    discount_amount = price_amount * reward_value / 100

    variant_channel_listing = product_variant.channel_listings.get(channel=channel_USD)

    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount - reward_value
    )
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=promotion_rule,
        discount_amount=discount_amount,
        currency=channel_USD.currency_code,
    )

    return product_variant


@pytest.fixture
def preorder_variant_global_threshold(product, channel_USD):
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_A_P", is_preorder=True, preorder_global_threshold=10
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    return product_variant


@pytest.fixture
def preorder_variant_channel_threshold(product, channel_USD):
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_B_P", is_preorder=True, preorder_global_threshold=None
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
        preorder_quantity_threshold=10,
    )
    return product_variant


@pytest.fixture
def preorder_variant_global_and_channel_threshold(product, channel_USD, channel_PLN):
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_C_P", is_preorder=True, preorder_global_threshold=10
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=product_variant,
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
                preorder_quantity_threshold=8,
            ),
            ProductVariantChannelListing(
                variant=product_variant,
                channel=channel_PLN,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_PLN.currency_code,
                preorder_quantity_threshold=4,
            ),
        ]
    )
    return product_variant


@pytest.fixture
def preorder_variant_with_end_date(product, channel_USD):
    product_variant = ProductVariant.objects.create(
        product=product,
        sku="SKU_D_P",
        is_preorder=True,
        preorder_global_threshold=10,
        preorder_end_date=timezone.now() + datetime.timedelta(days=10),
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    return product_variant


@pytest.fixture
def variant_with_many_stocks_different_shipping_zones(
    variant, warehouses_with_different_shipping_zone
):
    warehouses = warehouses_with_different_shipping_zone
    Stock.objects.bulk_create(
        [
            Stock(warehouse=warehouses[0], product_variant=variant, quantity=4),
            Stock(warehouse=warehouses[1], product_variant=variant, quantity=3),
        ]
    )
    return variant


@pytest.fixture
def gift_card_shippable_variant(shippable_gift_card_product, channel_USD, warehouse):
    product = shippable_gift_card_product
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_CARD_A", track_inventory=False
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(
        warehouse=warehouse, product_variant=product_variant, quantity=1
    )
    return product_variant


@pytest.fixture
def gift_card_non_shippable_variant(
    non_shippable_gift_card_product, channel_USD, warehouse
):
    product = non_shippable_gift_card_product
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_CARD_B", track_inventory=False
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(
        warehouse=warehouse, product_variant=product_variant, quantity=1
    )
    return product_variant


@pytest.fixture
def product_variant_list(product, channel_USD, channel_PLN):
    variants = list(
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(product=product, sku="1"),
                ProductVariant(product=product, sku="2"),
                ProductVariant(product=product, sku="3"),
                ProductVariant(product=product, sku="4"),
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
                price_amount=Decimal(10),
                discounted_price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_PLN,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                discounted_price_amount=Decimal(10),
                currency=channel_PLN.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[3],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                discounted_price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
        ]
    )
    return variants


@pytest.fixture
def variant_with_no_attributes(category, channel_USD):
    """Create a variant having no attributes, the same for the parent product."""
    product_type = ProductType.objects.create(
        name="Test product type",
        has_variants=True,
        is_shipping_required=True,
        kind=ProductTypeKind.NORMAL,
    )
    product = Product.objects.create(
        name="Test product",
        product_type=product_type,
        category=category,
    )
    variant = ProductVariant.objects.create(product=product, sku="123")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        cost_price_amount=Decimal(1),
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    return variant
