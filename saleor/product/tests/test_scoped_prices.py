import datetime
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from prices import Money

from ...attribute.models import AssignedUserAttributeValue, AttributeValue
from ...discount import RewardValueType
from ...discount.models import PromotionRule
from ..scoped_prices import (
    BuyerConditions,
    PricingBuyer,
    ScopedPriceRow,
    get_pricing_buyers,
    get_scoped_price_rows,
    get_scoped_prices,
    resolve_scoped_price,
)

NOW = datetime.datetime(2026, 9, 15, 12, tzinfo=datetime.UTC)
DAY = datetime.timedelta(days=1)
CURRENCY = "USD"

DEFAULT_TYPE_ID = 1
B2B_TYPE_ID = 2
LOYALTY_ATTRIBUTE_ID = 5
GOLD_VALUE_ID = 50
SILVER_VALUE_ID = 51
REGION_ATTRIBUTE_ID = 6
EU_VALUE_ID = 60

GUEST = None
DEFAULT_BUYER = PricingBuyer(
    customer_type_id=DEFAULT_TYPE_ID, attribute_value_ids=frozenset()
)
B2B_BUYER = PricingBuyer(customer_type_id=B2B_TYPE_ID, attribute_value_ids=frozenset())
GOLD_B2B_BUYER = PricingBuyer(
    customer_type_id=B2B_TYPE_ID, attribute_value_ids=frozenset({GOLD_VALUE_ID})
)
TYPELESS_BUYER = PricingBuyer(customer_type_id=None, attribute_value_ids=frozenset())


def row(
    amount,
    *,
    customer_type_ids=(),
    value_ids_by_attribute_id=None,
    valid_from=None,
    valid_to=None,
) -> ScopedPriceRow:
    return ScopedPriceRow(
        price=Money(Decimal(amount), CURRENCY),
        customer_type_ids=frozenset(customer_type_ids),
        value_ids_by_attribute_id={
            attribute_id: frozenset(value_ids)
            for attribute_id, value_ids in (value_ids_by_attribute_id or {}).items()
        },
        valid_from=valid_from,
        valid_to=valid_to,
    )


@pytest.mark.parametrize(
    ("_case", "rows", "buyer", "expected_amount"),
    [
        ("no_rows", [], B2B_BUYER, None),
        (
            "no_match_returns_none",
            [row(8, customer_type_ids=[B2B_TYPE_ID])],
            DEFAULT_BUYER,
            None,
        ),
        (
            "guest_never_matches_a_type_row_even_for_the_default_type",
            [row(8, customer_type_ids=[DEFAULT_TYPE_ID])],
            GUEST,
            None,
        ),
        (
            "guest_never_matches_a_value_row",
            [row(7, value_ids_by_attribute_id={LOYALTY_ATTRIBUTE_ID: [GOLD_VALUE_ID]})],
            GUEST,
            None,
        ),
        (
            "guest_matches_a_window_row",
            [row(9, valid_from=NOW - DAY, valid_to=NOW + DAY)],
            GUEST,
            9,
        ),
        (
            "buyer_without_a_type_never_matches_a_type_row",
            [row(8, customer_type_ids=[B2B_TYPE_ID])],
            TYPELESS_BUYER,
            None,
        ),
        (
            "type_matches_when_in_the_listed_set",
            [row(8, customer_type_ids=[DEFAULT_TYPE_ID, B2B_TYPE_ID])],
            B2B_BUYER,
            8,
        ),
        (
            "value_matches_when_one_listed_value_is_held",
            [
                row(
                    7,
                    value_ids_by_attribute_id={
                        LOYALTY_ATTRIBUTE_ID: [GOLD_VALUE_ID, SILVER_VALUE_ID]
                    },
                )
            ],
            GOLD_B2B_BUYER,
            7,
        ),
        (
            "value_not_held",
            [
                row(
                    7,
                    value_ids_by_attribute_id={LOYALTY_ATTRIBUTE_ID: [SILVER_VALUE_ID]},
                )
            ],
            GOLD_B2B_BUYER,
            None,
        ),
        (
            "every_declared_dimension_must_match",
            [
                row(
                    6,
                    customer_type_ids=[B2B_TYPE_ID],
                    value_ids_by_attribute_id={
                        LOYALTY_ATTRIBUTE_ID: [GOLD_VALUE_ID],
                        REGION_ATTRIBUTE_ID: [EU_VALUE_ID],
                    },
                )
            ],
            GOLD_B2B_BUYER,
            None,
        ),
        (
            "type_and_value_matched_together",
            [
                row(
                    6,
                    customer_type_ids=[B2B_TYPE_ID],
                    value_ids_by_attribute_id={LOYALTY_ATTRIBUTE_ID: [GOLD_VALUE_ID]},
                )
            ],
            GOLD_B2B_BUYER,
            6,
        ),
        (
            "more_matched_dimensions_beat_a_lower_price",
            [
                row(5, customer_type_ids=[B2B_TYPE_ID]),
                row(
                    6,
                    customer_type_ids=[B2B_TYPE_ID],
                    value_ids_by_attribute_id={LOYALTY_ATTRIBUTE_ID: [GOLD_VALUE_ID]},
                ),
            ],
            GOLD_B2B_BUYER,
            6,
        ),
        (
            "window_counts_as_a_matched_dimension",
            [
                row(5, customer_type_ids=[B2B_TYPE_ID]),
                row(
                    6,
                    customer_type_ids=[B2B_TYPE_ID],
                    valid_from=NOW - DAY,
                    valid_to=NOW + DAY,
                ),
            ],
            B2B_BUYER,
            6,
        ),
        (
            "tie_goes_to_the_lowest_price",
            [
                row(8, customer_type_ids=[B2B_TYPE_ID]),
                row(7, customer_type_ids=[B2B_TYPE_ID]),
                row(9, customer_type_ids=[B2B_TYPE_ID]),
            ],
            B2B_BUYER,
            7,
        ),
        (
            "an_unmatched_row_does_not_block_a_matched_one",
            [
                row(1, customer_type_ids=[DEFAULT_TYPE_ID]),
                row(8, customer_type_ids=[B2B_TYPE_ID]),
            ],
            B2B_BUYER,
            8,
        ),
        ("window_start_is_inclusive", [row(9, valid_from=NOW)], GUEST, 9),
        ("window_end_is_exclusive", [row(9, valid_to=NOW)], GUEST, None),
        ("window_not_started", [row(9, valid_from=NOW + DAY)], GUEST, None),
        ("window_ended", [row(9, valid_to=NOW - DAY)], GUEST, None),
        ("open_ended_window_matches", [row(9, valid_from=NOW - DAY)], GUEST, 9),
        ("unconditioned_row_matches_everyone", [row(9)], GUEST, 9),
        (
            "unconditioned_row_loses_to_any_matched_condition",
            [row(1), row(8, customer_type_ids=[B2B_TYPE_ID])],
            B2B_BUYER,
            8,
        ),
    ],
)
def test_resolve_scoped_price(_case, rows, buyer, expected_amount):
    # when
    price = resolve_scoped_price(rows, buyer, NOW)

    # then
    expected = Money(Decimal(expected_amount), CURRENCY) if expected_amount else None
    assert price == expected


def test_get_scoped_price_rows_without_listing_ids_runs_no_query(
    django_assert_num_queries,
):
    # when
    with django_assert_num_queries(0):
        rows_by_listing_id = get_scoped_price_rows([])

    # then
    assert rows_by_listing_id == {}


def test_get_scoped_price_rows_without_rows_runs_one_query(
    variant, django_assert_num_queries
):
    # given
    listing = variant.channel_listings.get()

    # when
    with django_assert_num_queries(1):
        rows_by_listing_id = get_scoped_price_rows([listing.pk])

    # then
    assert rows_by_listing_id == {}


def test_get_scoped_price_rows(
    variant,
    variant_channel_listing_price,
    variant_channel_listing_price_for_customer_type,
    variant_channel_listing_price_for_attribute_value,
    customer_type,
    loyalty_customer_attribute,
    django_assert_num_queries,
):
    # given
    listing = variant.channel_listings.get()
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )

    # when
    with django_assert_num_queries(3):
        rows_by_listing_id = get_scoped_price_rows([listing.pk])

    # then
    window_row = variant_channel_listing_price
    assert rows_by_listing_id == {
        listing.pk: [
            ScopedPriceRow(
                price=window_row.price,
                customer_type_ids=frozenset(),
                value_ids_by_attribute_id={},
                valid_from=window_row.valid_from,
                valid_to=window_row.valid_to,
            ),
            ScopedPriceRow(
                price=variant_channel_listing_price_for_customer_type.price,
                customer_type_ids=frozenset({customer_type.pk}),
                value_ids_by_attribute_id={},
                valid_from=None,
                valid_to=None,
            ),
            ScopedPriceRow(
                price=variant_channel_listing_price_for_attribute_value.price,
                customer_type_ids=frozenset(),
                value_ids_by_attribute_id={
                    loyalty_customer_attribute.pk: frozenset({gold_value.pk})
                },
                valid_from=None,
                valid_to=None,
            ),
        ]
    }


def test_get_pricing_buyers_for_unknown_user():
    # when
    buyers = get_pricing_buyers([-1])

    # then
    assert buyers == {}


def test_get_pricing_buyers_treats_missing_type_as_default(
    customer_user, default_customer_type
):
    # given
    customer_user.customer_type = None
    customer_user.save(update_fields=["customer_type"])

    # when
    buyers = get_pricing_buyers([customer_user.pk])

    # then
    assert buyers == {
        customer_user.pk: PricingBuyer(
            customer_type_id=default_customer_type.pk,
            attribute_value_ids=frozenset(),
        )
    }


def test_get_pricing_buyers_includes_only_values_of_attributes_assigned_to_the_type(
    gold_customer_user,
    customer_type,
    loyalty_customer_attribute,
    segment_customer_attribute,
):
    # given
    # the segment attribute is not assigned to the B2B type, so its value is hidden
    retail_value = AttributeValue.objects.get(
        attribute=segment_customer_attribute, slug="retail"
    )
    AssignedUserAttributeValue.objects.create(
        user=gold_customer_user, value=retail_value
    )
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )

    # when
    buyers = get_pricing_buyers([gold_customer_user.pk])

    # then
    assert buyers == {
        gold_customer_user.pk: PricingBuyer(
            customer_type_id=customer_type.pk,
            attribute_value_ids=frozenset({gold_value.pk}),
        )
    }


def test_get_pricing_buyers_includes_values_of_attributes_hidden_in_storefront(
    b2b_customer_user, customer_type, hidden_customer_attribute
):
    # given
    assert hidden_customer_attribute.visible_in_storefront is False
    customer_type.customer_attributes.add(hidden_customer_attribute)
    high_value = AttributeValue.objects.create(
        attribute=hidden_customer_attribute, name="High", slug="high"
    )
    AssignedUserAttributeValue.objects.create(user=b2b_customer_user, value=high_value)

    # when
    buyers = get_pricing_buyers([b2b_customer_user.pk])

    # then
    assert buyers == {
        b2b_customer_user.pk: PricingBuyer(
            customer_type_id=customer_type.pk,
            attribute_value_ids=frozenset({high_value.pk}),
        )
    }


def test_get_pricing_buyers_runs_at_most_four_queries_for_many_users(
    gold_customer_user, customer_user2, django_assert_num_queries
):
    # given
    # a user without a type forces the default type lookup, the fourth query
    customer_user2.customer_type = None
    customer_user2.save(update_fields=["customer_type"])

    # when
    with django_assert_num_queries(4):
        buyers = get_pricing_buyers([gold_customer_user.pk, customer_user2.pk])

    # then
    assert set(buyers) == {gold_customer_user.pk, customer_user2.pk}


def test_get_scoped_prices_skips_the_buyer_lookup_without_buyer_conditions(
    variant, variant_channel_listing_price, customer_user
):
    # given
    listing = variant.channel_listings.get()

    # when
    with CaptureQueriesContext(connection) as context:
        scoped_prices = get_scoped_prices(
            [listing.pk], customer_user.pk, variant_channel_listing_price.valid_from
        )

    # then
    assert scoped_prices == {listing.pk: variant_channel_listing_price.price}
    assert not [
        query for query in context.captured_queries if "account_user" in query["sql"]
    ]


def test_get_scoped_prices_ignores_buyer_rows_for_a_guest(
    variant, variant_channel_listing_price_for_customer_type
):
    # given
    listing = variant.channel_listings.get()

    # when
    scoped_prices = get_scoped_prices([listing.pk], None, NOW)

    # then
    assert scoped_prices == {}


def test_get_scoped_prices_for_a_member_of_the_type(
    variant, variant_channel_listing_price_for_customer_type, b2b_customer_user
):
    # given
    listing = variant.channel_listings.get()

    # when
    scoped_prices = get_scoped_prices([listing.pk], b2b_customer_user.pk, NOW)

    # then
    assert scoped_prices == {
        listing.pk: variant_channel_listing_price_for_customer_type.price
    }


@pytest.mark.parametrize(
    ("_case", "price_override", "scoped_amount", "expected_amount"),
    [
        ("listing_price_by_default", None, None, 10),
        ("scoped_price_beats_listing_price", None, 8, 8),
        ("custom_price_beats_scoped_price", Decimal(12), 8, 12),
    ],
)
def test_get_base_price_precedence(
    _case, price_override, scoped_amount, expected_amount, variant
):
    # given
    listing = variant.channel_listings.get()
    assert listing.price_amount == Decimal(10)
    scoped_price = Money(Decimal(scoped_amount), CURRENCY) if scoped_amount else None

    # when
    price = variant.get_base_price(listing, price_override, scoped_price)

    # then
    assert price == Money(Decimal(expected_amount), CURRENCY)


def test_get_price_without_scoped_price_returns_the_stored_discounted_price(variant):
    # given
    listing = variant.channel_listings.get()
    listing.discounted_price_amount = Decimal(6)
    listing.save(update_fields=["discounted_price_amount"])

    # when
    price = variant.get_price(listing)

    # then
    assert price == Money(Decimal(6), CURRENCY)


@pytest.mark.parametrize(
    ("_case", "reward_value_type", "reward_value", "expected_amount"),
    [
        (
            "percentage_rule_scales_with_the_scoped_price",
            RewardValueType.PERCENTAGE,
            10,
            "7.20",
        ),
        ("fixed_rule_subtracts_from_the_scoped_price", RewardValueType.FIXED, 5, 3),
    ],
)
def test_get_price_reapplies_promotion_rules_on_the_scoped_price(
    _case,
    reward_value_type,
    reward_value,
    expected_amount,
    variant,
    catalogue_promotion_without_rules,
):
    # given
    listing = variant.channel_listings.get()
    rule = PromotionRule.objects.create(
        promotion=catalogue_promotion_without_rules,
        reward_value_type=reward_value_type,
        reward_value=Decimal(reward_value),
    )
    scoped_price = Money(Decimal(8), CURRENCY)

    # when
    price = variant.get_price(
        listing, promotion_rules=[rule], scoped_price=scoped_price
    )

    # then
    assert price == Money(Decimal(expected_amount), CURRENCY)


def test_get_price_with_scoped_price_and_no_rules_returns_the_scoped_price(variant):
    # given
    listing = variant.channel_listings.get()
    listing.discounted_price_amount = Decimal(6)
    listing.save(update_fields=["discounted_price_amount"])
    scoped_price = Money(Decimal(8), CURRENCY)

    # when
    price = variant.get_price(listing, scoped_price=scoped_price)

    # then
    assert price == scoped_price


@pytest.mark.parametrize(
    ("_case", "conditions", "buyer", "expected_score"),
    [
        (
            "no_conditions_match_everyone_with_no_score",
            BuyerConditions(frozenset(), {}),
            GUEST,
            0,
        ),
        (
            "type_in_the_set_scores_one",
            BuyerConditions(frozenset({B2B_TYPE_ID, DEFAULT_TYPE_ID}), {}),
            B2B_BUYER,
            1,
        ),
        (
            "type_outside_the_set_mismatches",
            BuyerConditions(frozenset({B2B_TYPE_ID}), {}),
            DEFAULT_BUYER,
            None,
        ),
        (
            "guest_never_matches_a_type_condition",
            BuyerConditions(frozenset({DEFAULT_TYPE_ID}), {}),
            GUEST,
            None,
        ),
        (
            "one_value_per_attribute_is_enough",
            BuyerConditions(
                frozenset(),
                {LOYALTY_ATTRIBUTE_ID: frozenset({GOLD_VALUE_ID, SILVER_VALUE_ID})},
            ),
            GOLD_B2B_BUYER,
            1,
        ),
        (
            "every_attribute_must_match",
            BuyerConditions(
                frozenset(),
                {
                    LOYALTY_ATTRIBUTE_ID: frozenset({GOLD_VALUE_ID}),
                    REGION_ATTRIBUTE_ID: frozenset({EU_VALUE_ID}),
                },
            ),
            GOLD_B2B_BUYER,
            None,
        ),
        (
            "type_and_value_score_two",
            BuyerConditions(
                frozenset({B2B_TYPE_ID}),
                {LOYALTY_ATTRIBUTE_ID: frozenset({GOLD_VALUE_ID})},
            ),
            GOLD_B2B_BUYER,
            2,
        ),
    ],
)
def test_buyer_conditions_match_buyer(_case, conditions, buyer, expected_score):
    # when
    score = conditions.match_buyer(buyer)

    # then
    assert score == expected_score
