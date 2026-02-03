
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from saleor.product.models import Category, ProductType
from saleor.channel.models import Channel
from saleor.warehouse.models import Warehouse

def setup():
    # 1. Categories
    fruits, created = Category.objects.get_or_create(
        name="Fruits",
        defaults={"slug": "fruits-produce-final"}
    )
    veggies, created = Category.objects.get_or_create(
        name="Vegetables",
        defaults={"slug": "vegetables-produce-final"}
    )
    print(f"Fruits Category ID: {fruits.id} (Slug: {fruits.slug})")
    print(f"Vegetables Category ID: {veggies.id} (Slug: {veggies.slug})")

    # 2. Product Type
    prod_type, created = ProductType.objects.get_or_create(
        name="Fresh Produce",
        defaults={"slug": "fresh-produce-final", "has_variants": True}
    )
    print(f"Product Type ID: {prod_type.id}")

    # 3. Channels
    channels = Channel.objects.all()
    for ch in channels:
        print(f"Channel: {ch.name} (Slug: {ch.slug}) - ID: {ch.id}")

    # 4. Warehouses
    warehouses = Warehouse.objects.all()
    for w in warehouses:
        print(f"Warehouse: {w.name} - ID: {w.id}")

if __name__ == "__main__":
    setup()
