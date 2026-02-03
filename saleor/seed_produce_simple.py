
import os
import django
from django.utils.text import slugify

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from saleor.product.models import Category, Product, ProductType, ProductVariant, ProductChannelListing, ProductVariantChannelListing
from saleor.channel.models import Channel
from saleor.warehouse.models import Warehouse, Stock

def seed():
    # 1. Get Channel
    channel = Channel.objects.filter(slug="default-channel").first()
    if not channel:
        print("Channel 'default-channel' not found. Creating it...")
        channel = Channel.objects.create(name="Default Channel", slug="default-channel", currency="USD", is_active=True)
    
    # 2. Get Warehouse
    warehouse = Warehouse.objects.first()
    if not warehouse:
        print("No warehouse found. Creating 'Default Warehouse'...")
        warehouse = Warehouse.objects.create(name="Default Warehouse", slug="default-warehouse")

    # 3. Get or create Category
    fruits_cat, _ = Category.objects.get_or_create(name="Fruits", defaults={"slug": "fruits-produce-3"})
    veggies_cat, _ = Category.objects.get_or_create(name="Vegetables", defaults={"slug": "vegetables-produce-3"})

    # 4. Get or create Product Type
    product_type, _ = ProductType.objects.get_or_create(
        name="Fresh Produce", 
        defaults={
            "slug": "fresh-produce-final", 
            "has_variants": True
        }
    )

    # 5. Seed one product test
    name = "Organic Gala Apple"
    p_slug = slugify(name)
    
    product, created = Product.objects.get_or_create(
        slug=p_slug,
        defaults={
            "name": name,
            "category": fruits_cat,
            "product_type": product_type,
            "description": "Crisp and sweet organic gala apples.",
        }
    )
    
    if created:
        print(f"Created product: {product.name}")
        ProductChannelListing.objects.create(
            product=product,
            channel=channel,
            is_published=True,
            visible_in_listings=True
        )
        variant = ProductVariant.objects.create(product=product, sku=f"SKU-{p_slug}", name="Standard")
        ProductVariantChannelListing.objects.create(
            variant=variant,
            channel=channel,
            price_amount=1.50,
            currency="USD"
        )
        Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=100)
    else:
        print(f"Product already exists: {product.name}")

    print("Simplest seed ran successfully.")

if __name__ == "__main__":
    seed()
