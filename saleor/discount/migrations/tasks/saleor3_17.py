from django.db.models import Exists, F, OuterRef

from ....celeryconf import app
from ....product.models import (
    Product,
    ProductVariant,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)
from ....product.utils.variant_prices import update_discounted_prices_for_promotion

# For 100 rules, with 1000 variants for each rule it takes around 15s
BATCH_SIZE = 100


@app.task
def update_discounted_prices_task():
    variant_listing_qs = (
        ProductVariantChannelListing.objects.annotate(
            discount=F("price_amount") - F("discounted_price_amount")
        )
        .filter(discount__gt=0)
        .filter(
            ~Exists(
                VariantChannelListingPromotionRule.objects.filter(
                    variant_channel_listing_id=OuterRef("id")
                )
            )
        )
    )
    variant_qs = ProductVariant.objects.filter(
        Exists(variant_listing_qs.filter(variant_id=OuterRef("id")))
    )
    products_ids = Product.objects.filter(
        Exists(variant_qs.filter(product_id=OuterRef("id")))
    ).values_list("id", flat=True)[:BATCH_SIZE]
    if products_ids:
        products = Product.objects.filter(id__in=products_ids)
        update_discounted_prices_for_promotion(products)
        update_discounted_prices_task.delay()
