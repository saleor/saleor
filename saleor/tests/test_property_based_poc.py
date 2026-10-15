"""Proof of concept: property-based tests with Hypothesis.

Each test states an invariant that must hold for every input, and Hypothesis
searches for a counterexample instead of us hand-picking a few examples.
"""

from decimal import Decimal

import pytest
from django.db import connection, transaction
from hypothesis import assume, example, given
from hypothesis import strategies as st
from prices import Money

from ..core.cleaners.urls import InvalidHostname, normalize_host
from ..core.prices import quantize_price
from ..core.search import parse_search_query
from ..core.utils.text import strip_accents
from ..discount import DiscountValueType
from ..discount.models import OrderDiscount
from ..discount.utils.manual_discount import split_manual_discount
from ..graphql.core.connection import from_global_cursor, to_global_cursor
from ..order.base_calculations import propagate_order_discount_on_order_lines_prices
from ..order.models import OrderLine
from ..payment.utils import price_from_minor_unit, price_to_minor_unit

CURRENCIES = ["USD", "EUR", "JPY", "KWD", "PLN"]

currencies = st.sampled_from(CURRENCIES)


def amounts(max_value="100000", min_value="0"):
    return st.decimals(
        min_value=Decimal(min_value),
        max_value=Decimal(max_value),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    )


@given(amount=amounts(), currency=currencies)
def test_minor_unit_round_trip(amount, currency):
    minor = price_to_minor_unit(amount, currency)

    assert price_from_minor_unit(minor, currency) == quantize_price(amount, currency)
    assert Decimal(minor) == Decimal(minor).to_integral_value()


@pytest.mark.xfail(
    strict=True,
    reason="Each half is rounded separately, so 1.00 + 1.00 shipping with 0.05 off "
    "is split 0.03 + 0.03 and the tax app gets 0.06 of discount.",
)
@given(
    subtotal=amounts(),
    shipping=amounts(),
    value_type=st.sampled_from([DiscountValueType.FIXED, DiscountValueType.PERCENTAGE]),
    value=amounts(max_value="100"),
)
@example(
    subtotal=Decimal("1.00"),
    shipping=Decimal("1.00"),
    value_type=DiscountValueType.FIXED,
    value=Decimal("0.05"),
)
def test_split_manual_discount_parts_sum_to_total_discount(
    subtotal, shipping, value_type, value
):
    currency = "USD"
    discount = OrderDiscount(value=value, value_type=value_type, currency=currency)
    subtotal_money = Money(subtotal, currency)
    shipping_money = Money(shipping, currency)
    total = subtotal_money + shipping_money
    if value_type == DiscountValueType.PERCENTAGE:
        expected_total_discount = quantize_price(total * value / 100, currency)
    else:
        expected_total_discount = min(Money(value, currency), total)

    subtotal_discount, shipping_discount = split_manual_discount(
        discount, subtotal_money, shipping_money
    )

    assert subtotal_discount + shipping_discount == expected_total_discount
    assert Money(0, currency) <= subtotal_discount <= subtotal_money
    assert Money(0, currency) <= shipping_discount <= shipping_money


line_strategy = st.tuples(
    amounts(max_value="1000"), st.integers(min_value=1, max_value=20)
)


@pytest.mark.xfail(
    strict=True,
    reason="Rounding drift lands on the last line. With 3 x 10.00 plus a free "
    "gift and 10.00 off, the gift line clamps at 0 and the lines sum to 20.01.",
)
@given(
    lines_data=st.lists(line_strategy, min_size=2, max_size=6),
    discount_amount=amounts(),
)
@example(
    lines_data=[(Decimal("10.00"), 1)] * 3 + [(Decimal("0.00"), 1)],
    discount_amount=Decimal("10.00"),
)
def test_order_discount_propagated_to_lines(lines_data, discount_amount):
    currency = "USD"
    lines = [
        OrderLine(
            pk=index,
            currency=currency,
            quantity=quantity,
            base_unit_price_amount=unit_price,
            undiscounted_base_unit_price_amount=unit_price,
        )
        for index, (unit_price, quantity) in enumerate(lines_data)
    ]
    base_subtotal = Money(
        sum((price * quantity for price, quantity in lines_data), Decimal(0)),
        currency,
    )
    assume(base_subtotal.amount > 0)
    subtotal_discount = min(Money(discount_amount, currency), base_subtotal)

    results = list(
        propagate_order_discount_on_order_lines_prices(
            lines, base_subtotal, subtotal_discount
        )
    )

    assert sum((total for _, total in results), Money(0, currency)) == (
        base_subtotal - subtotal_discount
    )
    for line, total in results:
        assert Money(0, currency) <= total <= line.base_unit_price * line.quantity


cursor_values = st.lists(
    st.one_of(st.none(), st.text(), st.integers(), st.decimals(allow_nan=False)),
    max_size=5,
)


@given(values=cursor_values)
def test_cursor_round_trip(values):
    cursor = to_global_cursor(values)

    assert from_global_cursor(cursor) == [
        None if value is None else str(value) for value in values
    ]


@given(host=st.from_regex(r"\A[a-zA-Z0-9.\-\[\]:]{1,40}\Z"))
def test_normalize_host_is_idempotent(host):
    try:
        normalized = normalize_host(host)
    except InvalidHostname:
        return

    assert normalize_host(normalized) == normalized


search_word = st.text(
    alphabet=st.one_of(
        st.characters(exclude_characters="\x00"),
        st.sampled_from("()&|!:<>'*\\-"),
    ),
    min_size=1,
    max_size=6,
)
search_term = st.one_of(
    search_word,
    search_word.map(lambda word: f"-{word}"),
    st.lists(search_word, min_size=1, max_size=3).map(
        lambda words: '"' + " ".join(words) + '"'
    ),
    st.just("OR"),
)
search_input = st.lists(search_term, max_size=6).map(" ".join)


@pytest.mark.xfail(
    strict=True,
    reason='A backslash at the end of a quoted phrase, e.g. "shirt\\", is passed '
    "through to the raw tsquery and Postgres raises a syntax error.",
)
@pytest.mark.django_db
@given(value=search_input)
@example(value='"shirt\\"')
def test_parse_search_query_produces_valid_tsquery(value):
    parsed = parse_search_query(strip_accents(value))
    assume(parsed is not None)

    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT to_tsquery('simple', %s)", [parsed])
