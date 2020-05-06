import datetime
import uuid
from contextlib import contextmanager
from decimal import Decimal
from functools import partial
from io import BytesIO
from typing import List, Optional
from unittest.mock import MagicMock, Mock

import pytest
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.forms import ModelForm
from django.test.utils import CaptureQueriesContext as BaseCaptureQueriesContext
from django_countries import countries
from PIL import Image
from prices import Money, TaxedMoney

from saleor.account.models import Address, StaffNotificationRecipient, User
from saleor.app.models import App
from saleor.checkout import utils
from saleor.checkout.models import Checkout
from saleor.checkout.utils import add_variant_to_checkout
from saleor.core.payments import PaymentInterface
from saleor.discount import DiscountInfo, DiscountValueType, VoucherType
from saleor.discount.models import (
    Sale,
    SaleTranslation,
    Voucher,
    VoucherCustomer,
    VoucherTranslation,
)
from saleor.giftcard.models import GiftCard
from saleor.menu.models import Menu, MenuItem, MenuItemTranslation
from saleor.menu.utils import update_menu
from saleor.order import OrderStatus
from saleor.order.actions import cancel_fulfillment, fulfill_order_line
from saleor.order.events import OrderEvents
from saleor.order.models import FulfillmentStatus, Order, OrderEvent, OrderLine
from saleor.order.utils import recalculate_order
from saleor.page.models import Page, PageTranslation
from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.models import Payment
from saleor.product import AttributeInputType
from saleor.product.models import (
    Attribute,
    AttributeTranslation,
    AttributeValue,
    AttributeValueTranslation,
    Category,
    CategoryTranslation,
    Collection,
    CollectionTranslation,
    DigitalContent,
    DigitalContentUrl,
    Product,
    ProductImage,
    ProductTranslation,
    ProductType,
    ProductVariant,
    ProductVariantTranslation,
)
from saleor.product.utils.attributes import associate_attribute_values_to_instance
from saleor.shipping.models import (
    ShippingMethod,
    ShippingMethodTranslation,
    ShippingMethodType,
    ShippingZone,
)
from saleor.site import AuthenticationBackends
from saleor.site.models import AuthorizationKey, SiteSettings
from saleor.warehouse.models import Allocation, Stock, Warehouse
from saleor.webhook.event_types import WebhookEventType
from saleor.webhook.models import Webhook
from saleor.wishlist.models import Wishlist
from tests.utils import create_image


class CaptureQueriesContext(BaseCaptureQueriesContext):
    IGNORED_QUERIES = settings.PATTERNS_IGNORED_IN_QUERY_CAPTURES  # type: ignore

    @property
    def captured_queries(self):
        # flake8: noqa
        base_queries = self.connection.queries[
            self.initial_queries : self.final_queries
        ]
        new_queries = []

        def is_query_ignored(sql):
            for pattern in self.IGNORED_QUERIES:
                # Ignore the query if matches
                if pattern.match(sql):
                    return True
            return False

        for query in base_queries:
            if not is_query_ignored(query["sql"]):
                new_queries.append(query)

        return new_queries


def _assert_num_queries(context, *, config, num, exact=True, info=None):
    """
    Extracted from pytest_django.fixtures._assert_num_queries
    """
    yield context

    verbose = config.getoption("verbose") > 0
    num_performed = len(context)

    if exact:
        failed = num != num_performed
    else:
        failed = num_performed > num

    if not failed:
        return

    msg = "Expected to perform {} queries {}{}".format(
        num,
        "" if exact else "or less ",
        "but {} done".format(
            num_performed == 1 and "1 was" or "%d were" % (num_performed,)
        ),
    )
    if info:
        msg += "\n{}".format(info)
    if verbose:
        sqls = (q["sql"] for q in context.captured_queries)
        msg += "\n\nQueries:\n========\n\n%s" % "\n\n".join(sqls)
    else:
        msg += " (add -v option to show queries)"
    pytest.fail(msg)


@pytest.fixture
def capture_queries(pytestconfig):
    cfg = pytestconfig

    @contextmanager
    def _capture_queries(
        num: Optional[int] = None, msg: Optional[str] = None, exact=False
    ):
        with CaptureQueriesContext(connection) as ctx:
            yield ctx
            if num is not None:
                _assert_num_queries(ctx, config=cfg, num=num, exact=exact, info=msg)

    return _capture_queries


@pytest.fixture
def assert_num_queries(capture_queries):
    return partial(capture_queries, exact=True)


@pytest.fixture
def assert_max_num_queries(capture_queries):
    return partial(capture_queries, exact=False)


@pytest.fixture(autouse=True)
def setup_dummy_gateway(settings):
    settings.PLUGINS = ["saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin"]
    return settings


@pytest.fixture(autouse=True)
def site_settings(db, settings) -> SiteSettings:
    """Create a site and matching site settings.

    This fixture is autouse because django.contrib.sites.models.Site and
    saleor.site.models.SiteSettings have a one-to-one relationship and a site
    should never exist without a matching settings object.
    """
    site = Site.objects.get_or_create(name="mirumee.com", domain="mirumee.com")[0]
    obj = SiteSettings.objects.get_or_create(
        site=site,
        default_mail_sender_name="Mirumee Labs",
        default_mail_sender_address="mirumee@example.com",
    )[0]
    settings.SITE_ID = site.pk

    main_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS["top_menu_name"]
    )[0]
    update_menu(main_menu)
    secondary_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS["bottom_menu_name"]
    )[0]
    update_menu(secondary_menu)
    obj.top_menu = main_menu
    obj.bottom_menu = secondary_menu
    obj.save()
    return obj


@pytest.fixture
def checkout(db):
    checkout = Checkout.objects.create()
    checkout.set_country("US", commit=True)
    return checkout


@pytest.fixture
def checkout_with_item(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_single_item(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_variant_without_inventory_tracking(
    checkout, variant_without_inventory_tracking
):
    variant = variant_without_inventory_tracking
    add_variant_to_checkout(checkout, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_items(checkout, product_list, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1)
    for prod in product_list:
        variant = prod.variants.get()
        add_variant_to_checkout(checkout, variant, 1)
    checkout.refresh_from_db()
    return checkout


@pytest.fixture
def checkout_with_voucher(checkout, product, voucher):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    checkout.voucher_code = voucher.code
    checkout.discount = Money("20.00", "USD")
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_voucher_percentage(checkout, product, voucher_percentage):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    checkout.voucher_code = voucher_percentage.code
    checkout.discount = Money("3.00", "USD")
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_gift_card(checkout_with_item, gift_card):
    checkout_with_item.gift_cards.add(gift_card)
    checkout_with_item.save()
    return checkout_with_item


@pytest.fixture
def checkout_with_voucher_percentage_and_shipping(
    checkout_with_voucher_percentage, shipping_method, address
):
    checkout = checkout_with_voucher_percentage
    checkout.shipping_method = shipping_method
    checkout.shipping_address = address
    checkout.save()
    return checkout


@pytest.fixture
def address(db):  # pylint: disable=W0613
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
    )


@pytest.fixture
def address_other_country():
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        street_address_1="4371 Lucas Knoll Apt. 791",
        city="BENNETTMOUTH",
        postal_code="13377",
        country="IS",
        phone="",
    )


@pytest.fixture
def address_usa():
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        street_address_1="2000 Main Street",
        city="Irvine",
        postal_code="92614",
        country_area="CA",
        country="US",
        phone="",
    )


@pytest.fixture
def graphql_address_data():
    return {
        "firstName": "John Saleor",
        "lastName": "Doe Mirumee",
        "companyName": "Mirumee Software",
        "streetAddress1": "Tęczowa 7",
        "streetAddress2": "",
        "postalCode": "53-601",
        "country": "PL",
        "city": "Wrocław",
        "countryArea": "",
        "phone": "+48321321888",
    }


@pytest.fixture
def customer_user(address):  # pylint: disable=W0613
    default_address = address.get_copy()
    user = User.objects.create_user(
        "test@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Leslie",
        last_name="Wade",
    )
    user.addresses.add(default_address)
    user._password = "password"
    return user


@pytest.fixture
def user_checkout(customer_user):
    checkout = Checkout.objects.create(
        user=customer_user,
        billing_address=customer_user.default_billing_address,
        shipping_address=customer_user.default_shipping_address,
        note="Test notes",
    )
    return checkout


@pytest.fixture
def user_checkout_with_items(user_checkout, product_list):
    for product in product_list:
        variant = product.variants.get()
        add_variant_to_checkout(user_checkout, variant, 1)
    user_checkout.refresh_from_db()
    return user_checkout


@pytest.fixture
def request_checkout(checkout, monkeypatch):
    # FIXME: Fixtures should not have any side effects
    monkeypatch.setattr(
        utils,
        "get_checkout_from_request",
        lambda request, checkout_queryset=None: checkout,
    )
    return checkout


@pytest.fixture
def request_checkout_with_item(product, request_checkout):
    variant = product.variants.get()
    add_variant_to_checkout(request_checkout, variant)
    return request_checkout


@pytest.fixture
def order(customer_user):
    address = customer_user.default_billing_address.get_copy()
    return Order.objects.create(
        billing_address=address, user_email=customer_user.email, user=customer_user
    )


@pytest.fixture
def admin_user(db):
    """Return a Django admin user."""
    return User.objects.create_superuser("admin@example.com", "password")


@pytest.fixture
def staff_user(db):
    """Return a staff member."""
    return User.objects.create_user(
        email="staff_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )


@pytest.fixture
def staff_users(staff_user):
    """Return a staff members."""
    staff_users = User.objects.bulk_create(
        [
            User(
                email="staff1_test@example.com",
                password="password",
                is_staff=True,
                is_active=True,
            ),
            User(
                email="staff2_test@example.com",
                password="password",
                is_staff=True,
                is_active=True,
            ),
        ]
    )
    return [staff_user] + staff_users


@pytest.fixture
def shipping_zone(db):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(
        name="Europe", countries=[code for code, name in countries]
    )
    shipping_zone.shipping_methods.create(
        name="DHL",
        minimum_order_price=Money(0, "USD"),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(10, "USD"),
        shipping_zone=shipping_zone,
    )
    return shipping_zone


@pytest.fixture
def shipping_zone_without_countries(db):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(name="Europe", countries=[])
    shipping_zone.shipping_methods.create(
        name="DHL",
        minimum_order_price=Money(0, "USD"),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(10, "USD"),
        shipping_zone=shipping_zone,
    )
    return shipping_zone


@pytest.fixture
def shipping_method(shipping_zone):
    return ShippingMethod.objects.create(
        name="DHL",
        minimum_order_price=Money(0, "USD"),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(10, "USD"),
        shipping_zone=shipping_zone,
    )


@pytest.fixture
def color_attribute(db):  # pylint: disable=W0613
    attribute = Attribute.objects.create(slug="color", name="Color")
    AttributeValue.objects.create(attribute=attribute, name="Red", slug="red")
    AttributeValue.objects.create(attribute=attribute, name="Blue", slug="blue")
    return attribute


@pytest.fixture
def color_attribute_without_values(db):  # pylint: disable=W0613
    return Attribute.objects.create(slug="color", name="Color")


@pytest.fixture
def pink_attribute_value(color_attribute):  # pylint: disable=W0613
    value = AttributeValue.objects.create(
        slug="pink", name="Pink", attribute=color_attribute, value="#FF69B4"
    )
    return value


@pytest.fixture
def size_attribute(db):  # pylint: disable=W0613
    attribute = Attribute.objects.create(slug="size", name="Size")
    AttributeValue.objects.create(attribute=attribute, name="Small", slug="small")
    AttributeValue.objects.create(attribute=attribute, name="Big", slug="big")
    return attribute


@pytest.fixture
def attribute_list() -> List[Attribute]:
    return list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="size", name="Size"),
                Attribute(slug="weight", name="Weight"),
                Attribute(slug="thickness", name="Thickness"),
            ]
        )
    )


@pytest.fixture
def image():
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    return SimpleUploadedFile("product.jpg", img_data.getvalue())


@pytest.fixture
def category(db):  # pylint: disable=W0613
    return Category.objects.create(name="Default", slug="default")


@pytest.fixture
def category_with_image(db, image, media_root):  # pylint: disable=W0613
    return Category.objects.create(
        name="Default", slug="default", background_image=image
    )


@pytest.fixture
def categories_tree(db, product_type):  # pylint: disable=W0613
    parent = Category.objects.create(name="Parent", slug="parent")
    parent.children.create(name="Child", slug="child")
    child = parent.children.first()

    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-10",
        price=Money(10, "USD"),
        product_type=product_type,
        category=child,
        is_published=True,
    )

    associate_attribute_values_to_instance(product, product_attr, attr_value)
    return parent


@pytest.fixture
def categories_tree_with_published_products(categories_tree, product):
    parent = categories_tree
    parent_product = product
    parent_product.category = parent

    child = parent.children.first()
    child_product = child.products.first()

    for product in [child_product, parent_product]:
        product.publication_date = datetime.date.today()
        product.is_published = True
        product.save()
    return parent


@pytest.fixture
def non_default_category(db):  # pylint: disable=W0613
    return Category.objects.create(name="Not default", slug="not-default")


@pytest.fixture
def permission_manage_discounts():
    return Permission.objects.get(codename="manage_discounts")


@pytest.fixture
def permission_manage_gift_card():
    return Permission.objects.get(codename="manage_gift_card")


@pytest.fixture
def permission_manage_orders():
    return Permission.objects.get(codename="manage_orders")


@pytest.fixture
def permission_manage_checkouts():
    return Permission.objects.get(codename="manage_checkouts")


@pytest.fixture
def permission_manage_plugins():
    return Permission.objects.get(codename="manage_plugins")


@pytest.fixture
def permission_manage_apps():
    return Permission.objects.get(codename="manage_apps")


@pytest.fixture
def product_type(color_attribute, size_attribute):
    product_type = ProductType.objects.create(
        name="Default Type",
        slug="default-type",
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(color_attribute)
    product_type.variant_attributes.add(size_attribute)
    return product_type


@pytest.fixture
def product_type_without_variant():
    product_type = ProductType.objects.create(
        name="Type", slug="type", has_variants=False, is_shipping_required=True
    )
    return product_type


@pytest.fixture
def product(product_type, category, warehouse):
    product_attr = product_type.product_attributes.first()
    product_attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-11",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )

    associate_attribute_values_to_instance(product, product_attr, product_attr_value)

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(
        product=product, sku="123", cost_price=Money("1.00", "USD")
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)
    return product


@pytest.fixture
def product_with_single_variant(product_type, category, warehouse):
    product = Product.objects.create(
        name="Test product with single variant",
        slug="test-product-with-single-variant",
        price=Money("1.99", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )
    variant = ProductVariant.objects.create(
        product=product, sku="SKU_SINGLE_VARIANT", cost_price=Money("1.00", "USD")
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=101)
    return product


@pytest.fixture
def product_with_two_variants(product_type, category, warehouse):
    product = Product.objects.create(
        name="Test product with two variants",
        slug="test-product-with-two-variant",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )

    variants = [
        ProductVariant(
            product=product,
            sku=f"Product variant #{i}",
            cost_price=Money("1.00", "USD"),
        )
        for i in (1, 2)
    ]
    ProductVariant.objects.bulk_create(variants)
    Stock.objects.bulk_create(
        [
            Stock(warehouse=warehouse, product_variant=variant, quantity=10,)
            for variant in variants
        ]
    )

    return product


@pytest.fixture
def product_with_variant_with_two_attributes(
    color_attribute, size_attribute, category, warehouse
):
    product_type = ProductType.objects.create(
        name="Type with two variants",
        slug="two-variants",
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.variant_attributes.add(color_attribute)
    product_type.variant_attributes.add(size_attribute)

    product = Product.objects.create(
        name="Test product with two variants",
        slug="test-product-with-two-variant",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )

    variant = ProductVariant.objects.create(
        product=product, sku="prodVar1", cost_price=Money("1.00", "USD")
    )

    associate_attribute_values_to_instance(
        variant, color_attribute, color_attribute.values.first()
    )
    associate_attribute_values_to_instance(
        variant, size_attribute, size_attribute.values.first()
    )

    return product


@pytest.fixture
def product_with_multiple_values_attributes(product, product_type, category) -> Product:

    attribute = Attribute.objects.create(
        slug="modes", name="Available Modes", input_type=AttributeInputType.MULTISELECT
    )

    attr_val_1 = AttributeValue.objects.create(
        attribute=attribute, name="Eco Mode", slug="eco"
    )
    attr_val_2 = AttributeValue.objects.create(
        attribute=attribute, name="Performance Mode", slug="power"
    )

    product_type.product_attributes.clear()
    product_type.product_attributes.add(attribute)

    associate_attribute_values_to_instance(product, attribute, attr_val_1, attr_val_2)
    return product


@pytest.fixture
def product_with_default_variant(product_type_without_variant, category, warehouse):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-3",
        price=Money(10, "USD"),
        product_type=product_type_without_variant,
        category=category,
        is_published=True,
    )
    variant = ProductVariant.objects.create(
        product=product, sku="1234", track_inventory=True
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=100)
    return product


@pytest.fixture
def variant_without_inventory_tracking(
    product_type_without_variant, category, warehouse
):
    product = Product.objects.create(
        name="Test product without inventory tracking",
        slug="test-product-without-tracking",
        price=Money(10, "USD"),
        product_type=product_type_without_variant,
        category=category,
        is_published=True,
    )
    variant = ProductVariant.objects.create(
        product=product, sku="tracking123", track_inventory=False
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=0)
    return variant


@pytest.fixture
def variant(product) -> ProductVariant:
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_A", cost_price=Money(1, "USD")
    )
    return product_variant


@pytest.fixture
def variant_with_many_stocks(variant, warehouses_with_shipping_zone):
    warehouses = warehouses_with_shipping_zone
    Stock.objects.create(warehouse=warehouses[0], product_variant=variant, quantity=4)
    Stock.objects.create(warehouse=warehouses[1], product_variant=variant, quantity=3)
    return variant


@pytest.fixture
def product_variant_list(product):
    return list(
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(product=product, sku="1"),
                ProductVariant(product=product, sku="2"),
                ProductVariant(product=product, sku="3"),
            ]
        )
    )


@pytest.fixture
def product_without_shipping(category, warehouse):
    product_type = ProductType.objects.create(
        name="Type with no shipping",
        slug="no-shipping",
        has_variants=False,
        is_shipping_required=False,
    )
    product = Product.objects.create(
        name="Test product",
        slug="test-product-4",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_B")
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=1)
    return product


@pytest.fixture
def product_without_category(product):
    product.category = None
    product.is_published = False
    product.save()
    return product


@pytest.fixture
def product_list(product_type, category, warehouse):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    products = list(
        Product.objects.bulk_create(
            [
                Product(
                    pk=1486,
                    name="Test product 1",
                    slug="test-product-a",
                    price=Money(10, "USD"),
                    category=category,
                    product_type=product_type,
                    is_published=True,
                ),
                Product(
                    pk=1487,
                    name="Test product 2",
                    slug="test-product-b",
                    price=Money(20, "USD"),
                    category=category,
                    product_type=product_type,
                    is_published=False,
                ),
                Product(
                    pk=1489,
                    name="Test product 3",
                    slug="test-product-c",
                    price=Money(30, "USD"),
                    category=category,
                    product_type=product_type,
                    is_published=True,
                ),
            ]
        )
    )
    variants = list(
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(
                    product=products[0],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
                ProductVariant(
                    product=products[1],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
                ProductVariant(
                    product=products[2],
                    sku=str(uuid.uuid4()).replace("-", ""),
                    track_inventory=True,
                ),
            ]
        )
    )
    stocks = []
    for variant in variants:
        stocks.append(Stock(warehouse=warehouse, product_variant=variant, quantity=100))
    Stock.objects.bulk_create(stocks)

    for product in products:
        associate_attribute_values_to_instance(product, product_attr, attr_value)

    return products


@pytest.fixture
def product_list_unpublished(product_list):
    products = Product.objects.filter(pk__in=[product.pk for product in product_list])
    products.update(is_published=False)
    return products


@pytest.fixture
def product_list_published(product_list):
    products = Product.objects.filter(pk__in=[product.pk for product in product_list])
    products.update(is_published=True)
    return products


@pytest.fixture
def order_list(customer_user):
    address = customer_user.default_billing_address.get_copy()
    data = {
        "billing_address": address,
        "user": customer_user,
        "user_email": customer_user.email,
    }
    order = Order.objects.create(**data)
    order1 = Order.objects.create(**data)
    order2 = Order.objects.create(**data)

    return [order, order1, order2]


@pytest.fixture
def product_with_image(product, image, media_root):
    ProductImage.objects.create(product=product, image=image)
    return product


@pytest.fixture
def unavailable_product(product_type, category):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-5",
        price=Money("10.00", "USD"),
        product_type=product_type,
        is_published=False,
        category=category,
    )
    return product


@pytest.fixture
def unavailable_product_with_variant(product_type, category, warehouse):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-6",
        price=Money("10.00", "USD"),
        product_type=product_type,
        is_published=False,
        category=category,
    )

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(
        product=product, sku="123", cost_price=Money(1, "USD")
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)
    return product


@pytest.fixture
def product_with_images(product_type, category, media_root):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-7",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )
    file_mock_0 = MagicMock(spec=File, name="FileMock0")
    file_mock_0.name = "image0.jpg"
    file_mock_1 = MagicMock(spec=File, name="FileMock1")
    file_mock_1.name = "image1.jpg"
    product.images.create(image=file_mock_0)
    product.images.create(image=file_mock_1)
    return product


@pytest.fixture
def voucher(db):  # pylint: disable=W0613
    return Voucher.objects.create(code="mirumee", discount_value=20)


@pytest.fixture
def voucher_percentage(db):
    return Voucher.objects.create(
        code="mirumee",
        discount_value=10,
        discount_value_type=DiscountValueType.PERCENTAGE,
    )


@pytest.fixture
def voucher_specific_product_type(voucher_percentage):
    voucher_percentage.type = VoucherType.SPECIFIC_PRODUCT
    voucher_percentage.save()
    return voucher_percentage


@pytest.fixture
def voucher_with_high_min_spent_amount():
    return Voucher.objects.create(
        code="mirumee", discount_value=10, min_spent=Money(1_000_000, "USD")
    )


@pytest.fixture
def voucher_shipping_type():
    return Voucher.objects.create(
        code="mirumee", discount_value=10, type=VoucherType.SHIPPING, countries="IS"
    )


@pytest.fixture
def voucher_free_shipping(voucher_percentage):
    voucher_percentage.type = VoucherType.SHIPPING
    voucher_percentage.discount_value = 100
    voucher_percentage.save()
    return voucher_percentage


@pytest.fixture
def voucher_customer(voucher, customer_user):
    email = customer_user.email
    return VoucherCustomer.objects.create(voucher=voucher, customer_email=email)


@pytest.fixture
def order_line(order, variant):
    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    return order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=3,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
    )


@pytest.fixture
def order_line_with_allocation_in_many_stocks(customer_user, variant_with_many_stocks):
    address = customer_user.default_billing_address.get_copy()
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")

    order = Order.objects.create(
        billing_address=address, user_email=customer_user.email, user=customer_user
    )

    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order_line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=2,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
    )

    Allocation.objects.bulk_create(
        [
            Allocation(order_line=order_line, stock=stocks[0], quantity_allocated=2),
            Allocation(order_line=order_line, stock=stocks[1], quantity_allocated=1),
        ]
    )

    return order_line


@pytest.fixture
def gift_card(customer_user, staff_user):
    return GiftCard.objects.create(
        code="mirumee_giftcard",
        user=customer_user,
        initial_balance=Money(10, "USD"),
        current_balance=Money(10, "USD"),
    )


@pytest.fixture
def gift_card_used(staff_user):
    return GiftCard.objects.create(
        code="gift_card_used",
        initial_balance=Money(150, "USD"),
        current_balance=Money(100, "USD"),
    )


@pytest.fixture
def gift_card_created_by_staff(staff_user):
    return GiftCard.objects.create(
        code="mirumee_staff",
        initial_balance=Money(5, "USD"),
        current_balance=Money(5, "USD"),
    )


@pytest.fixture
def order_with_lines(order, product_type, category, shipping_zone, warehouse):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-8",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )
    variant = ProductVariant.objects.create(
        product=product, sku="SKU_A", cost_price=Money(1, "USD")
    )
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=3,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    product = Product.objects.create(
        name="Test product 2",
        slug="test-product-9",
        price=Money("20.00", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )
    variant = ProductVariant.objects.create(
        product=product, sku="SKU_B", cost_price=Money(2, "USD")
    )
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=2
    )

    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=2,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    order.shipping_address = order.billing_address.get_copy()
    method = shipping_zone.shipping_methods.get()
    order.shipping_method_name = method.name
    order.shipping_method = method

    net = method.get_total()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.shipping_price = TaxedMoney(net=net, gross=gross)
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_with_line_without_inventory_tracking(
    order, variant_without_inventory_tracking
):
    variant = variant_without_inventory_tracking
    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=3,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
    )

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_events(order):
    for event_type, _ in OrderEvents.CHOICES:
        OrderEvent.objects.create(type=event_type, order=order)


@pytest.fixture
def fulfilled_order(order_with_lines):
    order = order_with_lines
    fulfillment = order.fulfillments.create(tracking_number="123")
    line_1 = order.lines.first()
    stock_1 = line_1.allocations.get().stock
    warehouse_1_pk = stock_1.warehouse.pk
    line_2 = order.lines.last()
    stock_2 = line_2.allocations.get().stock
    warehouse_2_pk = stock_2.warehouse.pk
    fulfillment.lines.create(order_line=line_1, quantity=line_1.quantity, stock=stock_1)
    fulfill_order_line(line_1, line_1.quantity, warehouse_1_pk)
    fulfillment.lines.create(order_line=line_2, quantity=line_2.quantity, stock=stock_2)
    fulfill_order_line(line_2, line_2.quantity, warehouse_2_pk)
    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def fulfilled_order_without_inventory_tracking(
    order_with_line_without_inventory_tracking,
):
    order = order_with_line_without_inventory_tracking
    fulfillment = order.fulfillments.create(tracking_number="123")
    line = order.lines.first()
    stock = line.variant.stocks.get()
    warehouse_pk = stock.warehouse.pk
    fulfillment.lines.create(order_line=line, quantity=line.quantity, stock=stock)
    fulfill_order_line(line, line.quantity, warehouse_pk)
    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def fulfilled_order_with_cancelled_fulfillment(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.create()
    line_1 = fulfilled_order.lines.first()
    line_2 = fulfilled_order.lines.last()
    fulfillment.lines.create(order_line=line_1, quantity=line_1.quantity)
    fulfillment.lines.create(order_line=line_2, quantity=line_2.quantity)
    fulfillment.status = FulfillmentStatus.CANCELED
    fulfillment.save()
    return fulfilled_order


@pytest.fixture
def fulfilled_order_with_all_cancelled_fulfillments(
    fulfilled_order, staff_user, warehouse
):
    fulfillment = fulfilled_order.fulfillments.get()
    cancel_fulfillment(fulfillment, staff_user, warehouse)
    return fulfilled_order


@pytest.fixture
def fulfillment(fulfilled_order):
    return fulfilled_order.fulfillments.first()


@pytest.fixture
def draft_order(order_with_lines):
    Allocation.objects.filter(order_line__order=order_with_lines).delete()
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.save(update_fields=["status"])
    return order_with_lines


@pytest.fixture
def draft_order_without_inventory_tracking(order_with_line_without_inventory_tracking):
    order_with_line_without_inventory_tracking.status = OrderStatus.DRAFT
    order_with_line_without_inventory_tracking.save(update_fields=["status"])
    return order_with_line_without_inventory_tracking


@pytest.fixture
def payment_txn_preauth(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.AUTH,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def payment_txn_captured(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def payment_txn_to_confirm(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.to_confirm = True
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
        action_required=True,
    )
    return payment


@pytest.fixture
def payment_txn_refunded(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.is_active = False
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.REFUND,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def payment_not_authorized(payment_dummy):
    payment_dummy.is_active = False
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def sale(product, category, collection):
    sale = Sale.objects.create(name="Sale", value=5)
    sale.products.add(product)
    sale.categories.add(category)
    sale.collections.add(collection)
    return sale


@pytest.fixture
def discount_info(category, collection, sale):
    return DiscountInfo(
        sale=sale,
        product_ids=set(),
        category_ids={category.id},  # assumes this category does not have children
        collection_ids={collection.id},
    )


@pytest.fixture
def authorization_backend_name():
    return AuthenticationBackends.FACEBOOK


@pytest.fixture
def authorization_key(site_settings, authorization_backend_name):
    return AuthorizationKey.objects.create(
        site_settings=site_settings,
        name=authorization_backend_name,
        key="Key",
        password="Password",
    )


@pytest.fixture
def permission_manage_staff():
    return Permission.objects.get(codename="manage_staff")


@pytest.fixture
def permission_manage_products():
    return Permission.objects.get(codename="manage_products")


@pytest.fixture
def permission_manage_shipping():
    return Permission.objects.get(codename="manage_shipping")


@pytest.fixture
def permission_manage_users():
    return Permission.objects.get(codename="manage_users")


@pytest.fixture
def permission_manage_settings():
    return Permission.objects.get(codename="manage_settings")


@pytest.fixture
def permission_manage_menus():
    return Permission.objects.get(codename="manage_menus")


@pytest.fixture
def permission_manage_pages():
    return Permission.objects.get(codename="manage_pages")


@pytest.fixture
def permission_manage_translations():
    return Permission.objects.get(codename="manage_translations")


@pytest.fixture
def permission_manage_webhooks():
    return Permission.objects.get(codename="manage_webhooks")


@pytest.fixture
def permission_group_manage_users(permission_manage_users, staff_users):
    group = Group.objects.create(name="Manage user groups.")
    group.permissions.add(permission_manage_users)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def collection(db):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        is_published=True,
        description="Test description",
    )
    return collection


@pytest.fixture
def collection_with_products(db, collection, product_list_published):
    collection.products.set(list(product_list_published))
    return product_list_published


@pytest.fixture
def collection_with_image(db, image, media_root):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        description="Test description",
        background_image=image,
        is_published=True,
    )
    return collection


@pytest.fixture
def collection_list(db):
    collections = Collection.objects.bulk_create(
        [
            Collection(name="Collection 1", slug="collection-1", is_published="True"),
            Collection(name="Collection 2", slug="collection-2", is_published="True"),
            Collection(name="Collection 3", slug="collection-3", is_published="True"),
        ]
    )
    return collections


@pytest.fixture
def collection_list_unpublished(collection_list):
    collections = Collection.objects.filter(
        pk__in=[collection.pk for collection in collection_list]
    )
    collections.update(is_published=False)
    return collections


@pytest.fixture
def draft_collection(db):
    collection = Collection.objects.create(
        name="Draft collection", slug="draft-collection", is_published=False
    )
    return collection


@pytest.fixture
def unpublished_collection():
    collection = Collection.objects.create(
        name="Unpublished collection", slug="unpublished-collection", is_published=False
    )
    return collection


@pytest.fixture
def page(db):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "content": "test content",
        "is_published": True,
    }
    page = Page.objects.create(**data)
    return page


@pytest.fixture
def page_list(db):
    data_1 = {
        "slug": "test-url",
        "title": "Test page",
        "content": "test content",
        "is_published": True,
    }
    data_2 = {
        "slug": "test-url-2",
        "title": "Test page",
        "content": "test content",
        "is_published": True,
    }
    pages = Page.objects.bulk_create([Page(**data_1), Page(**data_2)])
    return pages


@pytest.fixture
def page_list_unpublished(db):
    pages = Page.objects.bulk_create(
        [
            Page(slug="page-1", title="Page 1", is_published=False),
            Page(slug="page-2", title="Page 2", is_published=False),
            Page(slug="page-3", title="Page 3", is_published=False),
        ]
    )
    return pages


@pytest.fixture
def model_form_class():
    mocked_form_class = MagicMock(name="test", spec=ModelForm)
    mocked_form_class._meta = Mock(name="_meta")
    mocked_form_class._meta.model = "test_model"
    mocked_form_class._meta.fields = "test_field"
    return mocked_form_class


@pytest.fixture
def menu(db):
    return Menu.objects.get_or_create(name="test-navbar", json_content={})[0]


@pytest.fixture
def menu_item(menu):
    item = MenuItem.objects.create(menu=menu, name="Link 1", url="http://example.com/")
    update_menu(menu)
    return item


@pytest.fixture
def menu_item_list(menu):
    menu_item_1 = MenuItem.objects.create(menu=menu, name="Link 1")
    menu_item_2 = MenuItem.objects.create(menu=menu, name="Link 2")
    menu_item_3 = MenuItem.objects.create(menu=menu, name="Link 3")
    update_menu(menu)
    return menu_item_1, menu_item_2, menu_item_3


@pytest.fixture
def menu_with_items(menu, category, collection):
    menu.items.create(name="Link 1", url="http://example.com/")
    menu_item = menu.items.create(name="Link 2", url="http://example.com/")
    menu.items.create(name=category.name, category=category, parent=menu_item)
    menu.items.create(name=collection.name, collection=collection, parent=menu_item)
    update_menu(menu)
    return menu


@pytest.fixture
def translated_variant_fr(product):
    attribute = product.product_type.variant_attributes.first()
    return AttributeTranslation.objects.create(
        language_code="fr", attribute=attribute, name="Name tranlsated to french"
    )


@pytest.fixture
def translated_attribute(product):
    attribute = product.product_type.product_attributes.first()
    return AttributeTranslation.objects.create(
        language_code="fr", attribute=attribute, name="French attribute name"
    )


@pytest.fixture
def translated_attribute_value(pink_attribute_value):
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=pink_attribute_value,
        name="French attribute value name",
    )


@pytest.fixture
def voucher_translation_fr(voucher):
    return VoucherTranslation.objects.create(
        language_code="fr", voucher=voucher, name="French name"
    )


@pytest.fixture
def product_translation_fr(product):
    return ProductTranslation.objects.create(
        language_code="fr",
        product=product,
        name="French name",
        description="French description",
    )


@pytest.fixture
def variant_translation_fr(variant):
    return ProductVariantTranslation.objects.create(
        language_code="fr", product_variant=variant, name="French product variant name"
    )


@pytest.fixture
def collection_translation_fr(collection):
    return CollectionTranslation.objects.create(
        language_code="fr",
        collection=collection,
        name="French collection name",
        description="French description",
    )


@pytest.fixture
def category_translation_fr(category):
    return CategoryTranslation.objects.create(
        language_code="fr",
        category=category,
        name="French category name",
        description="French category description",
    )


@pytest.fixture
def page_translation_fr(page):
    return PageTranslation.objects.create(
        language_code="fr",
        page=page,
        title="French page title",
        content="French page content",
    )


@pytest.fixture
def shipping_method_translation_fr(shipping_method):
    return ShippingMethodTranslation.objects.create(
        language_code="fr",
        shipping_method=shipping_method,
        name="French shipping method name",
    )


@pytest.fixture
def sale_translation_fr(sale):
    return SaleTranslation.objects.create(
        language_code="fr", sale=sale, name="French sale name"
    )


@pytest.fixture
def menu_item_translation_fr(menu_item):
    return MenuItemTranslation.objects.create(
        language_code="fr", menu_item=menu_item, name="French manu item name"
    )


@pytest.fixture
def payment_dummy(db, order_with_lines):
    return Payment.objects.create(
        gateway="mirumee.payments.dummy",
        order=order_with_lines,
        is_active=True,
        cc_first_digits="4111",
        cc_last_digits="1111",
        cc_brand="VISA",
        cc_exp_month=12,
        cc_exp_year=2027,
        total=order_with_lines.total.gross.amount,
        currency=order_with_lines.total.gross.currency,
        billing_first_name=order_with_lines.billing_address.first_name,
        billing_last_name=order_with_lines.billing_address.last_name,
        billing_company_name=order_with_lines.billing_address.company_name,
        billing_address_1=order_with_lines.billing_address.street_address_1,
        billing_address_2=order_with_lines.billing_address.street_address_2,
        billing_city=order_with_lines.billing_address.city,
        billing_postal_code=order_with_lines.billing_address.postal_code,
        billing_country_code=order_with_lines.billing_address.country.code,
        billing_country_area=order_with_lines.billing_address.country_area,
        billing_email=order_with_lines.user_email,
    )


@pytest.fixture
def digital_content(category, media_root, warehouse) -> DigitalContent:
    product_type = ProductType.objects.create(
        name="Digital Type",
        slug="digital-type",
        has_variants=True,
        is_shipping_required=False,
        is_digital=True,
    )
    product = Product.objects.create(
        name="Test digital product",
        slug="test-digital-product",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
        is_published=True,
    )
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_554", cost_price=Money(1, "USD")
    )
    Stock.objects.create(
        product_variant=product_variant, warehouse=warehouse, quantity=5,
    )

    assert product_variant.is_digital()

    image_file, image_name = create_image()
    d_content = DigitalContent.objects.create(
        content_file=image_file,
        product_variant=product_variant,
        use_default_settings=True,
    )
    return d_content


@pytest.fixture
def digital_content_url(digital_content, order_line):
    return DigitalContentUrl.objects.create(content=digital_content, line=order_line)


@pytest.fixture
def media_root(tmpdir, settings):
    settings.MEDIA_ROOT = str(tmpdir.mkdir("media"))


@pytest.fixture
def description_json():
    return {
        "blocks": [
            {
                "key": "",
                "data": {},
                "text": "E-commerce for the PWA era",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": (
                    "A modular, high performance e-commerce storefront "
                    "built with GraphQL, Django, and ReactJS."
                ),
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": (
                    "Saleor is a rapidly-growing open source e-commerce platform "
                    "that has served high-volume companies from branches "
                    "like publishing and apparel since 2012. Based on Python "
                    "and Django, the latest major update introduces a modular "
                    "front end with a GraphQL API and storefront and dashboard "
                    "written in React to make Saleor a full-functionality "
                    "open source e-commerce."
                ),
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "Get Saleor today!",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [{"key": 0, "length": 17, "offset": 0}],
                "inlineStyleRanges": [],
            },
        ],
        "entityMap": {
            "0": {
                "data": {"href": "https://github.com/mirumee/saleor"},
                "type": "LINK",
                "mutability": "MUTABLE",
            }
        },
    }


@pytest.fixture
def other_description_json():
    return {
        "blocks": [
            {
                "key": "",
                "data": {},
                "text": "A GRAPHQL-FIRST ECOMMERCE PLATFORM FOR PERFECTIONISTS",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": (
                    "Saleor is powered by a GraphQL server running on "
                    "top of Python 3 and a Django 2 framework."
                ),
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
        ],
        "entityMap": {},
    }


@pytest.fixture
def app(db):
    return App.objects.create(name="Sample app objects", is_active=True)


@pytest.fixture
def webhook(app):
    webhook = Webhook.objects.create(
        name="Simple webhook", app=app, target_url="http://www.example.com/test"
    )
    webhook.events.create(event_type=WebhookEventType.ORDER_CREATED)
    return webhook


@pytest.fixture
def fake_payment_interface(mocker):
    return mocker.Mock(spec=PaymentInterface)


@pytest.fixture
def mock_get_manager(mocker, fake_payment_interface):
    mgr = mocker.patch(
        "saleor.payment.gateway.get_plugins_manager",
        autospec=True,
        return_value=fake_payment_interface,
    )
    yield fake_payment_interface
    mgr.assert_called_once()


@pytest.fixture
def staff_notification_recipient(db, staff_user):
    return StaffNotificationRecipient.objects.create(active=True, user=staff_user)


@pytest.fixture
def customer_wishlist(customer_user):
    return Wishlist.objects.create(user=customer_user)


@pytest.fixture
def customer_wishlist_item(customer_wishlist, product_with_single_variant):
    product = product_with_single_variant
    assert product.variants.count() == 1
    variant = product.variants.first()
    item = customer_wishlist.add_variant(variant)
    return item


@pytest.fixture
def customer_wishlist_item_with_two_variants(
    customer_wishlist, product_with_two_variants
):
    product = product_with_two_variants
    assert product.variants.count() == 2
    [variant_1, variant_2] = product.variants.all()
    item = customer_wishlist.add_variant(variant_1)
    item.variants.add(variant_2)
    return item


@pytest.fixture
def warehouse(address, shipping_zone):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Example Warehouse",
        slug="example-warehouse",
        email="test@example.com",
    )
    warehouse.shipping_zones.add(shipping_zone)
    warehouse.save()
    return warehouse


@pytest.fixture
def warehouses(address):
    return Warehouse.objects.bulk_create(
        [
            Warehouse(
                address=address.get_copy(),
                name="Warehouse1",
                slug="warehouse1",
                email="warehouse1@example.com",
            ),
            Warehouse(
                address=address.get_copy(),
                name="Warehouse2",
                slug="warehouse2",
                email="warehouse2@example.com",
            ),
        ]
    )


@pytest.fixture
def warehouses_with_shipping_zone(warehouses, shipping_zone):
    warehouses[0].shipping_zones.add(shipping_zone)
    warehouses[1].shipping_zones.add(shipping_zone)
    return warehouses


@pytest.fixture
def warehouse_no_shipping_zone(address):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Warehouse withot shipping zone",
        email="test2@example.com",
    )
    return warehouse


@pytest.fixture
def stock(variant, warehouse):
    return Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=15
    )


@pytest.fixture
def allocation(order_line, stock):
    return Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=order_line.quantity
    )


@pytest.fixture
def allocations(order_list, stock):
    variant = stock.product_variant
    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    lines = OrderLine.objects.bulk_create(
        [
            OrderLine(
                order=order_list[0],
                variant=variant,
                quantity=1,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                is_shipping_required=variant.is_shipping_required(),
                unit_price=TaxedMoney(net=net, gross=gross),
                tax_rate=23,
            ),
            OrderLine(
                order=order_list[1],
                variant=variant,
                quantity=2,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                is_shipping_required=variant.is_shipping_required(),
                unit_price=TaxedMoney(net=net, gross=gross),
                tax_rate=23,
            ),
            OrderLine(
                order=order_list[2],
                variant=variant,
                quantity=4,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                is_shipping_required=variant.is_shipping_required(),
                unit_price=TaxedMoney(net=net, gross=gross),
                tax_rate=23,
            ),
        ]
    )
    return Allocation.objects.bulk_create(
        [
            Allocation(
                order_line=lines[0], stock=stock, quantity_allocated=lines[0].quantity
            ),
            Allocation(
                order_line=lines[1], stock=stock, quantity_allocated=lines[1].quantity
            ),
            Allocation(
                order_line=lines[2], stock=stock, quantity_allocated=lines[2].quantity
            ),
        ]
    )
