from decimal import Decimal

import pytest
from django.urls import reverse

from saleor.account.models import Address, User
from saleor.order.models import Order
from saleor.product.models import Product


@pytest.fixture(scope='function', autouse=True)
def postgresql_search_enabled(settings):
    settings.ENABLE_SEARCH = True
    settings.SEARCH_BACKEND = 'saleor.search.backends.postgresql'


PRODUCTS = [('Arabica Coffee', 'The best grains in galactic'),
            ('Cool T-Shirt', 'Blue and big.'),
            ('Roasted chicken', 'Fabulous vertebrate')]


@pytest.fixture
def named_products(default_category, product_type):
    def gen_product(name, description):
        product = Product.objects.create(
            name=name,
            description=description,
            price=Decimal(6.6),
            product_type=product_type,
            category=default_category)
        return product
    return [gen_product(name, desc) for name, desc in PRODUCTS]


def search_storefront(client, phrase):
    """Execute storefront search on client matching phrase."""
    resp = client.get(reverse('search:search'), {'q': phrase})
    return [prod for prod, _ in resp.context['results'].object_list]


@pytest.mark.parametrize('phrase,product_num',
                         [('Arabika', 0), ('Aarabica', 0), ('Arab', 0),
                          ('czicken', 2), ('blue', 1), ('roast', 2),
                          ('coool', 1)])
@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_storefront_product_fuzzy_name_search(client, named_products, phrase,
                                              product_num):
    results = search_storefront(client, phrase)
    assert 1 == len(results)
    assert named_products[product_num] in results


def unpublish_product(product):
    prod_to_unpublish = product
    prod_to_unpublish.is_published = False
    prod_to_unpublish.save()


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_storefront_filter_published_products(client, named_products):
    unpublish_product(named_products[0])
    assert search_storefront(client, 'Coffee') == []


def search_dashboard(client, phrase):
    """Execute dashboard search on client matching phrase."""
    response = client.get(reverse('dashboard:search'), {'q': phrase})
    assert response.context['query'] in phrase
    context = response.context
    return context['products'], context['orders'], context['users']


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_dashboard_search_with_empty_results(admin_client, named_products):
    products, orders, users = search_dashboard(admin_client, 'foo')
    assert 0 == len(products) == len(orders) == len(users)


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('phrase,product_num', [('  coffee. ', 0),
                                                ('shirt', 1), ('ROASTED', 2)])
def test_find_product_by_name(admin_client, named_products, phrase,
                              product_num):
    products, _, _ = search_dashboard(admin_client, phrase)
    assert 1 == len(products)
    assert named_products[product_num] in products


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('phrase,product_num', [('BIG', 1), (' grains, ', 0),
                                                ('fabulous', 2)])
def test_find_product_by_description(admin_client, named_products, phrase,
                                     product_num):
    products, _, _ = search_dashboard(admin_client, phrase)
    assert 1 == len(products)
    assert named_products[product_num] in products


USERS = [('Andreas', 'Knop', 'adreas.knop@example.com'),
         ('Euzebiusz', 'Ziemniak', 'euzeb.potato@cebula.pl'),
         ('John', 'Doe', 'johndoe@example.com')]
ORDER_IDS = [10, 45, 13]
ORDERS = [[pk] + list(user) for pk, user in zip(ORDER_IDS, USERS)]


def gen_address_for_user(first_name, last_name):
    return Address.objects.create(
        first_name=first_name,
        last_name=last_name,
        company_name='Mirumee Software',
        street_address_1='Tęczowa 7',
        city='Wrocław',
        postal_code='53-601',
        country='PL')


@pytest.fixture
def orders_with_addresses():
    orders = []
    for pk, name, lastname, email in ORDERS:
        addr = gen_address_for_user(name, lastname)
        user = User.objects.create(default_shipping_address=addr, email=email)
        order = Order.objects.create(user=user, billing_address=addr, pk=pk)
        orders.append(order)
    return orders


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_find_order_by_id_with_no_result(admin_client, orders_with_addresses):
    phrase = '991'  # not existing id
    _, orders, _ = search_dashboard(admin_client, phrase)
    assert 0 == len(orders)


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_find_order_by_id(admin_client, orders_with_addresses):
    phrase = ' 10 '
    _, orders, _ = search_dashboard(admin_client, phrase)
    assert 1 == len(orders)
    assert orders_with_addresses[0] in orders


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('phrase,order_num', [('euzeb.potato@cebula.pl', 1),
                                              ('  johndoe@example.com ', 2)])
def test_find_order_with_email(admin_client, orders_with_addresses, phrase,
                               order_num):
    _, orders, _ = search_dashboard(admin_client, phrase)
    assert 1 == len(orders)
    assert orders_with_addresses[order_num] in orders


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('phrase,order_num', [('knop', 0), ('ZIEMniak', 1),
                                              ('  john  ', 2), ('ANDREAS', 0)])
def test_find_order_with_user_name(admin_client, orders_with_addresses, phrase,
                                   order_num):
    _, orders, _ = search_dashboard(admin_client, phrase)
    assert 1 == len(orders)
    assert orders_with_addresses[order_num] in orders


ORDER_PHRASE_WITH_RESULT = 'Andreas'
ORDER_RESULTS_PERMISSION = 'order.manage_orders'


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_orders_search_results_restricted_to_users_with_permission(
        orders_with_addresses, staff_client, staff_user):
    assert not staff_user.has_perm(ORDER_RESULTS_PERMISSION)
    _, orders, _ = search_dashboard(staff_client, ORDER_PHRASE_WITH_RESULT)
    assert 0 == len(orders)


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_show_orders_search_result_to_user_with_permission_granted(
        orders_with_addresses, staff_client, staff_user,
        permission_manage_orders):
    assert not staff_user.has_perm(ORDER_RESULTS_PERMISSION)
    staff_user.user_permissions.add(permission_manage_orders)
    _, orders, _ = search_dashboard(staff_client, ORDER_PHRASE_WITH_RESULT)
    assert 1 == len(orders)


@pytest.fixture
def users_with_addresses():
    users = []
    for firstname, lastname, email in USERS:
        addr = gen_address_for_user(firstname, lastname)
        user = User.objects.create(default_billing_address=addr, email=email)
        users.append(user)
    return users


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('phrase,user_num', [('adreas.knop@example.com', 0),
                                             (' euzeb.potato@cebula.pl ', 1)])
def test_find_user_by_email(admin_client, users_with_addresses, phrase,
                            user_num):
    _, _, users = search_dashboard(admin_client, phrase)
    assert 1 == len(users)
    assert users_with_addresses[user_num] in users


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('phrase,user_num', [('Andreas Knop', 0),
                                             (' Euzebiusz ', 1), ('DOE', 2)])
def test_find_user_by_name(admin_client, users_with_addresses, phrase,
                           user_num):
    _, _, users = search_dashboard(admin_client, phrase)
    assert 1 == len(users)
    assert users_with_addresses[user_num] in users


USER_PHRASE_WITH_RESULT = 'adreas.knop@example.com'
USER_RESULTS_PERMISSION = 'account.manage_users'


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_users_search_results_restricted_to_staff_with_permission(
        users_with_addresses, staff_client, staff_user):
    assert not staff_user.has_perm(USER_RESULTS_PERMISSION)
    _, _, users = search_dashboard(staff_client, USER_PHRASE_WITH_RESULT)
    assert 0 == len(users)


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_show_users_search_result_when_access_granted(
        users_with_addresses, staff_client, staff_user,
        permission_manage_users):
    assert not staff_user.has_perm(USER_RESULTS_PERMISSION)
    staff_user.user_permissions.add(permission_manage_users)
    _, _, users = search_dashboard(staff_client, USER_PHRASE_WITH_RESULT)
    assert 1 == len(users)
