from collections import defaultdict
from typing import Optional

from django.db.models import Exists, F, OuterRef, Sum
from django.db.models.functions import Coalesce
from promise import Promise

from ...channel.models import Channel
from ...discount.interface import VoucherInfo
from ...discount.models import (
    CheckoutDiscount,
    CheckoutLineDiscount,
    OrderDiscount,
    Promotion,
    PromotionEvent,
    PromotionRule,
    Voucher,
    VoucherChannelListing,
    VoucherCode,
)
from ...product.models import ProductVariant
from ..channel.dataloaders import ChannelBySlugLoader
from ..core.dataloaders import DataLoader


class VoucherByIdLoader(DataLoader):
    context_key = "voucher_by_id"

    def batch_load(self, keys):
        vouchers = Voucher.objects.using(self.database_connection_name).in_bulk(keys)
        return [vouchers.get(voucher_id) for voucher_id in keys]


class VoucherCodeByCodeLoader(DataLoader):
    context_key = "voucher_code_by_code"

    def batch_load(self, keys):
        voucher_codes = (
            VoucherCode.objects.using(self.database_connection_name)
            .select_related("voucher")
            .filter(code__in=keys)
        )
        voucher_map = {
            voucher_code.code: voucher_code for voucher_code in voucher_codes
        }
        return [voucher_map.get(code) for code in keys]


class CodeByVoucherIDLoader(DataLoader):
    """Fetch voucher code.

    This dataloader will be deprecated together with `code` field.
    """

    context_key = "voucher_code"

    def batch_load(self, keys):
        voucher_codes = VoucherCode.objects.using(self.database_connection_name).filter(
            voucher_id__in=keys
        )
        voucher_codes_map = {}
        for voucher_code in voucher_codes:
            voucher_codes_map[voucher_code.voucher_id] = voucher_code.code
        return [voucher_codes_map.get(voucher_id) for voucher_id in keys]


class UsedByVoucherIDLoader(DataLoader):
    """Fetch voucher used.

    This dataloader will be deprecated together with `used` field.
    """

    context_key = "voucher_used"

    def batch_load(self, keys):
        vouchers = (
            Voucher.objects.using(self.database_connection_name)
            .filter(id__in=keys)
            .annotate(max_used=Coalesce(Sum("codes__used"), 0))
        )
        vouchers_map = {}
        for voucher in vouchers:
            vouchers_map[voucher.id] = voucher.max_used  # type: ignore
        return [vouchers_map.get(voucher_id) for voucher_id in keys]


class VoucherByCodeLoader(DataLoader):
    context_key = "voucher_by_code"

    def batch_load(self, codes):
        def with_voucher_codes(voucher_codes):
            voucher_ids = {code.voucher_id for code in voucher_codes}
            vouchers = (
                Voucher.objects.using(self.database_connection_name)
                .filter(id__in=voucher_ids)
                .in_bulk()
            )
            code_voucher_map = {}
            for voucher_code in voucher_codes:
                code_voucher_map[voucher_code.code] = vouchers.get(
                    voucher_code.voucher_id
                )
            return [code_voucher_map.get(code) for code in codes]

        return (
            VoucherCodeByCodeLoader(self.context)
            .load_many(codes)
            .then(with_voucher_codes)
        )


class VoucherChannelListingByVoucherIdAndChanneSlugLoader(DataLoader):
    context_key = "voucherchannelisting_by_voucher_and_channel"

    def batch_load(self, keys):
        voucher_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        voucher_channel_listings = (
            VoucherChannelListing.objects.using(self.database_connection_name)
            .filter(voucher_id__in=voucher_ids, channel__slug__in=channel_slugs)
            .annotate(channel_slug=F("channel__slug"))
            .order_by("pk")
        )
        voucher_channel_listings_by_voucher_and_channel_map = {}
        for voucher_channel_listing in voucher_channel_listings:
            key = (
                voucher_channel_listing.voucher_id,
                voucher_channel_listing.channel_slug,
            )
            voucher_channel_listings_by_voucher_and_channel_map[key] = (
                voucher_channel_listing
            )
        return [
            voucher_channel_listings_by_voucher_and_channel_map.get(key) for key in keys
        ]


class VoucherChannelListingByVoucherIdLoader(DataLoader):
    context_key = "voucherchannellisting_by_voucher"

    def batch_load(self, keys):
        voucher_channel_listings = VoucherChannelListing.objects.using(
            self.database_connection_name
        ).filter(voucher_id__in=keys)
        voucher_channel_listings_by_voucher_map = defaultdict(list)
        for voucher_channel_listing in voucher_channel_listings:
            voucher_channel_listings_by_voucher_map[
                voucher_channel_listing.voucher_id
            ].append(voucher_channel_listing)
        return [
            voucher_channel_listings_by_voucher_map[voucher_id] for voucher_id in keys
        ]


class VoucherInfoByVoucherCodeLoader(DataLoader[str, Optional[VoucherInfo]]):
    context_key = "voucher_info_by_voucher_code"

    def batch_load(self, keys):
        # FIXME dataloader should not operate on prefetched data. The channel
        #  listings are used in Voucher's model to calculate a discount amount.
        #  This is a workaround that we should solve by fetching channel_listings
        #  via data loader and passing it to calculate a discount amount.
        voucher_codes_map = (
            VoucherCode.objects.using(self.database_connection_name)
            .prefetch_related("voucher__channel_listings")
            .filter(code__in=keys)
            .in_bulk(field_name="code")
        )

        vouchers = set([code.voucher for code in voucher_codes_map.values()])
        voucher_products = (
            Voucher.products.through.objects.using(self.database_connection_name)
            .filter(voucher__in=vouchers)
            .values_list("voucher_id", "product_id")
        )
        voucher_variants = (
            Voucher.variants.through.objects.using(self.database_connection_name)
            .filter(voucher__in=vouchers)
            .values_list("voucher_id", "productvariant_id")
        )
        voucher_collections = (
            Voucher.collections.through.objects.using(self.database_connection_name)
            .filter(voucher__in=vouchers)
            .values_list("voucher_id", "collection_id")
        )
        voucher_categories = (
            Voucher.categories.through.objects.using(self.database_connection_name)
            .filter(voucher__in=vouchers)
            .values_list("voucher_id", "category_id")
        )
        product_pks_map = defaultdict(list)
        variant_pks_map = defaultdict(list)
        category_pks_map = defaultdict(list)
        collection_pks_map = defaultdict(list)
        for voucher_id, product_id in voucher_products:
            product_pks_map[voucher_id].append(product_id)
        for voucher_id, variant_id in voucher_variants:
            variant_pks_map[voucher_id].append(variant_id)
        for voucher_id, category_id in voucher_categories:
            category_pks_map[voucher_id].append(category_id)
        for voucher_id, collection_id in voucher_collections:
            collection_pks_map[voucher_id].append(collection_id)

        voucher_infos: list[Optional[VoucherInfo]] = []
        for code in keys:
            voucher_code = voucher_codes_map.get(code)
            if not voucher_code:
                voucher_infos.append(None)
                continue
            voucher_infos.append(
                VoucherInfo(
                    voucher=voucher_code.voucher,
                    voucher_code=voucher_code.code,
                    product_pks=product_pks_map.get(voucher_code.voucher_id, []),
                    variant_pks=variant_pks_map.get(voucher_code.voucher_id, []),
                    category_pks=category_pks_map.get(voucher_code.voucher_id, []),
                    collection_pks=collection_pks_map.get(voucher_code.voucher_id, []),
                )
            )
        return voucher_infos


class OrderDiscountsByOrderIDLoader(DataLoader):
    context_key = "orderdiscounts_by_order_id"

    def batch_load(self, keys):
        discounts = OrderDiscount.objects.using(self.database_connection_name).filter(
            order_id__in=keys
        )
        discount_map = defaultdict(list)
        for discount in discounts:
            discount_map[discount.order_id].append(discount)
        return [discount_map.get(order_id, []) for order_id in keys]


class CheckoutLineDiscountsByCheckoutLineIdLoader(DataLoader):
    context_key = "checkout_line_discounts_by_checkout_line_id"

    def batch_load(self, keys):
        discounts = CheckoutLineDiscount.objects.using(
            self.database_connection_name
        ).filter(line_id__in=keys)
        discount_map = defaultdict(list)
        for discount in discounts:
            discount_map[discount.line_id].append(discount)
        return [discount_map.get(checkout_line_id, []) for checkout_line_id in keys]


class CheckoutDiscountByCheckoutIdLoader(DataLoader):
    context_key = "checkout_discount_by_checkout_id"

    def batch_load(self, keys):
        checkout_line_discounts = CheckoutDiscount.objects.using(
            self.database_connection_name
        ).filter(checkout_id__in=keys)
        checkout_line_discounts_map = defaultdict(list)
        for discount in checkout_line_discounts:
            checkout_line_discounts_map[discount.checkout_id].append(discount)
        return [
            checkout_line_discounts_map.get(checkout_id, []) for checkout_id in keys
        ]


class PromotionRulesByPromotionIdLoader(DataLoader):
    context_key = "promotion_rules_by_promotion_id"

    def batch_load(self, keys):
        promotions = Promotion.objects.using(self.database_connection_name).filter(
            id__in=keys
        )
        rules = PromotionRule.objects.using(self.database_connection_name).filter(
            Exists(promotions.filter(id=OuterRef("promotion_id")))
        )
        rules_map = defaultdict(list)
        for rule in rules:
            rules_map[rule.promotion_id].append(rule)
        return [rules_map.get(promotion_id, []) for promotion_id in keys]


class PromotionEventsByPromotionIdLoader(DataLoader):
    context_key = "promotion_events_by_promotion_id"

    def batch_load(self, keys):
        promotions = Promotion.objects.using(self.database_connection_name).filter(
            id__in=keys
        )
        events = PromotionEvent.objects.using(self.database_connection_name).filter(
            Exists(promotions.filter(id=OuterRef("promotion_id")))
        )
        events_map = defaultdict(list)
        for event in events:
            events_map[event.promotion_id].append(event)
        return [events_map.get(promotion_id, []) for promotion_id in keys]


class PromotionByIdLoader(DataLoader):
    context_key = "promotion_by_id"

    def batch_load(self, keys):
        promotions = Promotion.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [promotions.get(id) for id in keys]


class ChannelsByPromotionRuleIdLoader(DataLoader):
    context_key = "channels_by_promotion_rule_id"

    def batch_load(self, keys):
        PromotionRuleChannel = PromotionRule.channels.through
        rule_channels = PromotionRuleChannel.objects.using(
            self.database_connection_name
        ).filter(promotionrule_id__in=keys)
        channels = (
            Channel.objects.using(self.database_connection_name)
            .filter(id__in=rule_channels.values("channel_id"))
            .in_bulk()
        )
        rule_to_channels_map = defaultdict(list)
        for rule_id, channel_id in rule_channels.values_list(
            "promotionrule_id", "channel_id"
        ):
            rule_to_channels_map[rule_id].append(channels.get(channel_id))
        return [rule_to_channels_map.get(rule_id, []) for rule_id in keys]


class PromotionRuleByIdLoader(DataLoader):
    context_key = "promotion_rule_by_id"

    def batch_load(self, keys):
        rules = PromotionRule.objects.using(self.database_connection_name).in_bulk(keys)
        return [rules.get(id) for id in keys]


class PromotionByRuleIdLoader(DataLoader):
    context_key = "promotion_by_rule_id"

    def batch_load(self, keys):
        rules = PromotionRule.objects.using(self.database_connection_name).filter(
            id__in=keys
        )
        promotions = (
            Promotion.objects.using(self.database_connection_name)
            .filter(Exists(rules.filter(promotion_id=OuterRef("id"))))
            .in_bulk()
        )
        promotion_map = {rule.id: promotions.get(rule.promotion_id) for rule in rules}
        return [promotion_map.get(rule_id) for rule_id in keys]


class SaleChannelListingByPromotionIdLoader(DataLoader):
    context_key = "sale_channel_listing_by_promotion_id"

    def batch_load(self, keys):
        from .types.sales import SaleChannelListing

        def with_rules(rules):
            rule_ids = [rule.id for item in rules for rule in item]

            def with_channels(channels):
                rule_channels = dict(zip(rule_ids, channels))
                promotion_listing_map = defaultdict(list)
                for promotion_id, promotion_rules in zip(keys, rules):
                    for rule in promotion_rules:
                        channels = rule_channels[rule.id]
                        for channel in channels:
                            promotion_listing_map[promotion_id].append(
                                SaleChannelListing(
                                    id=rule.old_channel_listing_id,
                                    channel=channel,
                                    discount_value=rule.reward_value,
                                    currency=channel.currency_code,
                                )
                            )
                return [promotion_listing_map[key] for key in keys]

            return (
                ChannelsByPromotionRuleIdLoader(self.context)
                .load_many(rule_ids)
                .then(with_channels)
            )

        return (
            PromotionRulesByPromotionIdLoader(self.context)
            .load_many(keys)
            .then(with_rules)
        )


class PromotionRulesByPromotionIdAndChannelSlugLoader(DataLoader):
    context_key = "promotion_rules_by_promotion_id_and_channel_slug"

    def batch_load(self, keys):
        promotion_ids = [key[0] for key in keys]
        channel_slug = keys[0][1]
        channel = ChannelBySlugLoader(self.context).load(channel_slug)

        def with_channel(data):
            channel, promotion_ids = data
            promotions = Promotion.objects.using(self.database_connection_name).filter(
                id__in=promotion_ids
            )
            PromotionRuleChannel = PromotionRule.channels.through
            rule_channels = PromotionRuleChannel.objects.using(
                self.database_connection_name
            ).filter(channel_id=channel.id)

            rules = PromotionRule.objects.using(self.database_connection_name).filter(
                Exists(promotions.filter(id=OuterRef("promotion_id"))),
                Exists(rule_channels.filter(promotionrule_id=OuterRef("id"))),
            )

            promotion_rule_map = defaultdict(list)
            for rule in rules:
                promotion_rule_map[rule.promotion_id].append(rule)

            return [promotion_rule_map[promotion_id] for promotion_id, _ in keys]

        return Promise.all([channel, promotion_ids]).then(with_channel)


class PredicateByPromotionIdLoader(DataLoader):
    context_key = "predicate_by_promotion_id_and_channel_slug"

    def batch_load(self, keys):
        def with_rules(rules):
            from .utils import convert_migrated_sale_predicate_to_model_ids

            rules = [rule for item in rules for rule in item]
            promotion_predicated_map = defaultdict(list)
            for rule in rules:
                converted_predicate = convert_migrated_sale_predicate_to_model_ids(
                    rule.catalogue_predicate
                )
                promotion_predicated_map[rule.promotion_id].append(converted_predicate)

            promotion_merged_predicated_map = {}
            for promotion_id, predicates in promotion_predicated_map.items():
                merged_predicates: dict = defaultdict(list)
                for predicate in predicates:
                    if not predicate:
                        continue
                    for key, ids in predicate.items():
                        merged_predicates[key].extend(ids)
                promotion_merged_predicated_map[promotion_id] = merged_predicates

            return [promotion_merged_predicated_map[key] for key in keys]

        return (
            PromotionRulesByPromotionIdLoader(self.context)
            .load_many(keys)
            .then(with_rules)
        )


class GiftsByPromotionRuleIDLoader(DataLoader):
    context_key = "gifts_by_promotion_rule"

    def batch_load(self, keys):
        PromotionRuleGift = PromotionRule.gifts.through
        rule_gifts = (
            PromotionRuleGift.objects.using(self.database_connection_name)
            .filter(promotionrule_id__in=keys)
            .order_by("pk")
        )
        gifts = (
            ProductVariant.objects.using(self.database_connection_name)
            .filter(Exists(rule_gifts.filter(productvariant_id=OuterRef("id"))))
            .in_bulk()
        )
        rule_to_gifts_map = defaultdict(list)
        for rule_id, variant_id in rule_gifts.values_list(
            "promotionrule_id", "productvariant_id"
        ):
            rule_to_gifts_map[rule_id].append(gifts.get(variant_id))
        return [rule_to_gifts_map.get(rule_id, []) for rule_id in keys]
