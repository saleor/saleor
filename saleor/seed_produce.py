
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
    # 1. Get or create Channel
    channel = Channel.objects.filter(slug="default-channel").first()
    if not channel:
        channel = Channel.objects.create(name="Default Channel", slug="default-channel", currency="USD", is_active=True)
    print(f"Using Channel: {channel.slug}")

    # 2. Get or create Warehouse
    warehouse = Warehouse.objects.first()
    if not warehouse:
        warehouse = Warehouse.objects.create(name="Default Warehouse", slug="default-warehouse")
    print(f"Using Warehouse: {warehouse.name}")

    # 3. Get or create Category
    fruits_cat, _ = Category.objects.get_or_create(name="Fruits", defaults={"slug": "fruits-produce"})
    veggies_cat, _ = Category.objects.get_or_create(name="Vegetables", defaults={"slug": "vegetables-produce"})
    print("Categories ensured.")

    # 4. Get or create Product Type
    product_type, _ = ProductType.objects.get_or_create(
        name="Fresh Produce", 
        defaults={
            "slug": "fresh-produce", 
            "has_variants": True, 
            "is_shipping_required": True
        }
    )
    print("Product Type ensured.")

    # Define products to seed
    items = [
        {"name": "Organic Red Apple", "category": fruits_cat, "price": 1.50},
        {"name": "Fresh Bananas", "category": fruits_cat, "price": 0.50},
        {"name": "Baby Carrots", "category": veggies_cat, "price": 2.00},
        {"name": "Green Broccoli", "category": veggies_cat, "price": 1.75},
    ]

    for item in items:
        # Create Product
        product, created = Product.objects.get_or_create(
            name=item["name"],
            defaults={
                "slug": slugify(item["name"]),
                "category": item["category"],
                "product_type": product_type,
                "description": f"Fresh {item['name']} from our local farms.",
            }
        )
        
        if created:
            print(f"Created product: {product.name}")
            
            # Create Channel Listing for Product
            ProductChannelListing.objects.create(
                product=product,
                channel=channel,
                is_published=True,
                visible_in_listings=True
            )

            # Create Variant
            variant = ProductVariant.objects.create(
                product=product,
                sku=f"SKU-{slugify(item['name'])}",
                name="Standard"
            )

            # Create Channel Listing for Variant
            ProductVariantChannelListing.objects.create(
                variant=variant,
                channel=channel,
                price_amount=item["price"],
                currency="USD"
            )

            # Create Stock
            Stock.objects.create(
                warehouse=warehouse,
                product_variant=variant,
                quantity=100
            )
        else:
            print(f"Product already exists: {product.name}")

    print("Seeding complete!")

if __name__ == "__main__":
    seed()
