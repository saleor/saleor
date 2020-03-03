from decimal import Decimal

import pytest
from django.contrib.auth import models as auth_models
from django.db.models import Count
from django.utils import timezone
from prices import Money

from saleor.account.models import Address, ServiceAccount, User
from saleor.checkout.models import Checkout
from saleor.discount import DiscountValueType
from saleor.discount.models import Sale, Voucher
from saleor.graphql.account.sorters import (
    PermissionGroupSortField,
    ServiceAccountSortField,
    UserSortField,
)
from saleor.graphql.core.connection import get_field_value, to_global_cursor
from saleor.graphql.discount.sorters import SaleSortField, VoucherSortField
from saleor.graphql.order.sorters import OrderSortField
from saleor.graphql.page.sorters import PageSortField
from saleor.graphql.product.sorters import AttributeSortField, CategorySortField
from saleor.menu.models import Menu
from saleor.order import OrderStatus
from saleor.order.models import Order
from saleor.page.models import Page
from saleor.payment import ChargeStatus
from saleor.payment.models import Payment
from saleor.product.models import Attribute, Category, Product, ProductType
from tests.api.utils import get_graphql_content


@pytest.fixture
def users_for_pagination():
    return User.objects.bulk_create(
        [
            User(
                first_name="Lily",
                last_name="Allen",
                email="allen@example.com",
                is_active=True,
            ),
            User(
                first_name="Bob",
                last_name="Dylan",
                email="zordon@example.com",
                is_active=True,
            ),
            User(
                first_name="Clark",
                last_name="Kent",
                email="leslie@example.com",
                is_active=True,
            ),
            User(
                first_name="Danny",
                last_name="Devito",
                email="ddevito@example.com",
                is_active=True,
            ),
            User(
                first_name="Ellen",
                last_name="Degeneres",
                email="ellen@example.com",
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
            auth_models.Group(name="Group",),
            auth_models.Group(name="Something",),
        ]
    )


@pytest.fixture
def service_accounts_for_pagination():
    ServiceAccount.objects.bulk_create(
        [
            ServiceAccount(name="Service Account",),
            ServiceAccount(name="Second Service Account",),
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
                name="Sale",
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
                code="Code",
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
def address():
    def _make_address(first_name, last_name):
        return Address(
            first_name=first_name,
            last_name=last_name,
            company_name="Mirumee Software",
            street_address_1="Tęczowa 7",
            city="WROCŁAW",
            postal_code="53-601",
            country="PL",
            phone="+48713988102",
        )

    return _make_address


@pytest.fixture
def payment():
    def _make_payment(token, order, charge_status=ChargeStatus.NOT_CHARGED):
        return Payment(
            gateway="Dummy",
            token=token,
            order=order,
            is_active=True,
            cc_first_digits="4111",
            cc_last_digits="1111",
            cc_brand="VISA",
            cc_exp_month=12,
            cc_exp_year=2027,
            total=order.total.gross.amount,
            currency=order.total.gross.currency,
            charge_status=charge_status,
            to_confirm=True,
            billing_first_name=order.billing_address.first_name,
            billing_last_name=order.billing_address.last_name,
            billing_company_name=order.billing_address.company_name,
            billing_address_1=order.billing_address.street_address_1,
            billing_address_2=order.billing_address.street_address_2,
            billing_city=order.billing_address.city,
            billing_postal_code=order.billing_address.postal_code,
            billing_country_code=order.billing_address.country.code,
            billing_country_area=order.billing_address.country_area,
            billing_email=order.user_email,
        )

    return _make_payment


@pytest.fixture
def orders_for_pagination(users_for_pagination, payment, address):
    addresses = Address.objects.bulk_create(
        [
            address(first_name="Lily", last_name="Allen",),
            address(first_name="Bob", last_name="Dylan",),
            address(first_name="Clark", last_name="Kent",),
            address(first_name="Danny", last_name="Devito",),
            address(first_name="Ellen", last_name="Degeneres",),
        ]
    )

    orders = Order.objects.bulk_create(
        [
            Order(
                user=users_for_pagination[0],
                status=OrderStatus.FULFILLED,
                token="order_token_1",
                total_gross_amount=Decimal("10"),
                billing_address=addresses[0],
            ),
            Order(
                user=users_for_pagination[0],
                status=OrderStatus.FULFILLED,
                token="order_token_2",
                total_gross_amount=Decimal("20"),
                billing_address=addresses[1],
            ),
            Order(
                user=users_for_pagination[0],
                status=OrderStatus.FULFILLED,
                token="order_token_3",
                total_gross_amount=Decimal("10"),
                billing_address=addresses[2],
            ),
            Order(
                user=users_for_pagination[2],
                status=OrderStatus.FULFILLED,
                token="order_token_4",
                total_gross_amount=Decimal("20"),
                billing_address=addresses[3],
            ),
            Order(
                user=users_for_pagination[2],
                status=OrderStatus.FULFILLED,
                token="order_token_5",
                total_gross_amount=Decimal("50"),
                billing_address=addresses[4],
            ),
        ]
    )

    Payment.objects.bulk_create(
        [
            payment(token="payment1", order=orders[0],),
            payment(token="payment2", order=orders[0],),
            payment(
                token="payment3",
                order=orders[2],
                charge_status=ChargeStatus.FULLY_CHARGED,
            ),
            payment(token="payment4", order=orders[3],),
            payment(
                token="payment5",
                order=orders[3],
                charge_status=ChargeStatus.FULLY_CHARGED,
            ),
        ]
    )


@pytest.fixture
def pages_for_pagination():
    Page.objects.bulk_create(
        [
            Page(title="About", slug="about", is_published=False),
            Page(title="About", slug="about2", is_published=False),
            Page(title="About3", slug="about3", is_published=False),
            Page(title="Page1", slug="slug_page_1", is_published=True),
            Page(title="Page2", slug="slug_page_2", is_published=True),
        ]
    )


@pytest.fixture
def attributes_for_pagination():
    return Attribute.objects.bulk_create(
        [
            Attribute(
                name="A",
                slug="a",
                value_required=True,
                is_variant_only=False,
                visible_in_storefront=False,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
                available_in_grid=True,
                storefront_search_position=2,
            ),
            Attribute(
                name="A",
                slug="b",
                value_required=True,
                is_variant_only=True,
                visible_in_storefront=True,
                filterable_in_storefront=False,
                filterable_in_dashboard=False,
                available_in_grid=True,
                storefront_search_position=5,
            ),
            Attribute(
                name="A",
                slug="c",
                value_required=False,
                is_variant_only=False,
                visible_in_storefront=False,
                filterable_in_storefront=False,
                filterable_in_dashboard=True,
                available_in_grid=True,
                storefront_search_position=2,
            ),
            Attribute(
                name="B",
                slug="d",
                value_required=False,
                is_variant_only=True,
                visible_in_storefront=True,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
                available_in_grid=False,
                storefront_search_position=4,
            ),
            Attribute(
                name="C",
                slug="e",
                value_required=False,
                is_variant_only=False,
                visible_in_storefront=True,
                filterable_in_storefront=True,
                filterable_in_dashboard=False,
                available_in_grid=False,
                storefront_search_position=5,
            ),
        ]
    )


@pytest.fixture
def categories_for_pagination():
    product_types = ProductType.objects.bulk_create(
        [
            ProductType(name="Default Type", slug="default-type",),
            ProductType(name="Default Type", slug="second-type",),
        ]
    )

    category1 = Category.objects.create(name="The Category", slug="the-category",)
    category2 = Category.objects.create(
        name="A Category", slug="second-category", parent=category1
    )
    category3 = Category.objects.create(
        name="The Category", slug="third-category", parent=category2
    )
    Category.objects.create(name="The Category", slug="category", parent=category2)
    Category.objects.create(name="The Category", slug="subcategory", parent=category3)

    Product.objects.bulk_create(
        [
            Product(
                name="Test product",
                slug="test-product",
                price=Money("10.00", "USD"),
                minimal_variant_price_amount=Decimal("4.00"),
                product_type=product_types[0],
                category=category1,
                is_published=True,
            ),
            Product(
                name="Test product",
                slug="a-product",
                price=Money("10.00", "USD"),
                minimal_variant_price_amount=Decimal("4.00"),
                product_type=product_types[1],
                category=category1,
                is_published=True,
            ),
            Product(
                name="Test product",
                slug="just-product",
                price=Money("10.00", "USD"),
                minimal_variant_price_amount=Decimal("2.00"),
                product_type=product_types[1],
                category=category2,
                is_published=True,
            ),
            Product(
                name="Test product",
                slug="second-product",
                price=Money("10.00", "USD"),
                minimal_variant_price_amount=Decimal("1.00"),
                product_type=product_types[0],
                category=category2,
                is_published=True,
            ),
            Product(
                name="Test product",
                slug="product",
                price=Money("10.00", "USD"),
                minimal_variant_price_amount=Decimal("10.00"),
                product_type=product_types[0],
                category=category3,
                is_published=True,
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
    menu = (
        Menu.objects.filter(name=name).annotate(items_count=Count("items__id")).first()
    )
    return create_global_cursor(menu, fields_list)


def create_cursor_from_order_token(token, fields_list):
    order_qs = Order.objects.filter(token=token)
    order = OrderSortField.qs_with_payment(order_qs).first()
    return create_global_cursor(order, fields_list)


def create_cursor_from_page_slug(slug, fields_list):
    page = Page.objects.get(slug=slug)
    return create_global_cursor(page, fields_list)


def create_cursor_from_payment_token(token, fields_list):
    payment = Payment.objects.get(token=token)
    return create_global_cursor(payment, fields_list)


def create_cursor_from_attribute_slug(slug, fields_list):
    attribute = Attribute.objects.get(slug=slug)
    return create_global_cursor(attribute, fields_list)


def create_cursor_from_category_slug(slug, fields_list):
    category = Category.objects.filter(slug=slug)
    category = CategorySortField.qs_with_product_count(category)
    category = CategorySortField.qs_with_subcategory_count(category).first()

    return create_global_cursor(category, fields_list)


def _test_pagination(
    staff_api_client,
    query,
    order_by,
    permission,
    start_cursor_page1,
    end_cursor_page1,
    start_cursor_page2,
    end_cursor_page2,
    start_cursor_before,
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

    variables = {"last": 2, "before": start_cursor_page2, "sortBy": order_by}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    page_info = content["data"][resolver_name]["pageInfo"]

    assert page_info["hasPreviousPage"]
    assert page_info["hasNextPage"]
    assert page_info["startCursor"] == start_cursor_before
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
            UserSortField.FIRST_NAME.value,
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
            UserSortField.LAST_NAME.value,
            [
                "allen@example.com",
                "ellen@example.com",
                "ddevito@example.com",
                "zordon@example.com",
                "leslie@example.com",
            ],
        ),
        (
            {"field": "EMAIL", "direction": "ASC"},
            UserSortField.EMAIL.value,
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
            UserSortField.EMAIL.value,
            [
                "zordon@example.com",
                "leslie@example.com",
                "ellen@example.com",
                "ddevito@example.com",
                "allen@example.com",
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
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: UserSortingInput
         ){
          customers(
            first: $first, last: $last, after: $after,
            before: $before, sortBy: $sortBy
        ) {
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
    start_cursor_page1 = create_cursor_from_user_email(user_order[0], cursor_fields)
    start_cursor_before = create_cursor_from_user_email(user_order[1], cursor_fields)
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
        start_cursor_before,
        resolver_name="customers",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, user_order",
    [
        (
            {"field": "ORDER_COUNT", "direction": "DESC"},
            UserSortField.ORDER_COUNT.value,
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
def test_user_with_order_pagination(
    order_by,
    cursor_fields,
    user_order,
    staff_api_client,
    permission_manage_users,
    users_for_pagination,
):
    query = """
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: UserSortingInput
         ){
          customers(
            first: $first, last: $last, after: $after,
            before: $before, sortBy: $sortBy
        ) {
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
    Order.objects.bulk_create(
        [
            Order(user=User.objects.get(email="allen@example.com"), token="1"),
            Order(user=User.objects.get(email="leslie@example.com"), token="2"),
            Order(user=User.objects.get(email="leslie@example.com"), token="3"),
        ]
    )

    start_cursor_page1 = create_cursor_from_user_email(user_order[0], cursor_fields)
    start_cursor_before = create_cursor_from_user_email(user_order[1], cursor_fields)
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
        start_cursor_before,
        resolver_name="customers",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, group_order",
    [
        (None, ["pk"], ["Group5", "Group3", "A group", "Group", "Something"],),
        (
            {"field": "NAME", "direction": "ASC"},
            PermissionGroupSortField.NAME.value,
            ["A group", "Group", "Group3", "Group5", "Something"],
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
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: PermissionGroupSortingInput
            ){
          permissionGroups(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy
            ) {
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
    start_cursor_before = create_cursor_from_group_name(group_order[1], cursor_fields)
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
        start_cursor_before,
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
                "Second Service Account",
                "Service Account",
                "The Service Account",
            ],
        ),
        (
            {"field": "NAME", "direction": "ASC"},
            ServiceAccountSortField.NAME.value,
            [
                "A Service Account",
                "Example Service Account",
                "Second Service Account",
                "Service Account",
                "The Service Account",
            ],
        ),
        (
            {"field": "CREATION_DATE", "direction": "ASC"},
            ServiceAccountSortField.CREATION_DATE.value,
            [
                "Service Account",
                "Second Service Account",
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
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: ServiceAccountSortingInput
        ){
          serviceAccounts(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy
            ) {
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
    start_cursor_before = create_cursor_from_service_account_name(
        service_account_order[1], cursor_fields
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
        start_cursor_before,
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
    start_cursor_before = create_cursor_from_checkout_date(
        checkout_order[1], cursor_fields
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
        start_cursor_before,
        resolver_name="checkouts",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, sales_order",
    [
        (
            None,
            ["name", "pk"],
            ["An example sale", "Example Sale", "Sale", "Sale example", "The Sale"],
        ),
        (
            {"field": "NAME", "direction": "ASC"},
            SaleSortField.NAME.value,
            ["An example sale", "Example Sale", "Sale", "Sale example", "The Sale"],
        ),
        (
            {"field": "START_DATE", "direction": "ASC"},
            SaleSortField.START_DATE.value,
            ["Sale", "The Sale", "Example Sale", "Sale example", "An example sale"],
        ),
        (
            {"field": "END_DATE", "direction": "ASC"},
            SaleSortField.END_DATE.value,
            ["Sale example", "The Sale", "Example Sale", "Sale", "An example sale"],
        ),
        (
            {"field": "VALUE", "direction": "ASC"},
            SaleSortField.VALUE.value,
            ["An example sale", "Sale", "Example Sale", "Sale example", "The Sale"],
        ),
        (
            {"field": "TYPE", "direction": "ASC"},
            SaleSortField.TYPE.value,
            ["An example sale", "Sale example", "The Sale", "Example Sale", "Sale"],
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
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: SaleSortingInput
        ){
          sales(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy
           ) {
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
    start_cursor_before = create_cursor_from_sales_name(sales_order[1], cursor_fields)
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
        start_cursor_before,
        resolver_name="sales",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, voucher_order",
    [
        (
            None,
            ["code"],
            ["An-example-v", "Code", "Example-code", "The-code", "Voucher-ex"],
        ),
        (
            {"field": "CODE", "direction": "ASC"},
            VoucherSortField.CODE.value,
            ["An-example-v", "Code", "Example-code", "The-code", "Voucher-ex"],
        ),
        (
            {"field": "START_DATE", "direction": "ASC"},
            VoucherSortField.START_DATE.value,
            ["Code", "The-code", "Example-code", "Voucher-ex", "An-example-v"],
        ),
        (
            {"field": "END_DATE", "direction": "ASC"},
            VoucherSortField.END_DATE.value,
            ["The-code", "Voucher-ex", "Example-code", "Code", "An-example-v"],
        ),
        (
            {"field": "VALUE", "direction": "ASC"},
            VoucherSortField.VALUE.value,
            ["Code", "An-example-v", "Example-code", "Voucher-ex", "The-code"],
        ),
        (
            {"field": "TYPE", "direction": "ASC"},
            VoucherSortField.TYPE.value,
            ["An-example-v", "The-code", "Voucher-ex", "Code", "Example-code"],
        ),
        (
            {"field": "USAGE_LIMIT", "direction": "ASC"},
            VoucherSortField.USAGE_LIMIT.value,
            ["An-example-v", "Code", "Example-code", "Voucher-ex", "The-code"],
        ),
        (
            {"field": "MINIMUM_SPENT_AMOUNT", "direction": "ASC"},
            VoucherSortField.MINIMUM_SPENT_AMOUNT.value,
            ["Code", "The-code", "Voucher-ex", "An-example-v", "Example-code"],
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
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: VoucherSortingInput
        ){
          vouchers(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy
            ) {
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
    start_cursor_page1 = create_cursor_from_voucher_code(
        voucher_order[0], cursor_fields
    )
    start_cursor_before = create_cursor_from_voucher_code(
        voucher_order[1], cursor_fields
    )
    end_cursor_page1 = create_cursor_from_voucher_code(voucher_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_voucher_code(
        voucher_order[3], cursor_fields
    )
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
        start_cursor_before,
        resolver_name="vouchers",
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
            OrderSortField.NUMBER.value,
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
            OrderSortField.CREATION_DATE.value,
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
            OrderSortField.CUSTOMER.value,
            [
                "order_token_1",
                "order_token_5",
                "order_token_4",
                "order_token_2",
                "order_token_3",
            ],
        ),
        (
            {"field": "PAYMENT", "direction": "ASC"},
            OrderSortField.PAYMENT.value,
            [
                "order_token_3",
                "order_token_4",
                "order_token_1",
                "order_token_2",
                "order_token_5",
            ],
        ),
        (
            {"field": "FULFILLMENT_STATUS", "direction": "ASC"},
            OrderSortField.FULFILLMENT_STATUS.value,
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
            OrderSortField.TOTAL.value,
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
    orders_for_pagination,
):
    query = """
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: OrderSortingInput
        ){
          orders(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy
            ) {
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
    start_cursor_before = create_cursor_from_order_token(orders_order[1], cursor_fields)
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
        start_cursor_before,
        resolver_name="orders",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, page_order",
    [
        (
            {"field": "VISIBILITY", "direction": "ASC"},
            PageSortField.VISIBILITY.value,
            ["about", "about2", "about3", "slug_page_1", "slug_page_2"],
        ),
        (None, ["slug"], ["about", "about2", "about3", "slug_page_1", "slug_page_2"]),
    ],
)
def test_page_pagination(
    order_by,
    cursor_fields,
    page_order,
    staff_api_client,
    permission_manage_pages,
    pages_for_pagination,
):
    query = """
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: PageSortingInput
        ){
          pages(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy
          ) {
            edges {
              node {
                  title
                  slug
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

    start_cursor_page1 = create_cursor_from_page_slug(page_order[0], cursor_fields)
    start_cursor_before = create_cursor_from_page_slug(page_order[1], cursor_fields)
    end_cursor_page1 = create_cursor_from_page_slug(page_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_page_slug(page_order[3], cursor_fields)
    end_cursor_page2 = create_cursor_from_page_slug(page_order[4], cursor_fields)
    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_pages,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        start_cursor_before,
        resolver_name="pages",
    )


@pytest.mark.parametrize(
    "cursor_fields, payment_order",
    [(["pk"], ["payment1", "payment2", "payment3", "payment4", "payment5"])],
)
def test_payment_pagination(
    cursor_fields,
    payment_order,
    staff_api_client,
    permission_manage_orders,
    orders_for_pagination,
):
    query = """
        query (
            $first: Int, $last: Int, $after: String, $before: String
        ){
          payments(
            first: $first, last: $last, after: $after, before: $before
          ) {
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

    start_cursor_page1 = create_cursor_from_payment_token(
        payment_order[0], cursor_fields
    )
    start_cursor_before = create_cursor_from_payment_token(
        payment_order[1], cursor_fields
    )
    end_cursor_page1 = create_cursor_from_payment_token(payment_order[2], cursor_fields)
    start_cursor_page2 = create_cursor_from_payment_token(
        payment_order[3], cursor_fields
    )
    end_cursor_page2 = create_cursor_from_payment_token(payment_order[4], cursor_fields)
    _test_pagination(
        staff_api_client,
        query,
        None,
        permission_manage_orders,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        start_cursor_before,
        resolver_name="payments",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, attribute_order",
    [
        (None, ["storefront_search_position", "slug"], ["a", "c", "d", "b", "e"],),
        (
            {"field": "NAME", "direction": "ASC"},
            AttributeSortField.NAME.value,
            ["a", "b", "c", "d", "e"],
        ),
        (
            {"field": "SLUG", "direction": "ASC"},
            AttributeSortField.SLUG.value,
            ["a", "b", "c", "d", "e"],
        ),
        (
            {"field": "VALUE_REQUIRED", "direction": "ASC"},
            AttributeSortField.VALUE_REQUIRED.value,
            ["c", "d", "e", "a", "b"],
        ),
        (
            {"field": "IS_VARIANT_ONLY", "direction": "ASC"},
            AttributeSortField.IS_VARIANT_ONLY.value,
            ["a", "c", "e", "b", "d"],
        ),
        (
            {"field": "VISIBLE_IN_STOREFRONT", "direction": "ASC"},
            AttributeSortField.VISIBLE_IN_STOREFRONT.value,
            ["a", "c", "b", "d", "e"],
        ),
        (
            {"field": "FILTERABLE_IN_STOREFRONT", "direction": "ASC"},
            AttributeSortField.FILTERABLE_IN_STOREFRONT.value,
            ["b", "c", "a", "d", "e"],
        ),
        (
            {"field": "FILTERABLE_IN_DASHBOARD", "direction": "ASC"},
            AttributeSortField.FILTERABLE_IN_DASHBOARD.value,
            ["b", "e", "a", "c", "d"],
        ),
        (
            {"field": "STOREFRONT_SEARCH_POSITION", "direction": "ASC"},
            AttributeSortField.STOREFRONT_SEARCH_POSITION.value,
            ["a", "c", "d", "b", "e"],
        ),
        (
            {"field": "AVAILABLE_IN_GRID", "direction": "ASC"},
            AttributeSortField.AVAILABLE_IN_GRID.value,
            ["d", "e", "a", "b", "c"],
        ),
    ],
)
def test_attribute_pagination(
    order_by,
    cursor_fields,
    attribute_order,
    staff_api_client,
    permission_manage_products,
    attributes_for_pagination,
):
    query = """
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: AttributeSortingInput
        ){
          attributes(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy
          ) {
            edges {
              node {
                  name
                  slug
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

    start_cursor_page1 = create_cursor_from_attribute_slug(
        attribute_order[0], cursor_fields
    )
    start_cursor_before = create_cursor_from_attribute_slug(
        attribute_order[1], cursor_fields
    )
    end_cursor_page1 = create_cursor_from_attribute_slug(
        attribute_order[2], cursor_fields
    )
    start_cursor_page2 = create_cursor_from_attribute_slug(
        attribute_order[3], cursor_fields
    )
    end_cursor_page2 = create_cursor_from_attribute_slug(
        attribute_order[4], cursor_fields
    )
    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_products,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        start_cursor_before,
        resolver_name="attributes",
    )


@pytest.mark.parametrize(
    "order_by, cursor_fields, category_order",
    [
        (
            None,
            ["pk"],
            [
                "the-category",
                "second-category",
                "third-category",
                "category",
                "subcategory",
            ],
        ),
        (
            {"field": "NAME", "direction": "ASC"},
            CategorySortField.NAME.value,
            [
                "second-category",
                "category",
                "subcategory",
                "the-category",
                "third-category",
            ],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "ASC"},
            CategorySortField.PRODUCT_COUNT.value,
            [
                "category",
                "subcategory",
                "third-category",
                "second-category",
                "the-category",
            ],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "DESC"},
            CategorySortField.SUBCATEGORY_COUNT.value,
            [
                "second-category",
                "third-category",
                "the-category",
                "subcategory",
                "category",
            ],
        ),
    ],
)
def test_category_pagination(
    order_by,
    cursor_fields,
    category_order,
    staff_api_client,
    permission_manage_products,
    categories_for_pagination,
):
    query = """
        query (
            $first: Int, $last: Int, $after: String,
            $before: String, $sortBy: CategorySortingInput
        ){
          categories(
            first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy
          ) {
            edges {
              node {
                  name
                  slug
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
    start_cursor_page1 = create_cursor_from_category_slug(
        category_order[0], cursor_fields
    )
    start_cursor_before = create_cursor_from_category_slug(
        category_order[1], cursor_fields
    )
    end_cursor_page1 = create_cursor_from_category_slug(
        category_order[2], cursor_fields
    )
    start_cursor_page2 = create_cursor_from_category_slug(
        category_order[3], cursor_fields
    )
    end_cursor_page2 = create_cursor_from_category_slug(
        category_order[4], cursor_fields
    )
    _test_pagination(
        staff_api_client,
        query,
        order_by,
        permission_manage_products,
        start_cursor_page1,
        end_cursor_page1,
        start_cursor_page2,
        end_cursor_page2,
        start_cursor_before,
        resolver_name="categories",
    )
