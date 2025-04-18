from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple, Optional

from . import DiscountType, DiscountValueType
from .models import PromotionRule, Voucher

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
class DiscountInfo:
    """It stores the discount details.

    The dataclass used to represent the discount before storing it on database side.
    """

    currency: str
    type: str = DiscountType.MANUAL
    value_type: str = DiscountValueType.FIXED
    value: Decimal = Decimal("0.0")
    amount_value: Decimal = Decimal("0.0")
    name: str | None = None
    translated_name: str | None = None
    reason: str | None = None
    promotion_rule: PromotionRule | None = None
    voucher: Voucher | None = None
    voucher_code: str | None = None


@dataclass
class VoucherInfo:
    """It contains the voucher's details and PKs of all applicable objects."""

    voucher: Voucher
    voucher_code: str | None
    product_pks: list[int]
    variant_pks: list[int]
    collection_pks: list[int]
    category_pks: list[int]


def fetch_voucher_info(
    voucher: Voucher, voucher_code: str | None = None
) -> VoucherInfo:
    variant_pks = [variant.id for variant in voucher.variants.all()]
    product_pks = [product.id for product in voucher.products.all()]
    category_pks = [category.id for category in voucher.categories.all()]
    collection_pks = [collection.id for collection in voucher.collections.all()]

    return VoucherInfo(
        voucher=voucher,
        voucher_code=voucher_code,
        product_pks=product_pks,
        variant_pks=variant_pks,
        collection_pks=collection_pks,
        category_pks=category_pks,
    )


class VariantPromotionRuleInfo(NamedTuple):
    rule: "PromotionRule"
    variant_listing_promotion_rule: Optional["VariantChannelListingPromotionRule"]
    promotion: "Promotion"
    promotion_translation: Optional["PromotionTranslation"]
    rule_translation: Optional["PromotionRuleTranslation"]


def fetch_variant_rules_info(
    variant_channel_listing: Optional["ProductVariantChannelListing"],
    translation_language_code: str,
) -> list[VariantPromotionRuleInfo]:
    listings_rules = (
        variant_channel_listing.variantlistingpromotionrule.all()
        if variant_channel_listing
        else []
    )

    rules_info = []
    if listings_rules:
        # Before introducing unique_type on discount models, there was possibility
        # to have multiple catalogue discount associated with single line. In such a
        # case, we should pick the best discount (with the highest discount amount)
        listing_promotion_rule = max(
            list(listings_rules),
            key=lambda x: x.discount_amount,
        )
        promotion = listing_promotion_rule.promotion_rule.promotion

        promotion_translation, rule_translation = get_rule_translations(
            promotion, listing_promotion_rule.promotion_rule, translation_language_code
        )
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


def get_rule_translations(
    promotion: "Promotion", rule: "PromotionRule", translation_language_code: str
):
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
        for translation in rule.translations.all()
        if translation.language_code == translation_language_code
    ]
    rule_translation = rule_translations[0] if rule_translations else None

    return promotion_translation, rule_translation
