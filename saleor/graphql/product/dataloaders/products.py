from collections import defaultdict
from collections.abc import Iterable
from typing import Optional

from django.db.models import Exists, F, OuterRef, Q

from ....core.db.connection import allow_writer_in_context
from ....product import ProductMediaTypes
from ....product.models import (
    Category,
    Collection,
    CollectionChannelListing,
    CollectionProduct,
    Product,
    ProductChannelListing,
    ProductMedia,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
    VariantMedia,
)
from ...channel.dataloaders import ChannelBySlugLoader
from ...core.dataloaders import BaseThumbnailBySizeAndFormatLoader, DataLoader

ProductIdAndChannelSlug = tuple[int, str]
VariantIdAndChannelSlug = tuple[int, str]
VariantIdAndChannelId = tuple[int, Optional[int]]


class CategoryByIdLoader(DataLoader[int, Category]):
    context_key = "category_by_id"

    def batch_load(self, keys):
        categories = Category.objects.using(self.database_connection_name).in_bulk(keys)
        return [categories.get(category_id) for category_id in keys]


class CategoryBySlugLoader(DataLoader[str, Category]):
    context_key = "category_by_slug"

    def batch_load(self, keys):
        categories = Category.objects.using(self.database_connection_name).in_bulk(
            keys, field_name="slug"
        )
        return [categories.get(category_id) for category_id in keys]


class ProductByIdLoader(DataLoader[int, Product]):
    context_key = "product_by_id"

    def batch_load(self, keys):
        products = Product.objects.using(self.database_connection_name).in_bulk(keys)
        return [products.get(product_id) for product_id in keys]


class ProductByVariantIdLoader(DataLoader[int, Product]):
    context_key = "product_by_variant_id"

    def batch_load(self, keys):
        def with_variants(variants):
            product_ids = [variant.product_id for variant in variants]
            return ProductByIdLoader(self.context).load_many(product_ids)

        return (
            ProductVariantByIdLoader(self.context).load_many(keys).then(with_variants)
        )


class ProductChannelListingByIdLoader(DataLoader[int, ProductChannelListing]):
    context_key = "productchannelisting_by_id"

    def batch_load(self, keys):
        product_channel_listings = ProductChannelListing.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [product_channel_listings.get(key) for key in keys]


class ProductChannelListingByProductIdLoader(DataLoader[int, ProductChannelListing]):
    context_key = "productchannelisting_by_product"

    def batch_load(self, keys):
        product_channel_listings = ProductChannelListing.objects.using(
            self.database_connection_name
        ).filter(product_id__in=keys)
        product_id_variant_channel_listings_map = defaultdict(list)
        for product_channel_listing in product_channel_listings.iterator():
            product_id_variant_channel_listings_map[
                product_channel_listing.product_id
            ].append(product_channel_listing)
        return [
            product_id_variant_channel_listings_map.get(product_id, [])
            for product_id in keys
        ]


class ProductChannelListingByProductIdAndChannelSlugLoader(
    DataLoader[ProductIdAndChannelSlug, ProductChannelListing]
):
    context_key = "productchannelisting_by_product_and_channel"

    def batch_load(self, keys: Iterable[ProductIdAndChannelSlug]):
        # Split the list of keys by channel first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per channel.
        product_channel_listing_by_channel: defaultdict[str, list[int]] = defaultdict(
            list
        )
        for product_id, channel_slug in keys:
            product_channel_listing_by_channel[channel_slug].append(product_id)

        # For each channel execute a single query for all products.
        product_channel_listing_by_product_and_channel: defaultdict[
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
    ) -> Iterable[tuple[int, Optional[ProductChannelListing]]]:
        product_channel_listings = ProductChannelListing.objects.using(
            self.database_connection_name
        ).filter(channel__slug=channel_slug, product_id__in=products_ids)

        product_channel_listings_map: dict[int, ProductChannelListing] = {}
        for product_channel_listing in product_channel_listings.iterator():
            product_channel_listings_map[product_channel_listing.product_id] = (
                product_channel_listing
            )

        return [
            (products_id, product_channel_listings_map.get(products_id))
            for products_id in products_ids
        ]


class ProductTypeByIdLoader(DataLoader[int, ProductType]):
    context_key = "product_type_by_id"

    def batch_load(self, keys):
        product_types = ProductType.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [product_types.get(product_type_id) for product_type_id in keys]


class MediaByProductIdLoader(DataLoader[int, list[ProductMedia]]):
    context_key = "media_by_product"

    def batch_load(self, keys):
        media = ProductMedia.objects.using(self.database_connection_name).filter(
            product_id__in=keys,
        )
        media_map = defaultdict(list)
        for media_obj in media.iterator():
            media_map[media_obj.product_id].append(media_obj)
        return [media_map[product_id] for product_id in keys]


class ImagesByProductIdLoader(DataLoader[int, list[ProductMedia]]):
    context_key = "images_by_product"

    def batch_load(self, keys):
        images = ProductMedia.objects.using(self.database_connection_name).filter(
            product_id__in=keys,
            type=ProductMediaTypes.IMAGE,
        )
        images_map = defaultdict(list)
        for image in images.iterator():
            images_map[image.product_id].append(image)
        return [images_map[product_id] for product_id in keys]


class ProductVariantByIdLoader(DataLoader[int, ProductVariant]):
    context_key = "productvariant_by_id"

    def batch_load(self, keys):
        variants = ProductVariant.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [variants.get(key) for key in keys]


class ProductVariantsByProductIdLoader(DataLoader[int, list[ProductVariant]]):
    context_key = "productvariants_by_product"

    def batch_load(self, keys):
        variants = ProductVariant.objects.using(self.database_connection_name).filter(
            product_id__in=keys
        )
        variant_map = defaultdict(list)
        variant_loader = ProductVariantByIdLoader(self.context)
        for variant in variants.iterator():
            variant_map[variant.product_id].append(variant)
            variant_loader.prime(variant.id, variant)
        return [variant_map.get(product_id, []) for product_id in keys]


class ProductVariantsByProductIdAndChannel(
    DataLoader[tuple[int, str], list[ProductVariant]]
):
    context_key = "productvariant_by_product_and_channel"

    def batch_load(self, keys: Iterable[tuple[int, str]]):
        product_ids_by_channel = defaultdict(list)
        for product_id, channel_slug in keys:
            product_ids_by_channel[channel_slug].append(product_id)

        def with_channels(channels):
            channel_map = {c.slug: c for c in channels}
            variant_map: defaultdict[tuple[int, str], list[ProductVariant]] = (
                defaultdict(list)
            )

            for channel_slug in product_ids_by_channel.keys():
                channel = channel_map[channel_slug]
                product_ids = product_ids_by_channel[channel_slug]
                variants_filter = self.get_variants_filter(channel.id)

                variants = (
                    ProductVariant.objects.using(self.database_connection_name)
                    .filter(variants_filter)
                    .filter(product_id__in=product_ids)
                    .order_by("sort_order", "sku")
                )

                for variant in variants.iterator():
                    key = (variant.product_id, channel.slug)
                    variant_map[key].append(variant)

            return [variant_map.get(key, []) for key in keys]

        return (
            ChannelBySlugLoader(self.context)
            .load_many(product_ids_by_channel.keys())
            .then(with_channels)
        )

    def get_variants_filter(self, channel_id: int):
        variant_channel_listings = ProductVariantChannelListing.objects.filter(
            channel_id=channel_id
        )
        return Q(Exists(variant_channel_listings.filter(variant_id=OuterRef("id"))))


class AvailableProductVariantsByProductIdAndChannel(
    ProductVariantsByProductIdAndChannel
):
    context_key = "available_productvariant_by_product_and_channel"

    def get_variants_filter(self, channel_id: int):
        variant_channel_listings = ProductVariantChannelListing.objects.filter(
            channel_id=channel_id, price_amount__isnull=False
        )
        return Q(Exists(variant_channel_listings.filter(variant_id=OuterRef("id"))))


class ProductVariantChannelListingByIdLoader(DataLoader):
    context_key = "productvariantchannelisting_by_id"

    def batch_load(self, keys):
        variants = ProductVariantChannelListing.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [variants.get(key) for key in keys]


class VariantChannelListingByVariantIdLoader(DataLoader):
    context_key = "productvariantchannelisting_by_productvariant"

    def batch_load(self, keys):
        variant_channel_listings = (
            ProductVariantChannelListing.objects.using(self.database_connection_name)
            .filter(variant_id__in=keys)
            .annotate_preorder_quantity_allocated()
            .order_by("pk")
        )

        variant_id_variant_channel_listings_map = defaultdict(list)
        for variant_channel_listing in variant_channel_listings.iterator():
            variant_id_variant_channel_listings_map[
                variant_channel_listing.variant_id
            ].append(variant_channel_listing)
        return [
            variant_id_variant_channel_listings_map.get(variant_id, [])
            for variant_id in keys
        ]


class VariantChannelListingByVariantIdAndChannelSlugLoader(
    DataLoader[VariantIdAndChannelSlug, ProductVariantChannelListing]
):
    context_key = "variantchannelisting_by_variant_and_channelslug"

    def batch_load(self, keys):
        channel_slugs = [channel_slug for _, channel_slug in keys if channel_slug]

        def with_channels(channels):
            channel_map = {c.slug: c.id for c in channels}
            variant_id_channel_id_keys = [
                (variant_id, channel_map.get(channel_slug, None))
                for (variant_id, channel_slug) in keys
            ]
            return VariantChannelListingByVariantIdAndChannelIdLoader(
                self.context
            ).load_many(variant_id_channel_id_keys)

        return (
            ChannelBySlugLoader(self.context)
            .load_many(channel_slugs)
            .then(with_channels)
        )


class VariantChannelListingByVariantIdAndChannelIdLoader(
    DataLoader[VariantIdAndChannelId, ProductVariantChannelListing]
):
    context_key = "variantchannelisting_by_variant_and_channelid"

    def batch_load(self, keys):
        # Split the list of keys by channel first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per channel.
        variant_channel_listing_by_channel: defaultdict[Optional[int], list[int]] = (
            defaultdict(list)
        )
        for variant_id, channel_id in keys:
            variant_channel_listing_by_channel[channel_id].append(variant_id)

        # For each channel execute a single query for all product variants.
        variant_channel_listing_by_variant_and_channel: defaultdict[
            VariantIdAndChannelId, Optional[ProductVariantChannelListing]
        ] = defaultdict()
        for channel_id, variant_ids in variant_channel_listing_by_channel.items():
            variant_channel_listings = self.batch_load_channel(channel_id, variant_ids)
            for variant_id, variant_channel_listing in variant_channel_listings:
                variant_channel_listing_by_variant_and_channel[
                    (variant_id, channel_id)
                ] = variant_channel_listing

        return [variant_channel_listing_by_variant_and_channel[key] for key in keys]

    def batch_load_channel(
        self, channel_id: Optional[int], variant_ids: Iterable[int]
    ) -> Iterable[tuple[int, Optional[ProductVariantChannelListing]]]:
        filter = {
            "channel_id": channel_id,
            "variant_id__in": variant_ids,
            "price_amount__isnull": False,
        }
        variant_channel_listings = (
            ProductVariantChannelListing.objects.all()
            .using(self.database_connection_name)
            .filter(**filter)
            .annotate_preorder_quantity_allocated()
            .order_by("pk")
        )

        variant_channel_listings_map: dict[int, ProductVariantChannelListing] = {}
        for variant_channel_listing in variant_channel_listings.iterator():
            variant_channel_listings_map[variant_channel_listing.variant_id] = (
                variant_channel_listing
            )

        return [
            (variant_id, variant_channel_listings_map.get(variant_id))
            for variant_id in variant_ids
        ]


class VariantsChannelListingByProductIdAndChannelSlugLoader(
    DataLoader[ProductIdAndChannelSlug, Iterable[ProductVariantChannelListing]]
):
    context_key = "variantschannelisting_by_product_and_channel"

    def batch_load(self, keys):
        # Split the list of keys by channel first. A typical query will only touch
        # a handful of unique countries but may access thousands of product variants
        # so it's cheaper to execute one query per channel.
        variant_channel_listing_by_channel: defaultdict[str, list[int]] = defaultdict(
            list
        )
        for product_id, channel_slug in keys:
            variant_channel_listing_by_channel[channel_slug].append(product_id)

        # For each channel execute a single query for all product variants.
        variant_channel_listing_by_product_and_channel: defaultdict[
            ProductIdAndChannelSlug, Optional[Iterable[ProductVariantChannelListing]]
        ] = defaultdict()
        for channel_slug, product_ids in variant_channel_listing_by_channel.items():
            variant_channel_listings = self.batch_load_channel(
                channel_slug, product_ids
            )
            for product_id, variants_channel_listing in variant_channel_listings:
                variant_channel_listing_by_product_and_channel[
                    (product_id, channel_slug)
                ] = variants_channel_listing

        return [
            variant_channel_listing_by_product_and_channel.get(key, []) for key in keys
        ]

    def batch_load_channel(
        self, channel_slug: str, products_ids: Iterable[int]
    ) -> Iterable[tuple[int, Optional[list[ProductVariantChannelListing]]]]:
        variants_channel_listings = (
            ProductVariantChannelListing.objects.all()
            .using(self.database_connection_name)
            .filter(
                channel__slug=channel_slug,
                variant__product_id__in=products_ids,
                price_amount__isnull=False,
            )
            .annotate(product_id=F("variant__product_id"))
            .order_by("pk")
        )

        variants_channel_listings_map: dict[int, list[ProductVariantChannelListing]] = (
            defaultdict(list)
        )
        for variant_channel_listing in variants_channel_listings.iterator():
            variants_channel_listings_map[
                getattr(variant_channel_listing, "product_id")  # annotation
            ].append(variant_channel_listing)

        return [
            (products_id, variants_channel_listings_map.get(products_id, []))
            for products_id in products_ids
        ]


class ProductMediaByIdLoader(DataLoader):
    context_key = "product_media_by_id"

    def batch_load(self, keys):
        product_media = ProductMedia.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [product_media.get(product_media_id) for product_media_id in keys]


class ProductImageByIdLoader(DataLoader):
    context_key = "product_image_by_id"

    def batch_load(self, keys):
        images = (
            ProductMedia.objects.using(self.database_connection_name)
            .filter(type=ProductMediaTypes.IMAGE)
            .in_bulk(keys)
        )
        return [images.get(product_image_id) for product_image_id in keys]


class MediaByProductVariantIdLoader(DataLoader):
    context_key = "media_by_product_variant"

    def batch_load(self, keys):
        variant_media = (
            VariantMedia.objects.using(self.database_connection_name)
            .filter(variant_id__in=keys)
            .values_list("variant_id", "media_id")
        )

        variant_media_pairs = defaultdict(list)
        for variant_id, media_id in variant_media.iterator():
            variant_media_pairs[variant_id].append(media_id)

        def map_variant_media(variant_media):
            media_map = {media.id: media for media in variant_media}
            return [
                [media_map[media_id] for media_id in variant_media_pairs[variant_id]]
                for variant_id in keys
            ]

        return (
            ProductMediaByIdLoader(self.context)
            .load_many(set(media_id for variant_id, media_id in variant_media))
            .then(map_variant_media)
        )


class ImagesByProductVariantIdLoader(DataLoader):
    context_key = "images_by_product_variant"

    def batch_load(self, keys):
        variant_media = (
            VariantMedia.objects.using(self.database_connection_name)
            .filter(
                variant_id__in=keys,
                media__type=ProductMediaTypes.IMAGE,
            )
            .values_list("variant_id", "media_id")
        )

        variant_media_pairs = defaultdict(list)
        for variant_id, media_id in variant_media.iterator():
            variant_media_pairs[variant_id].append(media_id)

        def map_variant_media(variant_media):
            media_map = {media.id: media for media in variant_media}
            return [
                [media_map[media_id] for media_id in variant_media_pairs[variant_id]]
                for variant_id in keys
            ]

        return (
            ProductMediaByIdLoader(self.context)
            .load_many(set(media_id for variant_id, media_id in variant_media))
            .then(map_variant_media)
        )


class CollectionByIdLoader(DataLoader):
    context_key = "collection_by_id"

    def batch_load(self, keys):
        collections = (
            Collection.objects.using(self.database_connection_name)
            .using(self.database_connection_name)
            .in_bulk(keys)
        )
        return [collections.get(collection_id) for collection_id in keys]


class CollectionsByProductIdLoader(DataLoader):
    context_key = "collections_by_product"

    def batch_load(self, keys):
        product_collection_pairs = list(
            CollectionProduct.objects.using(self.database_connection_name)
            .using(self.database_connection_name)
            .filter(product_id__in=keys)
            .order_by("id")
            .values_list("product_id", "collection_id")
            .iterator()
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


class CollectionsByVariantIdLoader(DataLoader):
    context_key = "collections_by_variant"

    def batch_load(self, keys):
        def with_variants(variants):
            product_ids = [variant.product_id for variant in variants]
            return CollectionsByProductIdLoader(self.context).load_many(product_ids)

        return (
            ProductVariantByIdLoader(self.context).load_many(keys).then(with_variants)
        )


class ProductTypeByProductIdLoader(DataLoader):
    context_key = "producttype_by_product_id"

    def batch_load(self, keys):
        @allow_writer_in_context(self.context)
        def with_products(products):
            product_ids = {p.id for p in products}
            product_types_map = (
                ProductType.objects.using(self.database_connection_name)
                .filter(products__in=product_ids)
                .in_bulk()
            )
            return [product_types_map[product.product_type_id] for product in products]

        return ProductByIdLoader(self.context).load_many(keys).then(with_products)


class ProductTypeByVariantIdLoader(DataLoader):
    context_key = "producttype_by_variant_id"

    def batch_load(self, keys):
        def with_variants(variants):
            product_ids = [v.product_id for v in variants]
            return ProductTypeByProductIdLoader(self.context).load_many(product_ids)

        return (
            ProductVariantByIdLoader(self.context).load_many(keys).then(with_variants)
        )


class CollectionChannelListingByIdLoader(DataLoader):
    context_key = "collectionchannelisting_by_id"

    def batch_load(self, keys):
        collections = CollectionChannelListing.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [collections.get(key) for key in keys]


class CollectionChannelListingByCollectionIdLoader(DataLoader):
    context_key = "collectionchannelisting_by_collection"

    def batch_load(self, keys):
        collections_channel_listings = CollectionChannelListing.objects.using(
            self.database_connection_name
        ).filter(collection_id__in=keys)
        collection_id_collection_channel_listings_map = defaultdict(list)
        for collection_channel_listing in collections_channel_listings.iterator():
            collection_id_collection_channel_listings_map[
                collection_channel_listing.collection_id
            ].append(collection_channel_listing)
        return [
            collection_id_collection_channel_listings_map.get(collection_id, [])
            for collection_id in keys
        ]


class CollectionChannelListingByCollectionIdAndChannelSlugLoader(DataLoader):
    context_key = "collectionchannelisting_by_collection_and_channel"

    def batch_load(self, keys):
        collection_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        collections_channel_listings = (
            CollectionChannelListing.objects.using(self.database_connection_name)
            .filter(collection_id__in=collection_ids, channel__slug__in=channel_slugs)
            .annotate(channel_slug=F("channel__slug"))
            .order_by("pk")
        )
        collections_channel_listings_by_collection_and_channel_map = {}
        for collections_channel_listing in collections_channel_listings.iterator():
            key = (
                collections_channel_listing.collection_id,
                collections_channel_listing.channel_slug,
            )
            collections_channel_listings_by_collection_and_channel_map[key] = (
                collections_channel_listing
            )
        return [
            collections_channel_listings_by_collection_and_channel_map.get(key, None)
            for key in keys
        ]


class CategoryChildrenByCategoryIdLoader(DataLoader):
    context_key = "categorychildren_by_category"

    def batch_load(self, keys):
        categories = Category.objects.using(self.database_connection_name).filter(
            parent_id__in=keys
        )
        parent_to_children_mapping = defaultdict(list)
        for category in categories.iterator():
            parent_to_children_mapping[category.parent_id].append(category)

        return [parent_to_children_mapping.get(key, []) for key in keys]


class ThumbnailByCategoryIdSizeAndFormatLoader(BaseThumbnailBySizeAndFormatLoader):
    context_key = "thumbnail_by_category_size_and_format"
    model_name = "category"


class ThumbnailByCollectionIdSizeAndFormatLoader(BaseThumbnailBySizeAndFormatLoader):
    context_key = "thumbnail_by_collection_size_and_format"
    model_name = "collection"


class ThumbnailByProductMediaIdSizeAndFormatLoader(BaseThumbnailBySizeAndFormatLoader):
    context_key = "thumbnail_by_productmedia_size_and_format"
    model_name = "product_media"


class VariantChannelListingPromotionRuleByListingIdLoader(DataLoader):
    context_key = "variant_channel_listing_promotion_rule_by_listing_id"

    def batch_load(self, keys):
        listing_promotion_rules = VariantChannelListingPromotionRule.objects.using(
            self.database_connection_name
        ).filter(variant_channel_listing_id__in=keys)

        channel_listing_to_channel_rules_map = defaultdict(list)
        for listing_rule in listing_promotion_rules:
            channel_listing_to_channel_rules_map[
                listing_rule.variant_channel_listing_id
            ].append(listing_rule)

        return [
            channel_listing_to_channel_rules_map.get(listing_id, [])
            for listing_id in keys
        ]
