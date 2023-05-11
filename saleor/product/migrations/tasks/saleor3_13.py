from django.db.models import Exists, OuterRef

from ...models import Product, ProductVariantChannelListing, ProductVariant
from ...utils.variant_prices import update_products_discounted_price
from ....celeryconf import app


# Results in memory usage of ~40MB for 500 products
BATCH_SIZE = 500


@app.task
def update_discounted_prices_task():
    listings = ProductVariantChannelListing.objects.filter(
        discounted_price_amount__isnull=True
    )
    variants = ProductVariant.objects.filter(
        Exists(listings.filter(variant_id=OuterRef("id")))
    )
    products = list(
        Product.objects.filter(
            Exists(variants.filter(product_id=OuterRef("id"))),
        )
        .prefetch_related("channel_listings", "collections")
        .order_by("-pk")[:BATCH_SIZE]
    )

    if products:
        update_products_discounted_price(products)
        update_discounted_prices_task.delay()
