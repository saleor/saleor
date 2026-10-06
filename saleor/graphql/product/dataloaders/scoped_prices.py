from collections import defaultdict
from collections.abc import Iterable
from typing import NamedTuple

from graphql import GraphQLError
from prices import Money
from promise import Promise

from ....core.db.connection import allow_writer_in_context
from ....core.exceptions import PermissionDenied
from ....discount.models import PromotionRule
from ....discount.utils.buyer_promotions import (
    get_buyer_promotion_rule_candidates,
    select_buyer_promotion_rules,
)
from ....permission.enums import AccountPermissions, ProductPermissions
from ....permission.utils import all_permissions_required
from ....product.models import (
    ProductVariantChannelListing,
    VariantChannelListingPrice,
    VariantChannelListingPriceAttributeValue,
    VariantChannelListingPriceCustomerType,
)
from ....product.scoped_prices import (
    PricingBuyer,
    ScopedPriceRow,
    get_pricing_buyers,
    get_scoped_price_rows,
    resolve_scoped_price,
)
from ...account.dataloaders import UserByUserIdLoader
from ...core.context import SaleorContext
from ...core.dataloaders import DataLoader
from ...core.utils import from_global_id_or_error
from ...discount.dataloaders import PromotionRuleByIdLoader
from .products import VariantChannelListingPromotionRuleByListingIdLoader

PRICING_PREVIEW_PERMISSIONS = (
    ProductPermissions.MANAGE_PRODUCTS,
    AccountPermissions.MANAGE_USERS,
)


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


class VariantChannelListingPricesByListingIdLoader(
    DataLoader[int, list[VariantChannelListingPrice]]
):
    context_key = "variant_channel_listing_prices_by_listing_id"

    def batch_load(self, keys):
        rows = (
            VariantChannelListingPrice.objects.using(self.database_connection_name)
            .filter(variant_channel_listing_id__in=keys)
            .order_by("pk")
        )
        rows_by_listing_id = defaultdict(list)
        for row in rows:
            rows_by_listing_id[row.variant_channel_listing_id].append(row)
        return [rows_by_listing_id[listing_id] for listing_id in keys]


class CustomerTypeIdsByListingPriceIdLoader(DataLoader[int, list[int]]):
    context_key = "customer_type_ids_by_listing_price_id"

    def batch_load(self, keys):
        conditions = (
            VariantChannelListingPriceCustomerType.objects.using(
                self.database_connection_name
            )
            .filter(listing_price_id__in=keys)
            .order_by("customer_type_id")
            .values_list("listing_price_id", "customer_type_id")
        )
        type_ids_by_row_id = defaultdict(list)
        for row_id, customer_type_id in conditions:
            type_ids_by_row_id[row_id].append(customer_type_id)
        return [type_ids_by_row_id[row_id] for row_id in keys]


class AttributeValueIdsByListingPriceIdLoader(DataLoader[int, list[int]]):
    context_key = "attribute_value_ids_by_listing_price_id"

    def batch_load(self, keys):
        conditions = (
            VariantChannelListingPriceAttributeValue.objects.using(
                self.database_connection_name
            )
            .filter(listing_price_id__in=keys)
            .order_by("value_id")
            .values_list("listing_price_id", "value_id")
        )
        value_ids_by_row_id = defaultdict(list)
        for row_id, value_id in conditions:
            value_ids_by_row_id[row_id].append(value_id)
        return [value_ids_by_row_id[row_id] for row_id in keys]


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


class BuyerPromotionRulesByVariantIdLoader(
    DataLoader[tuple[int, int, int], list[PromotionRule]]
):
    """Load the buyer-conditioned rules the user matches for a variant.

    Keyed by `(variant_id, channel_id, user_id)`. The candidate rules are
    fetched once per channel, the buyers come from their own loader.
    """

    context_key = "buyer_promotion_rules_by_variant_id"

    def batch_load(self, keys):
        variant_ids_by_channel_id: dict[int, set[int]] = defaultdict(set)
        for variant_id, channel_id, _ in keys:
            variant_ids_by_channel_id[channel_id].add(variant_id)
        candidates_by_channel_id = {
            channel_id: get_buyer_promotion_rule_candidates(
                variant_ids, channel_id, self.database_connection_name
            )
            for channel_id, variant_ids in variant_ids_by_channel_id.items()
        }
        user_ids = sorted(
            {
                user_id
                for _, channel_id, user_id in keys
                if candidates_by_channel_id[channel_id].rules_by_id
            }
        )

        @allow_writer_in_context(self.context)
        def with_buyers(buyers):
            buyer_by_user_id = dict(zip(user_ids, buyers, strict=True))
            rules_by_scope = {
                (channel_id, user_id): select_buyer_promotion_rules(
                    candidates_by_channel_id[channel_id], buyer_by_user_id.get(user_id)
                )
                for channel_id, user_id in {(key[1], key[2]) for key in keys}
            }
            return [
                rules_by_scope[(channel_id, user_id)].get(variant_id, [])
                for variant_id, channel_id, user_id in keys
            ]

        if not user_ids:
            return with_buyers([])
        return (
            PricingBuyerByUserIdLoader(self.context)
            .load_many(user_ids)
            .then(with_buyers)
        )


class BuyerPricingData(NamedTuple):
    """Per-listing pricing inputs of the request user, keyed by listing id.

    `scoped_prices` holds the listings with a scoped price. The rules mapping
    holds the candidate rules of every listing whose price must be computed
    for the buyer: its stored rule and the buyer rules of its variant.
    """

    scoped_prices: dict[int, Money]
    promotion_rules_by_listing_id: dict[int, list[PromotionRule]]


def load_buyer_user_id(
    context: SaleorContext, customer_id: str | None
) -> Promise[int | None]:
    """Return the id of the user the prices are resolved for.

    Without a customer id that is the request user, or no one for a guest. A
    customer id previews the prices another user sees and needs both the product
    and the user management permissions, because the price reveals how the
    customer is segmented.
    """
    if customer_id is None:
        # the request user is a lazy object, so it must be tested by truthiness
        user = context.user
        return Promise.resolve(user.pk if user else None)
    if not all_permissions_required(context, PRICING_PREVIEW_PERMISSIONS):
        permission_list = ", ".join(p.name for p in PRICING_PREVIEW_PERMISSIONS)
        raise PermissionDenied(
            "To preview prices for a customer, you need all of the following "
            f"permissions: {permission_list}",
            permissions=PRICING_PREVIEW_PERMISSIONS,
        )
    _, user_pk = from_global_id_or_error(customer_id, "User", raise_error=True)

    def with_user(user):
        if user is None:
            raise GraphQLError(f"Couldn't resolve to a node: {customer_id}")
        return user.pk

    return UserByUserIdLoader(context).load(int(user_pk)).then(with_user)


def load_buyer_pricing_data(
    context: SaleorContext,
    listings: Iterable[ProductVariantChannelListing],
    user_id: int | None,
) -> Promise[BuyerPricingData]:
    """Resolve the scoped prices and the candidate rules of the listings for the user.

    Rules are loaded only for the listings with a scoped price or with a
    buyer-conditioned rule the user matches, because the stored discounted
    price covers the others. The availability helpers pick the best candidate.
    """
    listings = list(listings)
    listing_ids = [listing.pk for listing in listings]
    scoped_prices_promise = load_scoped_prices(context, listing_ids, user_id)
    buyer_rules_promise: Promise[list[list[PromotionRule]]]
    if user_id is None:
        buyer_rules_promise = Promise.resolve([[] for _ in listings])
    else:
        buyer_rules_promise = BuyerPromotionRulesByVariantIdLoader(context).load_many(
            [(listing.variant_id, listing.channel_id, user_id) for listing in listings]
        )

    def with_buyer_pricing(results):
        scoped_prices, buyer_rules_per_listing = results
        buyer_rules_by_listing_id = {
            listing.pk: rules
            for listing, rules in zip(listings, buyer_rules_per_listing, strict=True)
            if rules
        }
        rule_listing_ids = sorted(set(scoped_prices) | set(buyer_rules_by_listing_id))
        if not rule_listing_ids:
            return BuyerPricingData(scoped_prices, {})

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
                        listing_id: [
                            *(rule_by_id[rule_id] for rule_id in stored_rule_ids),
                            *buyer_rules_by_listing_id.get(listing_id, []),
                        ]
                        for listing_id, stored_rule_ids in zip(
                            rule_listing_ids, rule_ids_per_listing, strict=True
                        )
                    },
                )

            return PromotionRuleByIdLoader(context).load_many(rule_ids).then(with_rules)

        return (
            VariantChannelListingPromotionRuleByListingIdLoader(context)
            .load_many(rule_listing_ids)
            .then(with_listing_rules)
        )

    return Promise.all([scoped_prices_promise, buyer_rules_promise]).then(
        with_buyer_pricing
    )
