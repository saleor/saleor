import pytest
from django.contrib.postgres.search import SearchVector
from django.db.models import Value

from ...account.models import User
from ...account.search import update_user_search_vector
from ...product.models import Product, ProductChannelListing
from ..search import parse_search_query, prefix_search

# --- parse_search_query unit tests ---


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


def test_parse_search_query_special_characters_stripped():
    assert parse_search_query("user@example.com") == "userexamplecom:*"


def test_parse_search_query_empty_string():
    assert parse_search_query("") is None


def test_parse_search_query_only_special_characters():
    assert parse_search_query("!@#$%") is None


def test_parse_search_query_whitespace_normalization():
    assert parse_search_query("  multiple   spaces  ") == "multiple:* & spaces:*"


def test_parse_search_query_preserves_case():
    assert parse_search_query("Coffee SHOP") == "Coffee:* & SHOP:*"


def test_parse_search_query_single_word_in_quotes():
    # Single word phrase should be treated as a prefix word
    assert parse_search_query('"coffee"') == "coffee:*"


def test_parse_search_query_unclosed_quote():
    # Unclosed quote should still parse the words as a phrase
    assert parse_search_query('"green tea') == "(green <-> tea)"


def test_parse_search_query_standalone_dash_ignored():
    # Standalone dash (space before and after) is ignored
    assert parse_search_query("coffee - tea") == "coffee:* & tea:*"


# --- prefix_search integration tests (Products) ---


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
                SearchVector(Value(name), weight="A")
                + SearchVector(Value(description), weight="C")
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
