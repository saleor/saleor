from collections import defaultdict
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple

from django.utils.functional import SimpleLazyObject

from ....product.models import (
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductChannelListing,
    ProductImage,
    ProductVariant,
)
from ...core.dataloaders import DataLoader

ProductIdAndChannelSlug = Tuple[int, str]


class CategoryByIdLoader(DataLoader):
    context_key = "category_by_id"

    def batch_load(self, keys):
        categories = Category.objects.in_bulk(keys)
        return [categories.get(category_id) for category_id in keys]


class ProductByIdLoader(DataLoader):
    context_key = "product_by_id"

    def batch_load(self, keys):
        channel_slug = self.context.channel_slug
        products = Product.objects.visible_to_user(self.user, channel_slug).in_bulk(
            keys
        )
        return [products.get(product_id) for product_id in keys]


class ProductChannelListingByProductId(DataLoader[int, ProductChannelListing]):
    context_key = "productchannelisting_by_id"

    def batch_load(self, keys):
        product_channel_listings = ProductChannelListing.objects.in_bulk(keys)
        return [product_channel_listings.get(key) for key in keys]


class ProductChannelListingByProductIdLoader(DataLoader[int, ProductChannelListing]):
    context_key = "productchannelisting_by_product"

    def batch_load(self, keys):
        product_channel_listings = ProductChannelListing.objects.filter(
            product_id__in=keys
        )
        product_channel_listings_map = defaultdict(list)
        product_channel_listing_loader = ProductChannelListingByProductId(self.context)
        for product_channel_listing in product_channel_listings.iterator():
            product_channel_listings_map[product_channel_listing.product_id].append(
                product_channel_listing
            )
            product_channel_listing_loader.prime(
                product_channel_listing.id, product_channel_listing
            )
        return [product_channel_listings_map.get(product_id, []) for product_id in keys]


class ProductChannelListingByProductIdAndChanneSlugLoader(
    DataLoader[ProductIdAndChannelSlug, ProductChannelListing]
):
    context_key = "productchannelisting_by_product_and_channel"

    def batch_load(self, keys):
        # Split the list of keys by channel first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per channel.
        product_channel_listing_by_channel: DefaultDict[str, List[int]] = defaultdict(
            list
        )
        for product_id, channel_slug in keys:
            product_channel_listing_by_channel[channel_slug].append(product_id)

        # For each channel execute a single query for all products.
        product_channel_listing_by_product_and_channel: DefaultDict[
            ProductIdAndChannelSlug, Optional[ProductChannelListing]
        ] = defaultdict()
        for channel_slug, product_ids in product_channel_listing_by_channel.items():
            product_channel_listings = self.batch_load_channel(
                channel_slug, product_ids
            )
            for product_id, product_channel_listing in product_channel_listings:
                product_channel_listing_by_product_and_channel[
                    (product_id, channel_slug)
                ] = product_channel_listing

        return [product_channel_listing_by_product_and_channel[key] for key in keys]

    def batch_load_channel(
        self, channel_slug: str, products_ids: Iterable[int]
    ) -> Iterable[Tuple[int, Optional[ProductChannelListing]]]:
        if isinstance(channel_slug, SimpleLazyObject):
            channel_slug = str(channel_slug)
        product_channel_listings = ProductChannelListing.objects.filter(
            channel__slug=channel_slug, product_id__in=products_ids
        )

        product_channel_listings_map: Dict[int, ProductChannelListing] = {}
        for product_channel_listing in product_channel_listings.iterator():
            product_channel_listings_map[
                product_channel_listing.product.id
            ] = product_channel_listing

        return [
            (products_id, product_channel_listings_map.get(products_id))
            for products_id in products_ids
        ]


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
