from ...models import Product
from ...utils.variant_prices import update_products_discounted_price
from ....celeryconf import app


# Results in memory usage of ~40MB for 500 products
BATCH_SIZE = 500


@app.task
def update_discounted_prices_task(start_pk=0):
    products = list(
        Product.objects.filter(pk__gt=start_pk)
        .prefetch_related("channel_listings", "collections")
        .order_by("pk")[:BATCH_SIZE]
    )

    if products:
        update_products_discounted_price(products)
        update_discounted_prices_task.delay(products[-1].pk)
