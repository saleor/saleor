from ... import DiscountInfo
from ...utils import fetch_sale_channel_listings


def generate_discount_info(
    sale,
    products_pks=set(),
    variant_pks=set(),
    collection_pks=set(),
    category_ids=set(),
    channel_listings=None,
):
    if not channel_listings:
        channel_listings = fetch_sale_channel_listings([sale.pk])[sale.pk]

    return DiscountInfo(
        sale=sale,
        category_ids=category_ids,
        channel_listings=channel_listings,
        collection_ids=collection_pks,
        product_ids=products_pks,
        variants_ids=variant_pks,
    )
