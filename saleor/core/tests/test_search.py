import pytest
from django.contrib.postgres.search import SearchVector
from django.db.models import Value

from ...account.models import User
from ...account.search import update_user_search_vector
from ...checkout.models import Checkout
from ...checkout.search.indexing import update_checkouts_search_vector
from ...product.models import Product, ProductChannelListing
from ..search import parse_search_query, prefix_search


def test_parse_search_query_single_word():
    assert parse_search_query("coffee") == "coffee:*"


def test_parse_search_query_multiple_words_implicit_and():
    assert parse_search_query("coffee shop") == "coffee:* & shop:*"


def test_parse_search_query_or_operator():
    assert parse_search_query("coffee OR tea") == "coffee:* | tea:*"


def test_parse_search_query_negation():
    assert parse_search_query("coffee -decaf") == "coffee:* & !decaf:*"


def test_parse_search_query_quoted_phrase():
    assert parse_search_query('"green tea"') == "(green <-> tea)"


def test_parse_search_query_quoted_phrase_with_other_terms():
    assert parse_search_query('coffee "green tea"') == "coffee:* & (green <-> tea)"


def test_parse_search_query_negated_quoted_phrase():
    assert parse_search_query('coffee -"green tea"') == "coffee:* & !(green <-> tea)"


def test_parse_search_query_or_with_negation():
    assert parse_search_query("coffee OR tea -decaf") == "coffee:* | tea:* & !decaf:*"


def test_parse_search_query_with_email():
    assert parse_search_query("user@example.com") == "user@example.com:*"


def test_parse_search_query_empty_string():
    assert parse_search_query("") is None


def test_parse_search_query_whitespace_normalization():
    assert parse_search_query("  multiple   spaces  ") == "multiple:* & spaces:*"


def test_parse_search_query_preserves_case():
    assert parse_search_query("Coffee SHOP") == "Coffee:* & SHOP:*"


def test_parse_search_query_single_word_in_quotes():
    # Single word in quotes should be an exact match (no prefix)
    assert parse_search_query('"coffee"') == "coffee"


def test_parse_search_query_quoted_word_with_or():
    assert parse_search_query('"aaron" OR aallen') == "aaron | aallen:*"


def test_parse_search_query_or_two_plain_words():
    assert parse_search_query("aaron0 OR aallen") == "aaron0:* | aallen:*"


def test_parse_search_query_or_between_phrases():
    assert (
        parse_search_query('"green tea" OR "black coffee"')
        == "(green <-> tea) | (black <-> coffee)"
    )


def test_parse_search_query_negated_word_with_or():
    assert parse_search_query("coffee OR tea -decaf -sugar") == (
        "coffee:* | tea:* & !decaf:* & !sugar:*"
    )


def test_parse_search_query_phrase_and_prefix_and_negation():
    assert parse_search_query('"green tea" maker -cheap') == (
        "(green <-> tea) & maker:* & !cheap:*"
    )


def test_parse_search_query_multiple_or_operators():
    assert parse_search_query("coffee OR tea OR juice") == (
        "coffee:* | tea:* | juice:*"
    )


def test_parse_search_query_or_with_negated_phrase():
    assert parse_search_query('coffee OR -"green tea"') == (
        "coffee:* | !(green <-> tea)"
    )


def test_parse_search_query_quoted_exact_and_prefix_mixed():
    assert parse_search_query('"exact" prefix') == "exact & prefix:*"


def test_parse_search_query_multiple_phrases_with_words():
    assert parse_search_query('"green tea" "black coffee" sugar') == (
        "(green <-> tea) & (black <-> coffee) & sugar:*"
    )


def test_parse_search_query_or_chain_with_phrase_in_middle():
    assert parse_search_query('coffee OR "green tea" OR juice') == (
        "coffee:* | (green <-> tea) | juice:*"
    )


def test_parse_search_query_negation_before_or():
    # Negation applies to decaf, then OR connects to tea
    assert parse_search_query("coffee -decaf OR tea") == ("coffee:* & !decaf:* | tea:*")


def test_parse_search_query_parentheses_are_stripped():
    # Parentheses are not supported for grouping; they are stripped as special chars
    assert parse_search_query("(green AND Tea) OR (coffee AND -black)") == (
        "green:* & Tea:* | coffee:* & !black:*"
    )


def test_parse_search_query_lowercase_or_is_regular_word():
    # Only uppercase OR is recognized as an operator
    assert parse_search_query("coffee or tea") == "coffee:* & or:* & tea:*"


def test_parse_search_query_lowercase_and_is_regular_word():
    assert parse_search_query("coffee and tea") == "coffee:* & and:* & tea:*"


def test_parse_search_query_mixed_case_or_is_regular_word():
    assert parse_search_query("coffee Or tea") == "coffee:* & Or:* & tea:*"


def test_parse_search_query_unclosed_quote():
    # Unclosed quote should still parse the words as a phrase
    assert parse_search_query('"green tea') == "(green <-> tea)"


@pytest.fixture
def products_for_search(category, product_type, channel_USD):
    products = []
    for name, description in [
        ("Coffee Maker", "Best coffee maker"),
        ("Coffeehouse Special", "Special blend for coffeehouses"),
        ("Tea Kettle", "Great for brewing tea"),
    ]:
        product = Product.objects.create(
            name=name,
            slug=name.lower().replace(" ", "-"),
            description_plaintext=description,
            product_type=product_type,
            category=category,
            search_vector=(
                SearchVector(Value(name), config="simple", weight="A")
                + SearchVector(Value(description), config="simple", weight="C")
            ),
        )
        ProductChannelListing.objects.create(
            product=product, channel=channel_USD, is_published=True
        )
        products.append(product)
    return products


@pytest.mark.django_db
def test_prefix_search_returns_prefix_matches(products_for_search):
    # given
    qs = Product.objects.all()

    # when
    results = prefix_search(qs, "coff")

    # then
    assert results.count() == 2
    names = {p.name for p in results}
    assert names == {"Coffee Maker", "Coffeehouse Special"}


@pytest.mark.django_db
def test_prefix_search_perfect_match_scores_higher(products_for_search):
    # given
    qs = Product.objects.all()

    # when
    results = list(prefix_search(qs, "coffee").order_by("-search_rank"))

    # then – "Coffee Maker" has exact word match, ranks above "Coffeehouse"
    assert len(results) == 2
    assert results[0].name == "Coffee Maker"


@pytest.mark.django_db
def test_prefix_search_empty_value_returns_all(products_for_search):
    # when
    results = prefix_search(Product.objects.all(), "")

    # then
    assert results.count() == 3


@pytest.mark.django_db
def test_prefix_search_no_matches(products_for_search):
    # when
    results = prefix_search(Product.objects.all(), "xyz")

    # then
    assert results.count() == 0


@pytest.mark.django_db
def test_prefix_search_case_insensitive(products_for_search):
    # when
    results = prefix_search(Product.objects.all(), "COFFEE")

    # then
    assert results.count() == 2


@pytest.mark.django_db
def test_prefix_search_multiple_terms_and(products_for_search):
    # when
    results = prefix_search(Product.objects.all(), "coffee mak")

    # then – only "Coffee Maker" matches both terms
    assert results.count() == 1
    assert results.first().name == "Coffee Maker"


@pytest.mark.django_db
def test_prefix_search_or_operator(products_for_search):
    # when
    results = prefix_search(Product.objects.all(), "coffee OR tea")

    # then – all three products match (Coffee Maker, Coffeehouse, Tea Kettle)
    assert results.count() == 3


@pytest.mark.django_db
def test_prefix_search_negation(products_for_search):
    # when
    results = prefix_search(Product.objects.all(), "coffee -special")

    # then – only "Coffee Maker" remains (Coffeehouse Special is excluded)
    assert results.count() == 1
    assert results.first().name == "Coffee Maker"


# --- prefix_search integration tests (Users) ---


@pytest.fixture
def users_for_search():
    users = []
    for email, first, last in [
        ("john.doe@example.com", "John", "Doe"),
        ("johnny.smith@example.com", "Johnny", "Smith"),
        ("jane.doe@example.com", "Jane", "Doe"),
    ]:
        user = User.objects.create(email=email, first_name=first, last_name=last)
        update_user_search_vector(user, attach_addresses_data=False)
        users.append(user)
    return users


@pytest.mark.django_db
def test_prefix_search_users(users_for_search):
    # when
    results = prefix_search(User.objects.all(), "joh")

    # then
    assert results.count() == 2
    emails = {u.email for u in results}
    assert emails == {"john.doe@example.com", "johnny.smith@example.com"}


@pytest.mark.django_db
def test_prefix_search_users_perfect_match_priority(users_for_search):
    # when
    results = list(prefix_search(User.objects.all(), "john").order_by("-search_rank"))

    # then – "John" exact match should rank higher than "Johnny"
    assert len(results) == 2
    assert results[0].first_name == "John"


def test_prefix_search_checkouts_exact_match_priority(
    channel_USD,
):
    # given

    checkouts = []

    # Checkout 1: email starts with "aaron00"
    checkout1 = Checkout.objects.create(
        channel=channel_USD,
        email="aaron00@example.net",
        user=None,
        currency="USD",
    )

    # Checkout 2: different email, user is "Aaron Smith" (exact match for "aaron")
    user2 = User.objects.create(
        email="smith.other@example.com", first_name="Aaron", last_name="Smith"
    )
    checkout2 = Checkout.objects.create(
        channel=channel_USD,
        email=user2.email,
        user=user2,
        currency="USD",
    )

    # Checkout 3: email contains "aaron" in middle, user is "Bob Wilson"
    # - not found as search uses prefix match
    user3 = User.objects.create(
        email="bob.wilson@example.com", first_name="Bob", last_name="Wilson"
    )
    checkout3 = Checkout.objects.create(
        channel=channel_USD,
        email=user3.email,
        user=user3,
        currency="USD",
    )

    # Checkout 4: user last name is "Aaron" (exact match), and email starts with `aaron`
    user4 = User.objects.create(
        email="aaron.thompson@example.com", first_name="Jane", last_name="Aaron"
    )
    checkout4 = Checkout.objects.create(
        channel=channel_USD,
        email=user4.email,
        user=user4,
        currency="USD",
    )

    # Checkout 5: no match at all
    user5 = User.objects.create(
        email="charlie.brown@example.com", first_name="Charlie", last_name="Brown"
    )
    checkout5 = Checkout.objects.create(
        channel=channel_USD,
        email=user5.email,
        user=user5,
        currency="USD",
    )

    checkouts = [checkout1, checkout2, checkout3, checkout4, checkout5]

    # Update search vectors
    update_checkouts_search_vector(checkouts)

    # when
    results = list(
        prefix_search(Checkout.objects.all(), "aaron").order_by("-search_rank")
    )

    # then
    expected_indexes = [3, 1, 0]
    assert len(results) == len(expected_indexes)
    for result, expected_index in zip(results, expected_indexes, strict=False):
        assert result.pk == checkouts[expected_index].pk
