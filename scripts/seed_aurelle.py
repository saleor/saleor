# ruff: noqa: T201
"""Idempotent development-data seeder for the AURELLE Cosmetics storefront.

Creates the categories, attributes (size/shade), product types, and all 17 cosmetics
products with their respective variants, prices, and warehouse stock.

Usage:
    python scripts/seed_aurelle.py
"""

import os
import sys
from pathlib import Path

import django

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from django.utils import timezone
from django.utils.text import slugify

from saleor.channel.models import Channel
from saleor.product.models import (
    Category,
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from saleor.attribute.models import Attribute, AttributeValue
from saleor.attribute.utils import associate_attribute_values_to_instance
from saleor.warehouse.models import Stock, Warehouse

DEFAULT_STOCK_QUANTITY = 100

# Definition of the 17 cosmetics products
PRODUCTS_DATA = [
    # 1. Skincare
    {
        "name": "Barrier Renewal Serum",
        "category": "Skincare",
        "product_type": "Skincare",
        "variants": [
            {"name": "30 ml", "price": "45.00", "attrs": {"size": "30 ml"}},
            {"name": "50 ml", "price": "65.00", "attrs": {"size": "50 ml"}},
        ]
    },
    {
        "name": "Cloud Cream Moisturizer",
        "category": "Skincare",
        "product_type": "Skincare",
        "variants": [
            {"name": "50 ml", "price": "55.00", "attrs": {"size": "50 ml"}},
        ]
    },
    {
        "name": "Gentle Milk Cleanser",
        "category": "Skincare",
        "product_type": "Skincare",
        "variants": [
            {"name": "Standard", "price": "32.00", "attrs": {}}
        ]
    },
    {
        "name": "Purifying Gel Cleanser",
        "category": "Skincare",
        "product_type": "Skincare",
        "variants": [
            {"name": "Standard", "price": "32.00", "attrs": {}}
        ]
    },
    {
        "name": "Mineral Defense SPF 50",
        "category": "Skincare",
        "product_type": "Skincare",
        "variants": [
            {"name": "Standard", "price": "42.00", "attrs": {}}
        ]
    },
    {
        "name": "Hydration Multiplier",
        "category": "Skincare",
        "product_type": "Skincare",
        "variants": [
            {"name": "Standard", "price": "38.00", "attrs": {}}
        ]
    },
    {
        "name": "Barrier Restore Cream",
        "category": "Skincare",
        "product_type": "Skincare",
        "variants": [
            {"name": "50 ml", "price": "48.00", "attrs": {"size": "50 ml"}},
        ]
    },
    {
        "name": "Cellular Renewal Complex",
        "category": "Skincare",
        "product_type": "Skincare",
        "variants": [
            {"name": "Standard", "price": "85.00", "attrs": {}}
        ]
    },
    # 2. Makeup
    {
        "name": "Skin Veil Foundation",
        "category": "Makeup",
        "product_type": "Makeup",
        "variants": [
            {"name": "Fair 01", "price": "52.00", "attrs": {"shade": "Fair 01"}},
            {"name": "Light 02", "price": "52.00", "attrs": {"shade": "Light 02"}},
            {"name": "Medium 03", "price": "52.00", "attrs": {"shade": "Medium 03"}},
            {"name": "Deep 04", "price": "52.00", "attrs": {"shade": "Deep 04"}},
            {"name": "Rich 05", "price": "52.00", "attrs": {"shade": "Rich 05"}},
        ]
    },
    {
        "name": "Soft Focus Concealer",
        "category": "Makeup",
        "product_type": "Makeup",
        "variants": [
            {"name": "Fair 01", "price": "36.00", "attrs": {"shade": "Fair 01"}},
            {"name": "Light 02", "price": "36.00", "attrs": {"shade": "Light 02"}},
            {"name": "Medium 03", "price": "36.00", "attrs": {"shade": "Medium 03"}},
            {"name": "Deep 04", "price": "36.00", "attrs": {"shade": "Deep 04"}},
            {"name": "Rich 05", "price": "36.00", "attrs": {"shade": "Rich 05"}},
        ]
    },
    {
        "name": "Satin Lip Colour",
        "category": "Makeup",
        "product_type": "Makeup",
        "variants": [
            {"name": "Standard", "price": "28.00", "attrs": {}}
        ]
    },
    # 3. Fragrance
    {
        "name": "No. 04 Amber Iris Eau de Parfum",
        "category": "Fragrance",
        "product_type": "Fragrance",
        "variants": [
            {"name": "30 ml", "price": "75.00", "attrs": {"size": "30 ml"}},
            {"name": "50 ml", "price": "110.00", "attrs": {"size": "50 ml"}},
            {"name": "100 ml", "price": "165.00", "attrs": {"size": "100 ml"}},
        ]
    },
    {
        "name": "No. 07 Fig Cedar Eau de Parfum",
        "category": "Fragrance",
        "product_type": "Fragrance",
        "variants": [
            {"name": "30 ml", "price": "75.00", "attrs": {"size": "30 ml"}},
            {"name": "50 ml", "price": "110.00", "attrs": {"size": "50 ml"}},
            {"name": "100 ml", "price": "165.00", "attrs": {"size": "100 ml"}},
        ]
    },
    # 4. Hair
    {
        "name": "Repair Ritual Hair Mask",
        "category": "Hair",
        "product_type": "Hair",
        "variants": [
            {"name": "Standard", "price": "48.00", "attrs": {}}
        ]
    },
    # 5. Bath and Body
    {
        "name": "Botanical Body Oil",
        "category": "Bath and Body",
        "product_type": "Bath and Body",
        "variants": [
            {"name": "Standard", "price": "38.00", "attrs": {}}
        ]
    },
    # 6. Beauty Tools
    {
        "name": "Sculpting Facial Tool",
        "category": "Beauty Tools",
        "product_type": "Beauty Tools",
        "variants": [
            {"name": "Standard", "price": "35.00", "attrs": {}}
        ]
    },
    # 7. Gifts
    {
        "name": "The Hydration Edit Gift Set",
        "category": "Gifts",
        "product_type": "Gifts",
        "variants": [
            {"name": "Standard", "price": "95.00", "attrs": {}}
        ]
    },
]

SHADE_HEX_MAPPING = {
    "Fair 01": "#f6f0e5",
    "Light 02": "#efe5d4",
    "Medium 03": "#dabfa0",
    "Deep 04": "#b88b66",
    "Rich 05": "#79523c"
}

def seed():
    channel = Channel.objects.filter(slug="default-channel").first()
    if not channel:
        channel = Channel.objects.create(
            name="Default Channel",
            slug="default-channel",
            currency_code="USD",
            is_active=True,
        )
    print(f"Using channel: {channel.slug} ({channel.currency_code})")

    warehouse = Warehouse.objects.first()
    if not warehouse:
        warehouse = Warehouse.objects.create(
            name="Default Warehouse", slug="default-warehouse"
        )
    print(f"Using warehouse: {warehouse.name}")

    # 1. Create categories
    categories = {}
    category_names = ["Skincare", "Makeup", "Fragrance", "Hair", "Bath and Body", "Beauty Tools", "Gifts"]
    for name in category_names:
        categories[name], _ = Category.objects.get_or_create(
            name=name, defaults={"slug": slugify(name)}
        )
    print("Categories ensured.")

    # 2. Create attributes
    size_attribute, _ = Attribute.objects.get_or_create(
        slug="size",
        defaults={
            "name": "Size",
            "type": "product-type",  # maps to AttributeType.PRODUCT_TYPE
            "input_type": "dropdown",
        }
    )
    for s_val in ["30 ml", "50 ml", "100 ml"]:
        size_attribute.values.get_or_create(
            slug=slugify(s_val),
            defaults={"name": s_val}
        )

    shade_attribute, _ = Attribute.objects.get_or_create(
        slug="shade",
        defaults={
            "name": "Shade",
            "type": "product-type",
            "input_type": "dropdown",
        }
    )
    for name, hex_code in SHADE_HEX_MAPPING.items():
        shade_attribute.values.get_or_create(
            slug=slugify(name),
            defaults={
                "name": name,
                "value": hex_code  # Save hex code in the value field for swatch resolution
            }
        )
    print("Attributes and values ensured.")

    # 3. Create product types
    product_types = {}
    for name in category_names:
        pt, _ = ProductType.objects.get_or_create(
            name=f"Aurelle {name}",
            defaults={
                "slug": slugify(f"aurelle-{name}"),
                "has_variants": True,
                "is_shipping_required": True,
            }
        )
        # Link variant attributes
        if name in ["Skincare", "Fragrance"]:
            pt.variant_attributes.add(size_attribute)
        elif name == "Makeup":
            pt.variant_attributes.add(shade_attribute)
        product_types[name] = pt
    print("Product types ensured.")

    now = timezone.now()

    # 4. Create products and variants
    for item in PRODUCTS_DATA:
        product, p_created = Product.objects.get_or_create(
            name=item["name"],
            defaults={
                "slug": slugify(item["name"]),
                "category": categories[item["category"]],
                "product_type": product_types[item["product_type"]],
            },
        )

        ProductChannelListing.objects.get_or_create(
            product=product,
            channel=channel,
            defaults={
                "is_published": True,
                "published_at": now,
                "visible_in_listings": True,
                "available_for_purchase_at": now,
                "currency": channel.currency_code,
            },
        )

        for var_idx, var_data in enumerate(item["variants"]):
            sku_name = slugify(f"{item['name']}-{var_data['name']}")
            variant, v_created = ProductVariant.objects.get_or_create(
                product=product,
                sku=f"AURELLE-{sku_name}".upper(),
                defaults={
                    "name": var_data["name"],
                    "track_inventory": True,
                },
            )

            # Map variant attribute values
            attr_val_map = {}
            for attr_slug, attr_val_name in var_data["attrs"].items():
                if attr_slug == "size":
                    val_obj = size_attribute.values.filter(name=attr_val_name).first()
                    if val_obj:
                        attr_val_map[size_attribute.id] = [val_obj]
                elif attr_slug == "shade":
                    val_obj = shade_attribute.values.filter(name=attr_val_name).first()
                    if val_obj:
                        attr_val_map[shade_attribute.id] = [val_obj]
            
            if attr_val_map:
                associate_attribute_values_to_instance(variant, attr_val_map)

            ProductVariantChannelListing.objects.get_or_create(
                variant=variant,
                channel=channel,
                defaults={
                    "price_amount": var_data["price"],
                    "discounted_price_amount": var_data["price"],
                    "currency": channel.currency_code,
                },
            )

            Stock.objects.get_or_create(
                warehouse=warehouse,
                product_variant=variant,
                defaults={"quantity": DEFAULT_STOCK_QUANTITY},
            )

        print(f"{'Created' if p_created else 'Ensured'} product: {product.name}")

    print("Seeding AURELLE complete.")

if __name__ == "__main__":
    seed()
