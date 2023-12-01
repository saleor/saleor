from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, Optional

from .models import Voucher

if TYPE_CHECKING:
    from ..product.models import (
        ProductVariantChannelListing,
        VariantChannelListingPromotionRule,
    )
    from .models import (
        Promotion,
        PromotionRule,
        PromotionRuleTranslation,
        PromotionTranslation,
    )


@dataclass
class VoucherInfo:
    """It contains the voucher's details and PKs of all applicable objects."""

    voucher: Voucher
    product_pks: list[int]
    variant_pks: list[int]
    collection_pks: list[int]
    category_pks: list[int]


def fetch_voucher_info(voucher: Voucher) -> VoucherInfo:
    variant_pks = list(variant.id for variant in voucher.variants.all())
    product_pks = list(product.id for product in voucher.products.all())
    category_pks = list(category.id for category in voucher.categories.all())
    collection_pks = list(collection.id for collection in voucher.collections.all())

    return VoucherInfo(
        voucher=voucher,
        product_pks=product_pks,
        variant_pks=variant_pks,
        collection_pks=collection_pks,
        category_pks=category_pks,
    )


class VariantPromotionRuleInfo(NamedTuple):
    rule: "PromotionRule"
    variant_listing_promotion_rule: "VariantChannelListingPromotionRule"
    promotion: "Promotion"
    promotion_translation: Optional["PromotionTranslation"]
    rule_translation: Optional["PromotionRuleTranslation"]


def fetch_variant_rules_info(
    variant_channel_listing: "ProductVariantChannelListing",
    translation_language_code: str,
):
    listings_rules = (
        variant_channel_listing.variantlistingpromotionrule.all()
        if variant_channel_listing
        else []
    )
    rules_info = []
    for listing_promotion_rule in listings_rules:
        promotion = listing_promotion_rule.promotion_rule.promotion
        promotion_translations = [
            translation
            for translation in promotion.translations.all()
            if translation.language_code == translation_language_code
        ]
        promotion_translation = (
            promotion_translations[0] if promotion_translations else None
        )

        rule_translations = [
            translation
            for translation in listing_promotion_rule.promotion_rule.translations.all()
            if translation.language_code == translation_language_code
        ]
        rule_translation = rule_translations[0] if rule_translations else None

        rules_info.append(
            VariantPromotionRuleInfo(
                rule=listing_promotion_rule.promotion_rule,
                variant_listing_promotion_rule=listing_promotion_rule,
                promotion=promotion,
                promotion_translation=promotion_translation,
                rule_translation=rule_translation,
            )
        )
    return rules_info
