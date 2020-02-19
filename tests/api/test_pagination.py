import pytest
from decimal import Decimal

from django.contrib.auth import models as auth_models
from django.db.models import Count, FilteredRelation, Max, Q
from django.utils import timezone

from saleor.graphql.core.connection import to_global_cursor, get_field_value
from saleor.account.models import Address, User, ServiceAccount
from saleor.checkout.models import Checkout
from saleor.discount import DiscountValueType
from saleor.discount.models import Sale, Voucher
from saleor.menu.models import Menu, MenuItem
from saleor.order import OrderStatus
from saleor.order.models import Order
from saleor.page.models import Page
from tests.api.utils import get_graphql_content


@pytest.fixture
def users_for_pagination():
    User.objects.bulk_create(
        [
            User(
                first_name="Lily",
                last_name="Allen",
                email="allen@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Bob",
                last_name="Dylan",
                email="zordon@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Clark",
                last_name="Kent",
                email="leslie@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Danny",
                last_name="DeVito",
                email="ddevito@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Ellen",
                last_name="Degeneres",
                email="ellen@example.com",
                is_staff=False,
                is_active=True,
            ),
        ]
    )


@pytest.fixture
def groups_for_pagination():
    auth_models.Group.objects.bulk_create(
        [
            auth_models.Group(name="Group5",),
            auth_models.Group(name="Group3",),
            auth_models.Group(name="A group",),
            auth_models.Group(name="Agroup",),
            auth_models.Group(name="Something",),
        ]
    )


@pytest.fixture
def service_accounts_for_pagination():
    ServiceAccount.objects.bulk_create(
        [
            ServiceAccount(name="ServiceAccount",),
            ServiceAccount(name="Service Account",),
            ServiceAccount(name="A Service Account",),
            ServiceAccount(name="The Service Account",),
            ServiceAccount(name="Example Service Account",),
        ]
    )


@pytest.fixture
def checkouts_for_pagination():
    Checkout.objects.bulk_create(
        [
            Checkout(token="1fa91751-fd0a-45ca-8633-4bac9f5cb2a7",),
            Checkout(token="63256386-a913-4dea-bee9-40c3f1faf952",),
            Checkout(token="31ad7bf3-2e0d-435d-aa8c-c23abaf6a934",),
            Checkout(token="308a080e-29e1-4eab-b856-148b925409c1",),
            Checkout(token="3e6140c5-5784-4965-8dc0-4d5ee4b9409a",),
        ]
    )


@pytest.fixture
def sales_for_pagination():
    timezone_now = timezone.now()
    Sale.objects.bulk_create(
        [
            Sale(
                name="A Sale",
                end_date=timezone_now + timezone.timedelta(hours=4),
                type=DiscountValueType.PERCENTAGE,
                value=Decimal("1"),
            ),
            Sale(
                name="The Sale",
                end_date=timezone_now + timezone.timedelta(hours=1),
                value=Decimal("7"),
            ),
            Sale(
                name="Example Sale",
                end_date=timezone_now + timezone.timedelta(hours=2),
                type=DiscountValueType.PERCENTAGE,
                value=Decimal("5"),
            ),
            Sale(
                name="Sale example",
                end_date=timezone_now + timezone.timedelta(hours=1),
                value=Decimal("5"),
            ),
            Sale(
                name="An example sale",
                end_date=timezone_now + timezone.timedelta(hours=5),
            ),
        ]
    )


@pytest.fixture
def voucher_for_pagination():
    timezone_now = timezone.now()
    Voucher.objects.bulk_create(
        [
            Voucher(
                code="code",
                name="A voucher",
                end_date=timezone_now + timezone.timedelta(hours=4),
                type=DiscountValueType.PERCENTAGE,
                discount_value=Decimal("1"),
                min_spent_amount=Decimal("10"),
                usage_limit=10,
            ),
            Voucher(
                code="The-code",
                name="A voucher",
                end_date=timezone_now + timezone.timedelta(hours=1),
                discount_value=Decimal("7"),
                min_spent_amount=Decimal("10"),
                usage_limit=1000,
            ),
            Voucher(
                code="Example-code",
                name="A voucher",
                end_date=timezone_now + timezone.timedelta(hours=2),
                type=DiscountValueType.PERCENTAGE,
                discount_value=Decimal("5"),
                min_spent_amount=Decimal("120"),
                usage_limit=100,
            ),
            Voucher(
                code="Voucher-ex",
                name="A voucher",
                end_date=timezone_now + timezone.timedelta(hours=1),
                discount_value=Decimal("5"),
                min_spent_amount=Decimal("50"),
                usage_limit=100,
            ),
            Voucher(
                code="An-example-v",
                name="A voucher",
                end_date=timezone_now + timezone.timedelta(hours=5),
                discount_value=Decimal("2"),
                min_spent_amount=Decimal("100"),
                usage_limit=10,
            ),
        ]
    )


@pytest.fixture
def menus_for_pagination():
    Menu.objects.bulk_create(
        [
            Menu(
                name="The menu",
                json_content={},
            ),
            Menu(
                name="The example menu",
                json_content={},
            ),
            Menu(
                name="Just menu",
                json_content={},
            ),
        ]
    )
    menu1 = Menu.objects.filter(name="The menu").first()
    menu2 = Menu.objects.filter(name="The example menu").first()
    menu3 = Menu.objects.filter(name="Just menu").first()
    MenuItem.objects.create(name="MenuItem1", menu=menu1)
    MenuItem.objects.create(name="MenuItem2", menu=menu1)
    MenuItem.objects.create(name="MenuItem3", menu=menu2)
    MenuItem.objects.create(name="MenuItem4", menu=menu2)
    MenuItem.objects.create(name="MenuItem5", menu=menu2)
    MenuItem.objects.create(name="MenuItem6", menu=menu3)
    MenuItem.objects.create(name="MenuItem7", menu=menu3)
    MenuItem.objects.create(name="MenuItem8", menu=menu3)
    MenuItem.objects.create(name="MenuItem9", menu=menu3)


@pytest.fixture
def orders_for_pagination(customer_user):
    address1 = Address.objects.create(
        first_name="Lily",
        last_name="Allen",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
    )
    address2 = Address.objects.create(
        first_name="Bob",
        last_name="Dylan",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
    )
    address3 = Address.objects.create(
        first_name="Clark",
        last_name="Kent",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
    )
    address4 = Address.objects.create(
        first_name="Danny",
        last_name="DeVito",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
    )
    address5 = Address.objects.create(
        first_name="Ellen",
        last_name="Degeneres",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
    )

    Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                token="order_token_1",
                total_gross_amount=Decimal("10"),
                billing_address=address1
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                token="order_token_2",
                total_gross_amount=Decimal("20"),
                billing_address=address2
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                token="order_token_3",
                total_gross_amount=Decimal("10"),
                billing_address=address3
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                token="order_token_4",
                total_gross_amount=Decimal("20"),
                billing_address=address4
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                token="order_token_5",
                total_gross_amount=Decimal("50"),
                billing_address=address5
            ),
        ]
    )


@pytest.fixture
def pages_for_pagination():
    Page.objects.bulk_create(
        [
            Page(
                name="About",
                slug="about",
                is_published=False
            ),
            Page(
                name="Abou2",
                slug="about",
                is_published=False
            ),
            Page(
                name="About3",
                slug="about",
                is_published=False
            ),
            Page(
                name="Page1",
                slug="slug_page_1",
                is_published=True
            ),
            Page(
                name="Page2",
                slug="slug_page_2",
                is_published=True
            ),
        ]
    )


def create_global_cursor(instance, fields_list):
    return to_global_cursor([get_field_value(instance, field) for field in fields_list])


def create_cursor_from_user_email(email, fields_list):
    user = (
        User.objects.filter(email=email)
        .annotate(order_count=Count("orders__id"))
        .first()
    )
    return create_global_cursor(user, fields_list)


def create_cursor_from_group_name(name, fields_list):
    group = auth_models.Group.objects.get(name=name)
    return create_global_cursor(group, fields_list)


def create_cursor_from_service_account_name(name, fields_list):
    service_account = ServiceAccount.objects.get(name=name)
    return create_global_cursor(service_account, fields_list)


def create_cursor_from_checkout_date(token, fields_list):
    checkout = Checkout.objects.get(token=token)
    return create_global_cursor(checkout, fields_list)


def create_cursor_from_sales_name(name, fields_list):
    sale = Sale.objects.get(name=name)
    return create_global_cursor(sale, fields_list)


def create_cursor_from_voucher_code(code, fields_list):
    voucher = Voucher.objects.get(code=code)
    return create_global_cursor(voucher, fields_list)


def create_cursor_from_menu_name(name, fields_list):
    menu = Menu.objects.filter(name=name).annotate(items_count=Count("items__id")).first()
    return create_global_cursor(menu, fields_list)


def create_cursor_from_order_token(token, fields_list):
    order_qs = Order.objects.filter(token=token)
    last_payments = (
        order_qs.exclude(payments__isnull=True)
            .annotate(payment_id=Max("payments__pk"))
            .values_list("payment_id", flat=True)
    )
    order = order_qs.annotate(
        last_payment=FilteredRelation(
            "payments", condition=Q(payments__pk__in=last_payments)
        )
    ).first()
    return create_global_cursor(order, fields_list)


def create_cursor_from_page_slug(slug, fields_list):
    page = Page.objects.get(slug=slug)
    return create_global_cursor(page, fields_list)


def _test_pagination(
    staff_api_client,
    query,
    order_by,
    permission,
    start_cursor_page1,
    end_cursor_page1,
    start_cursor_page2,
    end_cursor_page2,
    resolver_name,
):
    variables = {"first": 3, "after": None, "sortBy": order_by}

    staff_api_client.user.user_permissions.add(permission)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    page_info = content["data"][resolver_name]["pageInfo"]

    assert not page_info["hasPreviousPage"]
    assert page_info["hasNextPage"]
    assert page_info["startCursor"] == start_cursor_page1
    assert page_info["endCursor"] == end_cursor_page1

    variables = {"first": 3, "after": end_cursor_page1, "sortBy": order_by}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    page_info = content["data"][resolver_name]["pageInfo"]

    assert page_info["hasPreviousPage"]
    assert not page_info["hasNextPage"]
    assert page_info["startCursor"] == start_cursor_page2
    assert page_info["endCursor"] == end_cursor_page2

    variables = {"last": 3, "before": start_cursor_page2, "sortBy": order_by}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    page_info = content["data"][resolver_name]["pageInfo"]

    assert not page_info["hasPreviousPage"]
    assert page_info["hasNextPage"]
    assert page_info["startCursor"] == start_cursor_page1
    assert page_info["endCursor"] == end_cursor_page1


@pytest.mark.parametrize(
    "order_by, cursor_fields, user_order",
    [
        (
            None,
            ["email"],
            [
                "allen@example.com",
                "ddevito@example.com",
                "ellen@example.com",
                "leslie@example.com",
                "zordon@example.com",
            ],
        ),
        (
            {"field": "FIRST_NAME", "direction": "ASC"},
            ["first_name", "last_name", "pk"],
            [
                "zordon@example.com",
                "leslie@example.com",
                "ddevito@example.com",
                "ellen@example.com",
                "allen@example.com",
            ],
        ),
        (
            {"field": "LAST_NAME", "direction": "ASC"},
            ["last_name", "first_name", "pk"],
            [
                "allen@example.com",
                "ddevito@example.com",
                "ellen@example.com",
                "zordon@example.com",
                "leslie@example.com",
            ],
        ),
        (
            {"field": "EMAIL", "direction": "ASC"},
            ["email"],
            [
                "allen@example.com",
                "ddevito@example.com",
                "ellen@example.com",
                "leslie@example.com",
                "zordon@example.com",
            ],
        ),
        (
            {"field": "EMAIL", "direction": "DESC"},
            ["email"],
            [
                "zordon@example.com",
                "leslie@example.com",
                "ellen@example.com",
                "ddevito@example.com",
                "allen@example.com",
            ],
        ),
        (
            {"field": "ORDER_COUNT", "direction": "DESC"},
            ["order_count", "email"],
            [
                "leslie@example.com",
                "allen@example.com",
                "zordon@example.com",
                "ellen@example.com",
                "ddevito@example.com",
            ],
        ),
    ],
)
def test_user_pagination(
    order_by,
    cursor_fields,
    user_order,
    staff_api_client,
    permission_manage_users,
    users_for_pagination,
):
    query = """
        query ($first: Int, $last: Int, $after: String, $before: String, $sortBy: UserSortingInput){
          customers(first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy) {
            edges {
              node {
                firstName
                lastName
                email
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """
    Order.objects.create(user=User.objects.get(email="allen@example.com"))
    Order.objects.create(user=User.objects.get(email="leslie@example.com"))
    Order.objects.create(user=User.objects.get(email="leslie@example.com"))

    start_cursor_page1 = create_cursor_from_user_email(user_order[0], cursor_fields)
    end_cursor_page1 = create_cursor_from_user_email(user_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_user_email(user_order[3], cursor_fields)
    end_cursor_page2 = create_cursor_from_user_email(user_order[4], cursor_fields)

    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_users,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="customers",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, group_order",
    [
        (None, ["pk"], ["Group5", "Group3", "A group", "Agroup", "Something",],),
        (
            {"field": "NAME", "direction": "ASC"},
            ["name"],
            ["A group", "Agroup", "Group3", "Group5", "Something",],
        ),
    ],
)
def test_permission_groups_pagination(
    order_by,
    cursor_fields,
    group_order,
    staff_api_client,
    permission_manage_staff,
    groups_for_pagination,
):
    query = """
        query ($first: Int, $last: Int, $after: String, $before: String, $sortBy: PermissionGroupSortingInput){
          permissionGroups(first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy) {
            edges {
              node {
                name
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """
    start_cursor_page1 = create_cursor_from_group_name(group_order[0], cursor_fields)
    end_cursor_page1 = create_cursor_from_group_name(group_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_group_name(group_order[3], cursor_fields)
    end_cursor_page2 = create_cursor_from_group_name(group_order[4], cursor_fields)

    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_staff,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="permissionGroups",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, service_account_order",
    [
        (
            None,
            ["name", "pk"],
            [
                "A Service Account",
                "Example Service Account",
                "Service Account",
                "ServiceAccount",
                "The Service Account",
            ],
        ),
        (
            {"field": "NAME", "direction": "ASC"},
            ["name", "pk"],
            [
                "A Service Account",
                "Example Service Account",
                "Service Account",
                "ServiceAccount",
                "The Service Account",
            ],
        ),
        (
            {"field": "CREATION_DATE", "direction": "ASC"},
            ["created", "name", "pk"],
            [
                "ServiceAccount",
                "Service Account",
                "A Service Account",
                "The Service Account",
                "Example Service Account",
            ],
        ),
    ],
)
def test_service_accounts_pagination(
    order_by,
    cursor_fields,
    service_account_order,
    staff_api_client,
    permission_manage_service_accounts,
    service_accounts_for_pagination,
):
    query = """
        query ($first: Int, $last: Int, $after: String, $before: String, $sortBy: ServiceAccountSortingInput){
          serviceAccounts(first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy) {
            edges {
              node {
                name
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """
    start_cursor_page1 = create_cursor_from_service_account_name(
        service_account_order[0], cursor_fields
    )
    end_cursor_page1 = create_cursor_from_service_account_name(
        service_account_order[2], cursor_fields
    )
    start_cursor_page2 = create_cursor_from_service_account_name(
        service_account_order[3], cursor_fields
    )
    end_cursor_page2 = create_cursor_from_service_account_name(
        service_account_order[4], cursor_fields
    )

    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_service_accounts,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="serviceAccounts",
    )


@pytest.mark.parametrize(
    "cursor_fields, checkout_order",
    [
        (
            ["last_change"],
            [
                "3e6140c5-5784-4965-8dc0-4d5ee4b9409a",
                "308a080e-29e1-4eab-b856-148b925409c1",
                "31ad7bf3-2e0d-435d-aa8c-c23abaf6a934",
                "63256386-a913-4dea-bee9-40c3f1faf952",
                "1fa91751-fd0a-45ca-8633-4bac9f5cb2a7",
            ],
        ),
    ],
)
def test_checkouts_pagination(
    cursor_fields,
    checkout_order,
    staff_api_client,
    permission_manage_checkouts,
    checkouts_for_pagination,
):
    query = """
        query ($first: Int, $last: Int, $after: String, $before: String){
          checkouts(first: $first, last: $last, after: $after, before: $before) {
            edges {
              node {
                token
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """
    start_cursor_page1 = create_cursor_from_checkout_date(
        checkout_order[0], cursor_fields
    )
    end_cursor_page1 = create_cursor_from_checkout_date(
        checkout_order[2], cursor_fields
    )
    start_cursor_page2 = create_cursor_from_checkout_date(
        checkout_order[3], cursor_fields
    )
    end_cursor_page2 = create_cursor_from_checkout_date(
        checkout_order[4], cursor_fields
    )

    _test_pagination(
        staff_api_client,
        query,
        None,
        permission_manage_checkouts,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="checkouts",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, sales_order",
    [
        (
            None,
            ["name", "pk"],
            ["A Sale", "An example sale", "Example Sale", "Sale example", "The Sale",],
        ),
        (
            {"field": "NAME", "direction": "ASC"},
            ["name", "pk"],
            ["A Sale", "An example sale", "Example Sale", "Sale example", "The Sale",],
        ),
        (
            {"field": "START_DATE", "direction": "ASC"},
            ["start_date", "name", "pk"],
            ["A Sale", "The Sale", "Example Sale", "Sale example", "An example sale",],
        ),
        (
            {"field": "END_DATE", "direction": "ASC"},
            ["end_date", "name", "pk"],
            ["Sale example", "The Sale", "Example Sale", "A Sale", "An example sale",],
        ),
        (
            {"field": "VALUE", "direction": "ASC"},
            ["value", "name", "pk"],
            ["An example sale", "A Sale", "Example Sale", "Sale example", "The Sale",],
        ),
        (
            {"field": "TYPE", "direction": "ASC"},
            ["type", "name", "pk"],
            ["An example sale", "Sale example", "The Sale", "A Sale", "Example Sale",],
        ),
    ],
)
def test_sales_pagination(
    order_by,
    cursor_fields,
    sales_order,
    staff_api_client,
    permission_manage_discounts,
    sales_for_pagination,
):
    query = """
        query ($first: Int, $last: Int, $after: String, $before: String, $sortBy: SaleSortingInput){
          sales(first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy) {
            edges {
              node {
                name
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """
    start_cursor_page1 = create_cursor_from_sales_name(sales_order[0], cursor_fields)
    end_cursor_page1 = create_cursor_from_sales_name(sales_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_sales_name(sales_order[3], cursor_fields)
    end_cursor_page2 = create_cursor_from_sales_name(sales_order[4], cursor_fields)

    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_discounts,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="sales",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, voucher_order",
    [
        (
            None,
            ["code"],
            [
                "An-example-v",
                "Example-code",
                "The-code",
                "Voucher-ex",
                "code",
            ],
        ),
        (
            {"field": "CODE", "direction": "ASC"},
            ["code"],
            [
                "An-example-v",
                "Example-code",
                "The-code",
                "Voucher-ex",
                "code",
            ],
        ),
        (
            {"field": "START_DATE", "direction": "ASC"},
            ["start_date", "name", "code"],
            [
                "code",
                "The-code",
                "Example-code",
                "Voucher-ex",
                "An-example-v",
            ],
        ),
        (
            {"field": "END_DATE", "direction": "ASC"},
            ["end_date", "name", "code"],
            [
                "The-code",
                "Voucher-ex",
                "Example-code",
                "code",
                "An-example-v",
            ],
        ),
        (
            {"field": "VALUE", "direction": "ASC"},
            ["discount_value", "name", "code"],
            [
                "code",
                "An-example-v",
                "Example-code",
                "Voucher-ex",
                "The-code",
            ],
        ),
        (
            {"field": "TYPE", "direction": "ASC"},
            ["type", "name", "code"],
            [
                "An-example-v",
                "The-code",
                "Voucher-ex",
                "Example-code",
                "code",
            ],
        ),
        (
            {"field": "USAGE_LIMIT", "direction": "ASC"},
            ["usage_limit", "name", "code"],
            [
                "An-example-v",
                "code",
                "Example-code",
                "Voucher-ex",
                "The-code",
            ],
        ),
        (
            {"field": "MINIMUM_SPENT_AMOUNT", "direction": "ASC"},
            ["min_spent_amount", "name", "code"],
            [
                "The-code",
                "code",
                "Voucher-ex",
                "An-example-v",
                "Example-code",
            ],
        ),
    ],
)
def test_voucher_pagination(
    order_by,
    cursor_fields,
    voucher_order,
    staff_api_client,
    permission_manage_discounts,
    voucher_for_pagination,
):
    query = """
        query ($first: Int, $last: Int, $after: String, $before: String, $sortBy: VoucherSortingInput){
          vouchers(first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy) {
            edges {
              node {
                code
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """
    start_cursor_page1 = create_cursor_from_voucher_code(voucher_order[0], cursor_fields)
    end_cursor_page1 = create_cursor_from_voucher_code(voucher_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_voucher_code(voucher_order[3], cursor_fields)
    end_cursor_page2 = create_cursor_from_voucher_code(voucher_order[4], cursor_fields)

    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_discounts,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="vouchers",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, menus_order",
    [
        # We have "footer" and "navbar" from default saleor configuration
        (
            None,
            ["pk"],
            [
                "navbar",
                "footer",
                "The menu",
                "The example menu",
                "Just menu",
            ],
        ),
        (
            {"field": "NAME", "direction": "ASC"},
            ["name", "pk"],
            [
                "Just menu",
                "The example menu",
                "The menu",
                "footer",
                "navbar",
            ],
        ),
        (
            {"field": "ITEMS_COUNT", "direction": "ASC"},
            ["items_count", "name", "pk"],
            [
                "footer",
                "navbar",
                "The menu",
                "The example menu",
                "Just menu",
            ],
        ),
    ],
)
def test_menus_pagination(
    order_by,
    cursor_fields,
    menus_order,
    staff_api_client,
    permission_manage_plugins,
    menus_for_pagination
):
    query = """
        query ($first: Int, $last: Int, $after: String, $before: String, $sortBy: MenuSortingInput){
          menus(first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy) {
            edges {
              node {
                name
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """
    start_cursor_page1 = create_cursor_from_menu_name(menus_order[0], cursor_fields)
    end_cursor_page1 = create_cursor_from_menu_name(menus_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_menu_name(menus_order[3], cursor_fields)
    end_cursor_page2 = create_cursor_from_menu_name(menus_order[4], cursor_fields)

    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_plugins,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="menus",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, orders_order",
    [
        (
            None,
            ["pk"],
            [
                "order_token_5",
                "order_token_4",
                "order_token_3",
                "order_token_2",
                "order_token_1",
            ],
        ),
        (
            {"field": "NUMBER", "direction": "ASC"},
            ["pk"],
            [
                "order_token_1",
                "order_token_2",
                "order_token_3",
                "order_token_4",
                "order_token_5",
            ],
        ),
        (
            {"field": "CREATION_DATE", "direction": "ASC"},
            ["created", "status", "pk"],
            [
                "order_token_1",
                "order_token_2",
                "order_token_3",
                "order_token_4",
                "order_token_5",
            ],
        ),
        (
            {"field": "CUSTOMER", "direction": "ASC"},
            ["billing_address__last_name", "billing_address__first_name", "pk"],
            [
                "order_token_1",
                "order_token_4",
                "order_token_5",
                "order_token_2",
                "order_token_3",
            ],
        ),
        (
            {"field": "PAYMENT", "direction": "ASC"},
            ["last_payment__charge_status", "status", "pk"],
            [
                "order_token_1",
                "order_token_2",
                "order_token_3",
                "order_token_4",
                "order_token_5",
            ],
        ),
        (
            {"field": "FULFILLMENT_STATUS", "direction": "ASC"},
            ["status", "user_email", "pk"],
            [
                "order_token_1",
                "order_token_2",
                "order_token_3",
                "order_token_4",
                "order_token_5",
            ],
        ),
        (
            {"field": "TOTAL", "direction": "ASC"},
            ["total_gross_amount", "status", "pk"],
            [
                "order_token_1",
                "order_token_3",
                "order_token_2",
                "order_token_4",
                "order_token_5",
            ],
        ),
    ],
)
def test_orders_pagination(
    order_by,
    cursor_fields,
    orders_order,
    staff_api_client,
    permission_manage_orders,
    orders_for_pagination
):
    query = """
        query ($first: Int, $last: Int, $after: String, $before: String, $sortBy: OrderSortingInput){
          orders(first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy) {
            edges {
              node {
                token
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """
    start_cursor_page1 = create_cursor_from_order_token(orders_order[0], cursor_fields)
    end_cursor_page1 = create_cursor_from_order_token(orders_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_order_token(orders_order[3], cursor_fields)
    end_cursor_page2 = create_cursor_from_order_token(orders_order[4], cursor_fields)

    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_orders,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="orders",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, page_order",
    [
        (
            {"field": "VISIBILITY", "direction": "ASC"},
            ["is_published", "title", "slug"],
            [
                "about",
                "about2",
                "about3",
                "slug_page_1",
                "slug_page_2",
            ]
        ),
        (
            None,
            ["slug"],
            [
                "about",
                "about2",
                "about3",
                "slug_page_1",
                "slug_page_2",
            ]
         ),
    ],
)
def test_page_pagination(
    order_by, cursor_fields, page_order, staff_api_client, permission_manage_pages, pages_for_pagination
):
    query = """
        query ($after: String, $sortBy: PageSortingInput){
          pages(first: 3, after: $after, sortBy: $sortBy) {
            edges {
              node {
                  title
              }
            }
            pageInfo{
              startCursor
              endCursor
              hasNextPage
              hasPreviousPage
            }
          }
        }
    """

    start_cursor_page1 = create_cursor_from_order_token(page_order[0], cursor_fields)
    end_cursor_page1 = create_cursor_from_order_token(page_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_order_token(page_order[3], cursor_fields)
    end_cursor_page2 = create_cursor_from_order_token(page_order[4], cursor_fields)
    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_pages,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        resolver_name="pages",
    )
