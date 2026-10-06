import datetime
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from django.conf import settings
from prices import Money

from ..account.models import CustomerType, User
from ..attribute.models import AssignedUserAttributeValue, AttributeCustomerType
from .models import (
    VariantChannelListingPrice,
    VariantChannelListingPriceAttributeValue,
    VariantChannelListingPriceCustomerType,
)


@dataclass(frozen=True)
class PricingBuyer:
    """The buyer facts a scoped price can be matched against.

    Only logged-in users have a buyer. `customer_type_id` is `None` when the
    default customer type is missing, in which case no type condition matches.
    `attribute_value_ids` holds only the values whose attribute is assigned to the
    buyer's customer type, so values persisted after an attribute was unassigned
    never grant a price.
    """

    customer_type_id: int | None
    attribute_value_ids: frozenset[int]


@dataclass(frozen=True)
class BuyerConditions:
    """The buyer conditions of a scoped price row or a promotion rule.

    Within a dimension one listed value is enough, across dimensions every
    declared one must match. A guest never matches a declared dimension.
    """

    customer_type_ids: frozenset[int]
    value_ids_by_attribute_id: Mapping[int, frozenset[int]]

    @property
    def has_buyer_conditions(self) -> bool:
        return bool(self.customer_type_ids or self.value_ids_by_attribute_id)

    def match_buyer(self, buyer: PricingBuyer | None) -> int | None:
        """Return how many buyer dimensions matched, or `None` on a mismatch."""
        score = 0
        if self.customer_type_ids:
            if buyer is None or buyer.customer_type_id not in self.customer_type_ids:
                return None
            score += 1
        for value_ids in self.value_ids_by_attribute_id.values():
            if buyer is None or not (value_ids & buyer.attribute_value_ids):
                return None
            score += 1
        return score


@dataclass(frozen=True)
class ScopedPriceRow(BuyerConditions):
    """A scoped price row with its conditions, detached from the ORM."""

    price: Money
    valid_from: datetime.datetime | None
    valid_to: datetime.datetime | None


def get_pricing_buyers(
    user_ids: Iterable[int],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> dict[int, PricingBuyer]:
    """Return the buyer facts of the users, keyed by user id.

    Unknown user ids are absent from the result. A user without a customer type
    is treated as a member of the default type. At most four queries are run for
    any number of users.
    """
    user_ids = list(user_ids)
    if not user_ids:
        return {}
    customer_type_id_by_user_id: dict[int, int | None] = dict(
        User.objects.using(database_connection_name)
        .filter(pk__in=user_ids)
        .values_list("pk", "customer_type_id")
    )
    if not customer_type_id_by_user_id:
        return {}
    if any(
        customer_type_id is None
        for customer_type_id in customer_type_id_by_user_id.values()
    ):
        default_customer_type_id = (
            CustomerType.objects.using(database_connection_name)
            .filter(is_default=True)
            .values_list("pk", flat=True)
            .first()
        )
        customer_type_id_by_user_id = {
            user_id: (
                customer_type_id
                if customer_type_id is not None
                else default_customer_type_id
            )
            for user_id, customer_type_id in customer_type_id_by_user_id.items()
        }
    customer_type_ids = {
        customer_type_id
        for customer_type_id in customer_type_id_by_user_id.values()
        if customer_type_id is not None
    }
    attribute_ids_by_customer_type_id: dict[int, set[int]] = defaultdict(set)
    assignments = (
        AttributeCustomerType.objects.using(database_connection_name)
        .filter(customer_type_id__in=customer_type_ids)
        .values_list("customer_type_id", "attribute_id")
    )
    for customer_type_id, attribute_id in assignments:
        attribute_ids_by_customer_type_id[customer_type_id].add(attribute_id)
    value_ids_by_user_id: dict[int, set[int]] = defaultdict(set)
    assigned_values = (
        AssignedUserAttributeValue.objects.using(database_connection_name)
        .filter(user_id__in=customer_type_id_by_user_id)
        .values_list("user_id", "value_id", "value__attribute_id")
    )
    for user_id, value_id, attribute_id in assigned_values:
        user_customer_type_id = customer_type_id_by_user_id[user_id]
        if (
            user_customer_type_id is not None
            and attribute_id in attribute_ids_by_customer_type_id[user_customer_type_id]
        ):
            value_ids_by_user_id[user_id].add(value_id)
    return {
        user_id: PricingBuyer(
            customer_type_id=customer_type_id,
            attribute_value_ids=frozenset(value_ids_by_user_id[user_id]),
        )
        for user_id, customer_type_id in customer_type_id_by_user_id.items()
    }


def get_scoped_price_rows(
    listing_ids: Iterable[int],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> dict[int, list[ScopedPriceRow]]:
    """Return the scoped price rows of the listings, keyed by listing id.

    Listings without rows are absent from the result. The condition tables are
    only queried when at least one row exists.
    """
    listing_ids = list(listing_ids)
    if not listing_ids:
        return {}
    rows = list(
        VariantChannelListingPrice.objects.using(database_connection_name)
        .filter(variant_channel_listing_id__in=listing_ids)
        .order_by("pk")
        .values_list(
            "pk",
            "variant_channel_listing_id",
            "price_amount",
            "currency",
            "valid_from",
            "valid_to",
        )
    )
    if not rows:
        return {}
    row_ids = [row[0] for row in rows]
    customer_type_ids_by_row_id: dict[int, set[int]] = defaultdict(set)
    type_conditions = (
        VariantChannelListingPriceCustomerType.objects.using(database_connection_name)
        .filter(listing_price_id__in=row_ids)
        .values_list("listing_price_id", "customer_type_id")
    )
    for row_id, customer_type_id in type_conditions:
        customer_type_ids_by_row_id[row_id].add(customer_type_id)
    value_ids_by_row_id: dict[int, dict[int, set[int]]] = defaultdict(
        lambda: defaultdict(set)
    )
    value_conditions = (
        VariantChannelListingPriceAttributeValue.objects.using(database_connection_name)
        .filter(listing_price_id__in=row_ids)
        .values_list("listing_price_id", "value__attribute_id", "value_id")
    )
    for row_id, attribute_id, value_id in value_conditions:
        value_ids_by_row_id[row_id][attribute_id].add(value_id)

    rows_by_listing_id: dict[int, list[ScopedPriceRow]] = defaultdict(list)
    for row_id, listing_id, price_amount, currency, valid_from, valid_to in rows:
        rows_by_listing_id[listing_id].append(
            ScopedPriceRow(
                price=Money(price_amount, currency),
                customer_type_ids=frozenset(customer_type_ids_by_row_id[row_id]),
                value_ids_by_attribute_id={
                    attribute_id: frozenset(value_ids)
                    for attribute_id, value_ids in value_ids_by_row_id[row_id].items()
                },
                valid_from=valid_from,
                valid_to=valid_to,
            )
        )
    return dict(rows_by_listing_id)


def _get_match_score(
    row: ScopedPriceRow, buyer: PricingBuyer | None, now: datetime.datetime
) -> int | None:
    """Return how many dimensions of the row matched, or `None` on a mismatch.

    Every dimension the row declares must match. The buyer dimensions follow
    `BuyerConditions.match_buyer`, the validity window counts as one more.
    """
    score = row.match_buyer(buyer)
    if score is None:
        return None
    if row.valid_from is not None or row.valid_to is not None:
        if row.valid_from is not None and now < row.valid_from:
            return None
        if row.valid_to is not None and now >= row.valid_to:
            return None
        score += 1
    return score


def resolve_scoped_price(
    rows: Iterable[ScopedPriceRow],
    buyer: PricingBuyer | None,
    now: datetime.datetime,
) -> Money | None:
    """Return the price of the best matching row, or `None` when none matches.

    The row that matched the most dimensions wins. Between rows with the same
    score the lowest price wins.
    """
    best_row: ScopedPriceRow | None = None
    best_score = -1
    for row in rows:
        score = _get_match_score(row, buyer, now)
        if score is None:
            continue
        if (
            best_row is None
            or score > best_score
            or (score == best_score and row.price < best_row.price)
        ):
            best_row = row
            best_score = score
    return best_row.price if best_row is not None else None


def get_scoped_prices(
    listing_ids: Iterable[int],
    user_id: int | None,
    now: datetime.datetime,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> dict[int, Money]:
    """Resolve the scoped price of every listing for the user.

    Listings without a matching row are absent from the result. The buyer is
    looked up only when a row has a buyer condition and the user is logged in.
    """
    rows_by_listing_id = get_scoped_price_rows(listing_ids, database_connection_name)
    if not rows_by_listing_id:
        return {}
    buyer = None
    if user_id is not None and any(
        row.has_buyer_conditions for rows in rows_by_listing_id.values() for row in rows
    ):
        buyer = get_pricing_buyers([user_id], database_connection_name).get(user_id)
    scoped_prices = {}
    for listing_id, rows in rows_by_listing_id.items():
        price = resolve_scoped_price(rows, buyer, now)
        if price is not None:
            scoped_prices[listing_id] = price
    return scoped_prices
