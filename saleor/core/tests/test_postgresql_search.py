import pytest
from django.contrib.postgres.search import SearchVector
from django.db.models import Value
from django.utils.text import slugify

from ...account.models import Address
from ...product.models import Product, ProductChannelListing
from ...product.search import search_products
from ...tests.utils import dummy_editorjs
from ..postgres import FlatConcat

PRODUCTS = [
    ("Arabica Coffee", "The best grains in galactic"),
    ("Cool T-Shirt", "Blue and big."),
    ("Roasted chicken", "Fabulous vertebrate"),
]


@pytest.fixture
def named_products(category, product_type, channel_USD):
    def gen_product(name, description):
        product = Product.objects.create(
            name=name,
            slug=slugify(name),
            description=dummy_editorjs(description),
            description_plaintext=description,
            product_type=product_type,
            category=category,
            search_document=f"{name}{description}",
            search_vector=(
                SearchVector(Value(name), weight="A")
                + SearchVector(Value(description), weight="C")
            ),
        )
        ProductChannelListing.objects.create(
            product=product,
            channel=channel_USD,
            is_published=True,
        )
        return product

    return [gen_product(name, desc) for name, desc in PRODUCTS]


def execute_search(phrase):
    """Execute storefront search."""
    qs = Product.objects.all()
    return search_products(qs, phrase)


@pytest.mark.parametrize(
    ("phrase", "product_num"),
    [("Arabica", 0), ("chicken", 2), ("blue", 1), ("roast", 2), ("cool", 1)],
)
@pytest.mark.integration
@pytest.mark.django_db
def test_storefront_product_fuzzy_name_search(named_products, phrase, product_num):
    results = execute_search(phrase)
    assert 1 == len(results)
    assert named_products[product_num] in results


USERS = [
    ("Andreas", "Knop", "adreas.knop@example.com"),
    ("Euzebiusz", "Ziemniak", "euzeb.potato@cebula.pl"),
    ("John", "Doe", "johndoe@example.com"),
]
ORDER_IDS = [10, 45, 13]
ORDERS = [[pk] + list(user) for pk, user in zip(ORDER_IDS, USERS)]


def gen_address_for_user(first_name, last_name):
    return Address.objects.create(
        first_name=first_name,
        last_name=last_name,
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="Wrocław",
        postal_code="53-601",
        country="PL",
    )


def test_combined_flat_search_vector():
    flat_vector_1 = FlatConcat(
        SearchVector(Value("value1"), weight="A"),
        SearchVector(Value("value2"), weight="C"),
    )
    flat_vector_2 = FlatConcat(
        SearchVector(Value("value3"), weight="A"),
        SearchVector(Value("value4"), weight="C"),
    )

    combined_flat_vector = flat_vector_1 + flat_vector_2
    assert combined_flat_vector.get_source_expressions() == [
        SearchVector(Value("value1"), weight="A"),
        SearchVector(Value("value2"), weight="C"),
        SearchVector(Value("value3"), weight="A"),
        SearchVector(Value("value4"), weight="C"),
    ]


def test_flat_concat_drop_exceeding_count_no_silently_fail():
    class LimitedFlatConcat(FlatConcat):
        max_expression_count = 2
        silent_drop_expression = False

    # Should not raise an exception and shouldn't truncate
    concat = LimitedFlatConcat(Value("1"), Value("2"))
    assert concat.source_expressions == [Value("1"), Value("2")]

    with pytest.raises(ValueError, match="Maximum expression count exceeded") as error:
        LimitedFlatConcat(Value("1"), Value("2"), Value("3"))

    assert error.value.args == ("Maximum expression count exceeded",)


def test_flat_concat_drop_exceeding_count_silently_truncate():
    class LimitedFlatConcat(FlatConcat):
        max_expression_count = 2
        silent_drop_expression = True

    # Should not raise an exception and shouldn't truncate
    concat = LimitedFlatConcat(Value("1"), Value("2"))
    assert concat.source_expressions == [Value("1"), Value("2")]

    concat = LimitedFlatConcat(Value("a"), Value("b"), Value("c"))
    assert concat.source_expressions == [Value("a"), Value("b")]
