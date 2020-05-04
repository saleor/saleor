from collections import defaultdict

from ....product.models import (
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductImage,
    ProductVariant,
)
from ...core.dataloaders import DataLoader


class CategoryByIdLoader(DataLoader):
    context_key = "category_by_id"

    def batch_load(self, keys):
        categories = Category.objects.in_bulk(keys)
        return [categories.get(category_id) for category_id in keys]


class ProductByIdLoader(DataLoader):
    context_key = "product_by_id"

    def batch_load(self, keys):
        products = Product.objects.visible_to_user(self.user).in_bulk(keys)
        return [products.get(product_id) for product_id in keys]


class ImagesByProductIdLoader(DataLoader):
    context_key = "images_by_product"

    def batch_load(self, keys):
        images = ProductImage.objects.filter(product_id__in=keys)
        image_map = defaultdict(list)
        for image in images:
            image_map[image.product_id].append(image)
        return [image_map[product_id] for product_id in keys]


class ProductVariantByIdLoader(DataLoader):
    context_key = "productvariant_by_id"

    def batch_load(self, keys):
        variants = ProductVariant.objects.in_bulk(keys)
        return [variants.get(key) for key in keys]


class ProductVariantsByProductIdLoader(DataLoader):
    context_key = "productvariants_by_product"

    def batch_load(self, keys):
        variants = ProductVariant.objects.filter(product_id__in=keys)
        variant_map = defaultdict(list)
        variant_loader = ProductVariantByIdLoader(self.context)
        for variant in variants.iterator():
            variant_map[variant.product_id].append(variant)
            variant_loader.prime(variant.id, variant)
        return [variant_map.get(product_id, []) for product_id in keys]


class CollectionByIdLoader(DataLoader):
    context_key = "collection_by_id"

    def batch_load(self, keys):
        collections = Collection.objects.in_bulk(keys)
        return [collections.get(collection_id) for collection_id in keys]


class CollectionsByProductIdLoader(DataLoader):
    context_key = "collections_by_product"

    def batch_load(self, keys):
        product_collection_pairs = list(
            CollectionProduct.objects.filter(product_id__in=keys)
            .order_by("id")
            .values_list("product_id", "collection_id")
        )
        product_collection_map = defaultdict(list)
        for pid, cid in product_collection_pairs:
            product_collection_map[pid].append(cid)

        def map_collections(collections):
            collection_map = {c.id: c for c in collections}
            return [
                [collection_map[cid] for cid in product_collection_map[pid]]
                for pid in keys
            ]

        return (
            CollectionByIdLoader(self.context)
            .load_many(set(cid for pid, cid in product_collection_pairs))
            .then(map_collections)
        )
