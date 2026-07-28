# ruff: noqa: T201
"""Idempotent product media seeder for AURELLE Cosmetics.

Links the copied product image files in the media folder to their database products.

Usage:
    python scripts/seed_images.py
"""

import os
import sys
from pathlib import Path

import django

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from saleor.product.models import Product, ProductMedia

MEDIA_MAPPING = {
    "Barrier Renewal Serum": {
        "file": "products/barrier_renewal_serum.png",
        "alt": "Aurelle Barrier Renewal Serum frosted glass bottle with black dropper cap on clean white marble"
    },
    "Cloud Cream Moisturizer": {
        "file": "products/cloud_cream.png",
        "alt": "Aurelle Cloud Cream Moisturizer open jar showcasing luxurious fluffy cream texture"
    },
    "Skin Veil Foundation": {
        "file": "products/skin_veil_foundation.png",
        "alt": "Aurelle Skin Veil Foundation glass pump bottle next to color swatches on ivory stone surface"
    },
    "No. 04 Amber Iris Eau de Parfum": {
        "file": "products/amber_iris_perfume.png",
        "alt": "Aurelle No. 04 Amber Iris Eau de Parfum minimalist clear glass spray bottle with gold liquid"
    }
}

def seed():
    for product_name, media_info in MEDIA_MAPPING.items():
        product = Product.objects.filter(name=product_name).first()
        if not product:
            print(f"Product not found: {product_name}")
            continue

        # Clean existing media to avoid duplicates
        product.media.all().delete()
        print(f"Cleared existing media for {product_name}")

        # Create new product media
        media = ProductMedia.objects.create(
            product=product,
            image=media_info["file"],
            alt=media_info["alt"],
            type="IMAGE"
        )
        print(f"Assigned media {media_info['file']} to product: {product.name}")

    print("Media Seeding complete.")

if __name__ == "__main__":
    seed()
