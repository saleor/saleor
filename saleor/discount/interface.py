from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple, Optional

from django.db import DEFAULT_DB_ALIAS
from django.db.models import CharField, Value

from . import DiscountType, DiscountValueType
from .models import PromotionRule, Voucher

if TYPE_CHECKING:
    from ..product.models import (
        Product,
        ProductVariant,
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


@dataclass(frozen=True)
class VoucherCatalogue:
    """PKs of catalogue entities a voucher includes or excludes."""

    product_pks: frozenset[int] = frozenset()
    variant_pks: frozenset[int] = frozenset()
    collection_pks: frozenset[int] = frozenset()
    category_pks: frozenset[int] = frozenset()
    product_type_pks: frozenset[int] = frozenset()

    def is_empty(self) -> bool:
        return not (
            self.product_pks
            or self.variant_pks
            or self.collection_pks
            or self.category_pks
            or self.product_type_pks
        )

    def matches(
        self,
        variant: "ProductVariant",
        product: "Product",
        collection_pks: set[int],
    ) -> bool:
        """Category matching is exact; descendants of a category do not match."""
        return (
            variant.pk in self.variant_pks
            or product.pk in self.product_pks
            or product.category_id in self.category_pks
            or product.product_type_id in self.product_type_pks
            or not self.collection_pks.isdisjoint(collection_pks)
        )


class VoucherCatalogueRelation(NamedTuple):
    catalogue_field: str
    included_field: str
    excluded_field: str


VOUCHER_CATALOGUE_RELATIONS = (
    VoucherCatalogueRelation("product_pks", "products", "excluded_products"),
    VoucherCatalogueRelation("variant_pks", "variants", "excluded_variants"),
    VoucherCatalogueRelation("collection_pks", "collections", "excluded_collections"),
    VoucherCatalogueRelation("category_pks", "categories", "excluded_categories"),
    VoucherCatalogueRelation(
        "product_type_pks", "product_types", "excluded_product_types"
    ),
)


@dataclass
class VoucherInfo:
    """It contains the voucher's details and PKs of all applicable objects."""

    voucher: Voucher
    voucher_code: str | None
    included: VoucherCatalogue
    excluded: VoucherCatalogue


def fetch_voucher_relation_pks(
    voucher_pks: Iterable[int], database_connection_name: str
) -> dict[int, dict[str, set[int]]]:
    """Return related PKs per voucher PK and Voucher M2M field name.

    All catalogue relations are read in a single UNION ALL query.
    """
    querysets = []
    for relation in VOUCHER_CATALOGUE_RELATIONS:
        for field_name in (relation.included_field, relation.excluded_field):
            field = Voucher._meta.get_field(field_name)
            querysets.append(
                field.remote_field.through.objects.using(database_connection_name)  # type: ignore[union-attr]
                .filter(voucher_id__in=voucher_pks)
                .annotate(relation=Value(field_name, output_field=CharField()))
                .values_list("voucher_id", field.m2m_reverse_field_name(), "relation")  # type: ignore[union-attr]
            )
    pks_by_voucher: dict[int, dict[str, set[int]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for voucher_pk, related_pk, field_name in querysets[0].union(
        *querysets[1:], all=True
    ):
        pks_by_voucher[voucher_pk][field_name].add(related_pk)
    return pks_by_voucher


def build_voucher_info(
    voucher: Voucher,
    voucher_code: str | None,
    related_pks: Mapping[str, set[int]],
) -> VoucherInfo:
    return VoucherInfo(
        voucher=voucher,
        voucher_code=voucher_code,
        included=VoucherCatalogue(
            **{
                relation.catalogue_field: frozenset(
                    related_pks.get(relation.included_field, ())
                )
                for relation in VOUCHER_CATALOGUE_RELATIONS
            }
        ),
        excluded=VoucherCatalogue(
            **{
                relation.catalogue_field: frozenset(
                    related_pks.get(relation.excluded_field, ())
                )
                for relation in VOUCHER_CATALOGUE_RELATIONS
            }
        ),
    )


def fetch_voucher_info(
    voucher: Voucher, voucher_code: str | None = None
) -> VoucherInfo:
    related_pks = fetch_voucher_relation_pks(
        [voucher.pk], voucher._state.db or DEFAULT_DB_ALIAS
    )
    return build_voucher_info(voucher, voucher_code, related_pks.get(voucher.pk, {}))


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
