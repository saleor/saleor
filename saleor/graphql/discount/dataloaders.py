from ...discount import DiscountInfo
from ...discount.models import Sale
from ...discount.utils import (
    fetch_categories,
    fetch_collections,
    fetch_products,
    fetch_sale_channel_listings,
)
from ..core.dataloaders import DataLoader


class DiscountsByDateTimeLoader(DataLoader):
    context_key = "discounts"

    def batch_load(self, keys):
        sales_map = {
            datetime: list(Sale.objects.active(datetime).order_by("id"))
            for datetime in keys
        }
        pks = {s.pk for d, ss in sales_map.items() for s in ss}
        collections = fetch_collections(pks)
        channel_listings = fetch_sale_channel_listings(pks)
        products = fetch_products(pks)
        categories = fetch_categories(pks)

        return [
            [
                DiscountInfo(
                    sale=sale,
                    channel_listings=channel_listings[sale.pk],
                    category_ids=categories[sale.pk],
                    collection_ids=collections[sale.pk],
                    product_ids=products[sale.pk],
                )
                for sale in sales_map[datetime]
            ]
            for datetime in keys
        ]
