from collections import defaultdict

from ...discount import DiscountInfo
from ...discount.models import Sale
from ...product.models import Category
from ..core.dataloaders import DataLoader


class DiscountsByDateTimeLoader(DataLoader):
    context_key = "discounts"

    def fetch_categories(self, sale_pks):
        categories = (
            Sale.categories.through.objects.filter(sale_id__in=sale_pks)
            .order_by("id")
            .values_list("sale_id", "category_id")
        )
        category_map = defaultdict(set)
        for sale_pk, category_pk in categories:
            category_map[sale_pk].add(category_pk)
        subcategory_map = defaultdict(set)
        for sale_pk, category_pks in category_map.items():
            subcategory_map[sale_pk] = set(
                Category.tree.filter(pk__in=category_pks)
                .get_descendants(include_self=True)
                .values_list("id", flat=True)
            )
        return subcategory_map

    def fetch_collections(self, sale_pks):
        collections = (
            Sale.collections.through.objects.filter(sale_id__in=sale_pks)
            .order_by("id")
            .values_list("sale_id", "collection_id")
        )
        collection_map = defaultdict(set)
        for sale_pk, collection_pk in collections:
            collection_map[sale_pk].add(collection_pk)
        return collection_map

    def fetch_products(self, sale_pks):
        products = (
            Sale.products.through.objects.filter(sale_id__in=sale_pks)
            .order_by("id")
            .values_list("sale_id", "product_id")
        )
        product_map = defaultdict(set)
        for sale_pk, product_pk in products:
            product_map[sale_pk].add(product_pk)
        return product_map

    def batch_load(self, keys):
        sales_map = {
            datetime: list(Sale.objects.active(datetime).order_by("id"))
            for datetime in keys
        }
        pks = {s.pk for d, ss in sales_map.items() for s in ss}
        collections = self.fetch_collections(pks)
        products = self.fetch_products(pks)
        categories = self.fetch_categories(pks)

        return [
            [
                DiscountInfo(
                    sale=sale,
                    category_ids=categories[sale.pk],
                    collection_ids=collections[sale.pk],
                    product_ids=products[sale.pk],
                )
                for sale in sales_map[datetime]
            ]
            for datetime in keys
        ]
