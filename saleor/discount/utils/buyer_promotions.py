from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, Union, cast
from uuid import UUID

from django.conf import settings
from django.db.models import Exists, OuterRef, prefetch_related_objects
from prices import Money

from ...checkout.models import CheckoutLine
from ...core.taxes import zero_money
from ...product.models import ProductVariant
from ...product.scoped_prices import BuyerConditions, PricingBuyer, get_pricing_buyers
from ..interface import VariantPromotionRuleInfo, get_rule_translations
from ..models import Promotion, PromotionRule
from .buyer_conditions import (
    get_rule_buyer_conditions,
    rule_has_buyer_conditions_expression,
)

if TYPE_CHECKING:
    from ...channel.models import Channel
    from ...checkout.fetch import CheckoutLineInfo
    from ...order.fetch import EditableOrderLineInfo
    from ...order.models import OrderLine


class RuleDiscount(NamedTuple):
    rule: "PromotionRule"
    discount: Money


def get_best_rule_discount(
    price: Money, rules: Iterable["PromotionRule"], currency: str
) -> RuleDiscount | None:
    """Return the rule that takes the most off the price, with that amount.

    A tie keeps the rule given first, so callers list the stored rule of the
    listing before the rules resolved for the buyer.
    """
    best: RuleDiscount | None = None
    for rule in rules:
        discount = rule.get_discount(currency)
        amount = price - discount(price)
        if best is None or amount > best.discount:
            best = RuleDiscount(rule, amount)
    return best


def calculate_best_discounted_price_for_rules(
    *, price: Money, rules: Iterable["PromotionRule"], currency: str
) -> Money:
    """Apply the best of the rules to the price, as the stored price does."""
    best = get_best_rule_discount(price, rules, currency)
    if best is None:
        return price
    return max(price - best.discount, zero_money(currency))


def get_line_price_override(
    line: Union["CheckoutLine", "OrderLine"], currency: str
) -> Money | None:
    if isinstance(line, CheckoutLine):
        if line.price_override is None:
            return None
        return Money(line.price_override, currency)
    return line.undiscounted_base_unit_price if line.is_price_overridden else None


@dataclass(frozen=True)
class BuyerPromotionRuleCandidates:
    """The active buyer-conditioned rules of a channel that cover some variants."""

    rules_by_id: dict[UUID, PromotionRule]
    conditions_by_rule_id: dict[UUID, BuyerConditions]
    rule_ids_by_variant_id: dict[int, list[UUID]]


EMPTY_BUYER_PROMOTION_RULE_CANDIDATES = BuyerPromotionRuleCandidates({}, {}, {})


def get_buyer_promotion_rule_candidates(
    variant_ids: Iterable[int],
    channel_id: int,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> BuyerPromotionRuleCandidates:
    """Return the buyer-conditioned rules that may discount the variants.

    A rule qualifies when its promotion is active, it applies in the channel,
    it has buyer conditions and its catalogue predicate covers the variant.
    One query is run when no such rule exists, four otherwise.
    """
    variant_ids = list(variant_ids)
    if not variant_ids:
        return EMPTY_BUYER_PROMOTION_RULE_CANDIDATES
    promotions = Promotion.objects.using(database_connection_name).active()
    PromotionRuleChannel = PromotionRule.channels.through
    rule_channels = PromotionRuleChannel.objects.using(database_connection_name).filter(
        channel_id=channel_id, promotionrule_id=OuterRef("pk")
    )
    rules = (
        PromotionRule.objects.using(database_connection_name)
        .annotate(has_buyer_conditions=rule_has_buyer_conditions_expression())
        .filter(
            Exists(promotions.filter(id=OuterRef("promotion_id"))),
            Exists(rule_channels),
            has_buyer_conditions=True,
        )
    )
    PromotionRuleVariant = PromotionRule.variants.through
    rule_variants = list(
        PromotionRuleVariant.objects.using(database_connection_name)
        .filter(
            Exists(rules.filter(pk=OuterRef("promotionrule_id"))),
            productvariant_id__in=variant_ids,
        )
        .order_by("promotionrule_id")
        .values_list("promotionrule_id", "productvariant_id")
    )
    if not rule_variants:
        return EMPTY_BUYER_PROMOTION_RULE_CANDIDATES
    rule_ids_by_variant_id: dict[int, list[UUID]] = defaultdict(list)
    for rule_id, variant_id in rule_variants:
        rule_ids_by_variant_id[variant_id].append(rule_id)
    rule_ids = {rule_id for rule_id, _ in rule_variants}
    rules_by_id = (
        PromotionRule.objects.using(database_connection_name)
        .select_related("promotion")
        .in_bulk(rule_ids)
    )
    return BuyerPromotionRuleCandidates(
        rules_by_id=rules_by_id,
        conditions_by_rule_id=get_rule_buyer_conditions(
            rule_ids, database_connection_name
        ),
        rule_ids_by_variant_id=dict(rule_ids_by_variant_id),
    )


def select_buyer_promotion_rules(
    candidates: BuyerPromotionRuleCandidates, buyer: PricingBuyer | None
) -> dict[int, list[PromotionRule]]:
    """Return the candidate rules the buyer matches, keyed by variant id.

    A guest matches none. The translations of the matching rules are
    prefetched, so the discount names can be built without further queries.
    """
    if buyer is None or not candidates.rules_by_id:
        return {}
    matching_rule_ids = {
        rule_id
        for rule_id, conditions in candidates.conditions_by_rule_id.items()
        if conditions.match_buyer(buyer) is not None
    }
    if not matching_rule_ids:
        return {}
    prefetch_related_objects(
        [candidates.rules_by_id[rule_id] for rule_id in matching_rule_ids],
        "translations",
        "promotion__translations",
    )
    rules_by_variant_id = {}
    for variant_id, rule_ids in candidates.rule_ids_by_variant_id.items():
        rules = [
            candidates.rules_by_id[rule_id]
            for rule_id in rule_ids
            if rule_id in matching_rule_ids
        ]
        if rules:
            rules_by_variant_id[variant_id] = rules
    return rules_by_variant_id


def get_buyer_promotion_rules(
    variant_ids: Iterable[int],
    channel_id: int,
    user_id: int | None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> dict[int, list[PromotionRule]]:
    """Return the buyer-conditioned rules that apply to the user, keyed by variant id.

    A guest gets none without a query. The buyer is looked up only when a
    candidate rule exists.
    """
    if user_id is None:
        return {}
    candidates = get_buyer_promotion_rule_candidates(
        variant_ids, channel_id, database_connection_name
    )
    if not candidates.rules_by_id:
        return {}
    buyer = get_pricing_buyers([user_id], database_connection_name).get(user_id)
    return select_buyer_promotion_rules(candidates, buyer)


def get_line_base_price(
    line_info: Union["CheckoutLineInfo", "EditableOrderLineInfo"],
) -> Money | None:
    """Return the price the catalogue rules of the line apply to.

    A custom price wins over a scoped price, which wins over the listing price.
    `None` when the line has no priced listing.
    """
    listing = line_info.channel_listing
    if listing is None or listing.price is None:
        return None
    price_override = get_line_price_override(line_info.line, listing.currency)
    if price_override is not None:
        return price_override
    if line_info.scoped_unit_price is not None:
        return line_info.scoped_unit_price
    return listing.price


def attach_buyer_promotion_rules(
    lines_info: Iterable[Union["CheckoutLineInfo", "EditableOrderLineInfo"]],
    user_id: int | None,
    channel: "Channel",
    language_code: str,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> None:
    """Let the buyer-conditioned rules compete with the stored rule of each line.

    The stored rule of a listing is the guest rule. Rules with buyer conditions
    are never stored, so they are resolved here for the user and the rule that
    takes the most off the base price of the line wins. The stored rule keeps a
    tie. Gift lines and lines without a priced listing are left alone.
    """
    lines_info = [
        line_info
        for line_info in lines_info
        if line_info.variant is not None
        and not line_info.line.is_gift
        and get_line_base_price(line_info) is not None
    ]
    rules_by_variant_id = get_buyer_promotion_rules(
        {line_info.variant.pk for line_info in lines_info if line_info.variant},
        channel.id,
        user_id,
        database_connection_name,
    )
    if not rules_by_variant_id:
        return
    currency = channel.currency_code
    for line_info in lines_info:
        variant = cast(ProductVariant, line_info.variant)
        buyer_rules = rules_by_variant_id.get(variant.pk)
        if not buyer_rules:
            continue
        rules_info = resolve_buyer_rules_info(
            cast(Money, get_line_base_price(line_info)),
            line_info.rules_info or [],
            buyer_rules,
            currency,
            language_code,
        )
        if rules_info is not None:
            line_info.rules_info = rules_info


def resolve_buyer_rules_info(
    base_price: Money,
    stored_rules_info: Iterable[VariantPromotionRuleInfo],
    buyer_rules: Iterable[PromotionRule],
    currency: str,
    language_code: str,
) -> list[VariantPromotionRuleInfo] | None:
    """Return the rule info of a buyer rule when it beats the stored rule.

    `None` means the stored rule stays, which includes a tie. The buyer rule
    has no stored listing rule, its discount is computed on the base price.
    """
    stored_rules = [rule_info.rule for rule_info in stored_rules_info]
    best = get_best_rule_discount(base_price, [*stored_rules, *buyer_rules], currency)
    if best is None or any(rule.pk == best.rule.pk for rule in stored_rules):
        return None
    promotion = best.rule.promotion
    promotion_translation, rule_translation = get_rule_translations(
        promotion, best.rule, language_code
    )
    return [
        VariantPromotionRuleInfo(
            rule=best.rule,
            variant_listing_promotion_rule=None,
            promotion=promotion,
            promotion_translation=promotion_translation,
            rule_translation=rule_translation,
            resolved_for_buyer=True,
        )
    ]
