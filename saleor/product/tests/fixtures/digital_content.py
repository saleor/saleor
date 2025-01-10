import datetime
from decimal import Decimal

import pytest

from ....warehouse.models import Stock
from ... import ProductTypeKind
from ...models import (
    DigitalContent,
    DigitalContentUrl,
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ..utils import create_image


@pytest.fixture
def digital_content(category, media_root, warehouse, channel_USD) -> DigitalContent:
    product_type = ProductType.objects.create(
        name="Digital Type",
        slug="digital-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=False,
        is_digital=True,
    )
    product = Product.objects.create(
        name="Test digital product",
        slug="test-digital-product",
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
    product_variant = ProductVariant.objects.create(product=product, sku="SKU_554")
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(
        product_variant=product_variant,
        warehouse=warehouse,
        quantity=5,
    )

    assert product_variant.is_digital()

    image_file, image_name = create_image()
    d_content = DigitalContent.objects.create(
        content_file=image_file,
        product_variant=product_variant,
        use_default_settings=True,
    )
    return d_content


@pytest.fixture
def digital_content_url(digital_content, order_line):
    return DigitalContentUrl.objects.create(content=digital_content, line=order_line)
