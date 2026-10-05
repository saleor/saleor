from collections.abc import Iterable
from typing import NamedTuple

from prices import Money
from promise import Promise

from ....discount.models import PromotionRule
from ....product.scoped_prices import (
    PricingBuyer,
    ScopedPriceRow,
    get_pricing_buyers,
    get_scoped_price_rows,
    resolve_scoped_price,
)
from ...core.context import SaleorContext
from ...core.dataloaders import DataLoader
from ...discount.dataloaders import PromotionRuleByIdLoader
from .products import VariantChannelListingPromotionRuleByListingIdLoader


class ScopedPriceRowsByListingIdLoader(DataLoader[int, list[ScopedPriceRow]]):
    context_key = "scoped_price_rows_by_listing_id"

    def batch_load(self, keys):
        rows_by_listing_id = get_scoped_price_rows(keys, self.database_connection_name)
        return [rows_by_listing_id.get(listing_id, []) for listing_id in keys]


class PricingBuyerByUserIdLoader(DataLoader[int, PricingBuyer | None]):
    context_key = "pricing_buyer_by_user_id"

    def batch_load(self, keys):
        buyer_by_user_id = get_pricing_buyers(keys, self.database_connection_name)
        return [buyer_by_user_id.get(user_id) for user_id in keys]


def load_scoped_prices(
    context: SaleorContext, listing_ids: Iterable[int], user_id: int | None
) -> Promise[dict[int, Money]]:
    """Resolve the scoped prices of the listings for the user, keyed by listing id.

    Listings without a matching row are absent. The buyer is looked up only when a
    row has a buyer condition and a user is given.
    """
    listing_ids = list(listing_ids)
    now = context.request_time

    def with_rows(rows_per_listing):
        rows_by_listing_id = {
            listing_id: rows
            for listing_id, rows in zip(listing_ids, rows_per_listing, strict=True)
            if rows
        }
        if not rows_by_listing_id:
            return Promise.resolve({})

        def resolve(buyer):
            scoped_prices = {}
            for listing_id, rows in rows_by_listing_id.items():
                price = resolve_scoped_price(rows, buyer, now)
                if price is not None:
                    scoped_prices[listing_id] = price
            return scoped_prices

        has_buyer_conditions = any(
            row.has_buyer_conditions
            for rows in rows_by_listing_id.values()
            for row in rows
        )
        if user_id is not None and has_buyer_conditions:
            return PricingBuyerByUserIdLoader(context).load(user_id).then(resolve)
        return Promise.resolve(resolve(None))

    return (
        ScopedPriceRowsByListingIdLoader(context).load_many(listing_ids).then(with_rows)
    )


class BuyerPricingData(NamedTuple):
    """Per-listing pricing inputs of the request user, keyed by listing id.

    Only listings with a scoped price are present in either mapping.
    """

    scoped_prices: dict[int, Money]
    promotion_rules_by_listing_id: dict[int, list[PromotionRule]]


def load_buyer_pricing_data(
    context: SaleorContext, listing_ids: Iterable[int]
) -> Promise[BuyerPricingData]:
    """Resolve the scoped prices of the listings for the request user.

    Promotion rules are loaded only for listings with a scoped price, because the
    stored discounted price covers the others.
    """
    user = context.user

    def with_scoped_prices(scoped_prices):
        if not scoped_prices:
            return Promise.resolve(BuyerPricingData({}, {}))
        scoped_listing_ids = list(scoped_prices)

        def with_listing_rules(listing_rules_per_listing):
            rule_ids_per_listing = [
                [listing_rule.promotion_rule_id for listing_rule in listing_rules]
                for listing_rules in listing_rules_per_listing
            ]
            rule_ids = sorted(
                {rule_id for rule_ids in rule_ids_per_listing for rule_id in rule_ids}
            )

            def with_rules(rules):
                rule_by_id = dict(zip(rule_ids, rules, strict=True))
                return BuyerPricingData(
                    scoped_prices=scoped_prices,
                    promotion_rules_by_listing_id={
                        listing_id: [rule_by_id[rule_id] for rule_id in rule_ids]
                        for listing_id, rule_ids in zip(
                            scoped_listing_ids, rule_ids_per_listing, strict=True
                        )
                    },
                )

            return PromotionRuleByIdLoader(context).load_many(rule_ids).then(with_rules)

        return (
            VariantChannelListingPromotionRuleByListingIdLoader(context)
            .load_many(scoped_listing_ids)
            .then(with_listing_rules)
        )

    # the request user is a lazy object, so it must be tested by truthiness
    return load_scoped_prices(context, listing_ids, user.pk if user else None).then(
        with_scoped_prices
    )
