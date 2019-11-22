from decimal import Decimal

import pytest
from django.urls import reverse
from prices import Money

from saleor.account.models import Address, User
from saleor.order.models import Order
from saleor.product.models import Product

PRODUCTS = [
    ("Arabica Coffee", "The best grains in galactic"),
    ("Cool T-Shirt", "Blue and big."),
    ("Roasted chicken", "Fabulous vertebrate"),
]


@pytest.fixture
def named_products(category, product_type):
    def gen_product(name, description):
        product = Product.objects.create(
            name=name,
            description=description,
            price=Money(Decimal(6.6), "USD"),
            product_type=product_type,
            category=category,
            is_published=True,
        )
        return product

    return [gen_product(name, desc) for name, desc in PRODUCTS]


def search_storefront(client, phrase):
    """Execute storefront search on client matching phrase."""
    resp = client.get(reverse("search:search"), {"q": phrase})
    return [prod for prod, _ in resp.context["results"].object_list]


@pytest.mark.parametrize(
    "phrase,product_num",
    [
        ("Arabika", 0),
        ("Aarabica", 0),
        ("Arab", 0),
        ("czicken", 2),
        ("blue", 1),
        ("roast", 2),
        ("coool", 1),
    ],
)
@pytest.mark.integration
@pytest.mark.django_db
def test_storefront_product_fuzzy_name_search(
    client, named_products, phrase, product_num
):
    results = search_storefront(client, phrase)
    assert 1 == len(results)
    assert named_products[product_num] in results


def unpublish_product(product):
    prod_to_unpublish = product
    prod_to_unpublish.is_published = False
    prod_to_unpublish.save()


@pytest.mark.integration
@pytest.mark.django_db
def test_storefront_filter_published_products(client, named_products):
    unpublish_product(named_products[0])
    assert search_storefront(client, "Coffee") == []


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


@pytest.fixture
def orders_with_addresses():
    orders = []
    for pk, name, lastname, email in ORDERS:
        addr = gen_address_for_user(name, lastname)
        user = User.objects.create(default_shipping_address=addr, email=email)
        order = Order.objects.create(user=user, billing_address=addr, pk=pk)
        orders.append(order)
    return orders


@pytest.fixture
def orders_with_user_names():
    orders = []
    for pk, first_name, last_name, email in ORDERS:
        user = User.objects.create(
            email=email, first_name=first_name, last_name=last_name
        )
        order = Order.objects.create(user=user, pk=pk)
        orders.append(order)
    return orders


@pytest.fixture
def users_with_addresses():
    users = []
    for firstname, lastname, email in USERS:
        addr = gen_address_for_user(firstname, lastname)
        user = User.objects.create(default_billing_address=addr, email=email)
        users.append(user)
    return users


@pytest.fixture
def users_with_names():
    users = []
    for firstname, lastname, email in USERS:
        user = User.objects.create(
            email=email, first_name=firstname, last_name=lastname
        )
        users.append(user)
    return users
