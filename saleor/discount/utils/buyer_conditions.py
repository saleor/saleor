from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from django.conf import settings
from django.db.models import BooleanField, Count, Exists, ExpressionWrapper, OuterRef

from ...core.tracing import traced_atomic_transaction
from ...core.utils.unset import UNSET, Unset
from ...product.scoped_prices import BuyerConditions
from ..lock_objects import promotion_rule_qs_select_for_update
from ..models import (
    PromotionRule,
    PromotionRuleCustomerAttributeValue,
    PromotionRuleCustomerType,
)


def rule_has_buyer_conditions_expression() -> ExpressionWrapper:
    """Return a boolean expression telling whether a rule has buyer conditions.

    Meant for annotations and filters on `PromotionRule` querysets.
    """
    type_conditions = PromotionRuleCustomerType.objects.filter(rule_id=OuterRef("pk"))
    value_conditions = PromotionRuleCustomerAttributeValue.objects.filter(
        rule_id=OuterRef("pk")
    )
    return ExpressionWrapper(
        Exists(type_conditions) | Exists(value_conditions),
        output_field=BooleanField(),
    )


def get_rule_buyer_conditions(
    rule_ids: Iterable[UUID],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> dict[UUID, BuyerConditions]:
    """Return the buyer conditions of the rules, keyed by rule id.

    Rules without conditions are absent from the result. Two queries are run
    for any number of rules.
    """
    rule_ids = list(rule_ids)
    if not rule_ids:
        return {}
    customer_type_ids_by_rule_id: dict[UUID, set[int]] = defaultdict(set)
    type_conditions = (
        PromotionRuleCustomerType.objects.using(database_connection_name)
        .filter(rule_id__in=rule_ids)
        .values_list("rule_id", "customer_type_id")
    )
    for rule_id, customer_type_id in type_conditions:
        customer_type_ids_by_rule_id[rule_id].add(customer_type_id)
    value_ids_by_rule_id: dict[UUID, dict[int, set[int]]] = defaultdict(
        lambda: defaultdict(set)
    )
    value_conditions = (
        PromotionRuleCustomerAttributeValue.objects.using(database_connection_name)
        .filter(rule_id__in=rule_ids)
        .values_list("rule_id", "value__attribute_id", "value_id")
    )
    for rule_id, attribute_id, value_id in value_conditions:
        value_ids_by_rule_id[rule_id][attribute_id].add(value_id)
    return {
        rule_id: BuyerConditions(
            customer_type_ids=frozenset(customer_type_ids_by_rule_id[rule_id]),
            value_ids_by_attribute_id={
                attribute_id: frozenset(value_ids)
                for attribute_id, value_ids in value_ids_by_rule_id[rule_id].items()
            },
        )
        for rule_id in set(customer_type_ids_by_rule_id) | set(value_ids_by_rule_id)
    }


def create_rule_buyer_conditions(
    conditions_per_rule: Iterable[tuple[PromotionRule, Iterable[int], Iterable[int]]],
) -> None:
    """Add the customer types and attribute values to freshly created rules.

    Takes `(rule, customer_type_ids, attribute_value_ids)` triples and writes
    all of them in two queries.
    """
    type_conditions: list[PromotionRuleCustomerType] = []
    value_conditions: list[PromotionRuleCustomerAttributeValue] = []
    for rule, customer_type_ids, attribute_value_ids in conditions_per_rule:
        type_conditions.extend(
            PromotionRuleCustomerType(rule=rule, customer_type_id=customer_type_id)
            for customer_type_id in sorted(customer_type_ids)
        )
        value_conditions.extend(
            PromotionRuleCustomerAttributeValue(rule=rule, value_id=value_id)
            for value_id in sorted(attribute_value_ids)
        )
    PromotionRuleCustomerType.objects.bulk_create(type_conditions)
    PromotionRuleCustomerAttributeValue.objects.bulk_create(value_conditions)


def set_rule_buyer_conditions(
    rule: PromotionRule,
    customer_type_ids: frozenset[int] | Unset = UNSET,
    attribute_value_ids: frozenset[int] | Unset = UNSET,
) -> None:
    """Replace the buyer conditions of the rule per dimension.

    A dimension left unset keeps its conditions, a given set replaces them and
    only the differences are written. The rule is locked while the current
    conditions are read, so two concurrent updates cannot revert each other.
    """
    with traced_atomic_transaction():
        list(
            promotion_rule_qs_select_for_update()
            .filter(pk=rule.pk)
            .values_list("pk", flat=True)
        )
        if customer_type_ids is not UNSET:
            current_type_ids = frozenset(
                PromotionRuleCustomerType.objects.filter(rule_id=rule.pk).values_list(
                    "customer_type_id", flat=True
                )
            )
            if removed_type_ids := current_type_ids - customer_type_ids:
                PromotionRuleCustomerType.objects.filter(
                    rule_id=rule.pk, customer_type_id__in=removed_type_ids
                ).delete()
            PromotionRuleCustomerType.objects.bulk_create(
                [
                    PromotionRuleCustomerType(rule=rule, customer_type_id=type_id)
                    for type_id in sorted(customer_type_ids - current_type_ids)
                ]
            )
        if attribute_value_ids is not UNSET:
            current_value_ids = frozenset(
                PromotionRuleCustomerAttributeValue.objects.filter(
                    rule_id=rule.pk
                ).values_list("value_id", flat=True)
            )
            if removed_value_ids := current_value_ids - attribute_value_ids:
                PromotionRuleCustomerAttributeValue.objects.filter(
                    rule_id=rule.pk, value_id__in=removed_value_ids
                ).delete()
            PromotionRuleCustomerAttributeValue.objects.bulk_create(
                [
                    PromotionRuleCustomerAttributeValue(rule=rule, value_id=value_id)
                    for value_id in sorted(attribute_value_ids - current_value_ids)
                ]
            )


def count_promotion_rules_for_customer_type(customer_type_id: int) -> int:
    return PromotionRuleCustomerType.objects.filter(
        customer_type_id=customer_type_id
    ).count()


def count_promotion_rules_for_attribute_values(value_ids: Iterable[int]) -> int:
    """Return how many rules reference any of the values, each rule counted once."""
    return (
        PromotionRuleCustomerAttributeValue.objects.filter(value_id__in=list(value_ids))
        .values("rule_id")
        .distinct()
        .count()
    )


def count_promotion_rules_by_attribute_value_id(
    value_ids: Iterable[int],
) -> dict[int, int]:
    """Return how many rules reference each value, only for referenced values."""
    return dict(
        PromotionRuleCustomerAttributeValue.objects.filter(value_id__in=list(value_ids))
        .values("value_id")
        .annotate(rule_count=Count("rule_id", distinct=True))
        .values_list("value_id", "rule_count")
    )


def count_promotion_rules_by_attribute_id(
    attribute_ids: Iterable[int],
) -> dict[int, int]:
    """Return how many rules reference a value of each attribute.

    Only referenced attributes are present. A rule referencing two values of
    the same attribute is counted once.
    """
    return dict(
        PromotionRuleCustomerAttributeValue.objects.filter(
            value__attribute_id__in=list(attribute_ids)
        )
        .values("value__attribute_id")
        .annotate(rule_count=Count("rule_id", distinct=True))
        .values_list("value__attribute_id", "rule_count")
    )
