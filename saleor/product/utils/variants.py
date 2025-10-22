from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import QuerySet

from ...attribute import AttributeType
from ...discount.models import PromotionRule
from ...discount.utils.promotion import update_rule_variant_relation
from ..models import ProductVariant

if TYPE_CHECKING:
    from ...attribute.models import Attribute


def generate_and_set_variant_name(
    variant: "ProductVariant", sku: str | None, save: bool | None = True
):
    """Generate ProductVariant's name based on its attributes."""
    attributes_display = []

    values_qs = variant.attributevalues.all()
    attributes_display.append(", ".join([str(value) for value in values_qs]))

    name = " / ".join(sorted(attributes_display))
    if not name:
        name = sku or variant.get_global_id()

    variant.name = name
    if save:
        variant.save(update_fields=["name", "updated_at"])
    return variant


def get_variant_selection_attributes(
    attributes: Iterable[tuple["Attribute", bool]],
) -> list[tuple["Attribute", bool]]:
    """Return attributes that can be used in variant selection.

    Attribute must be product attribute and attribute input type must be
    in ALLOWED_IN_VARIANT_SELECTION list.
    """
    return [
        (attribute, variant_selection)
        for attribute, variant_selection in attributes
        if variant_selection and attribute.type == AttributeType.PRODUCT_TYPE
    ]


def fetch_variants_for_promotion_rules(rules: QuerySet[PromotionRule]):
    from ...graphql.discount.utils import get_variants_for_catalogue_predicate

    PromotionRuleVariant = PromotionRule.variants.through
    new_rules_variants = []
    for rule in rules.iterator(chunk_size=1000):
        variants = get_variants_for_catalogue_predicate(
            rule.catalogue_predicate,
            database_connection_name=settings.DATABASE_CONNECTION_REPLICA_NAME,
        )
        new_rules_variants.extend(
            [
                PromotionRuleVariant(
                    promotionrule_id=rule.pk, productvariant_id=variant_id
                )
                for variant_id in set(variants.values_list("pk", flat=True))
            ]
        )
    return update_rule_variant_relation(rules, new_rules_variants)
