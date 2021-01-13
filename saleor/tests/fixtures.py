import datetime
import uuid
from contextlib import contextmanager
from decimal import Decimal
from functools import partial
from io import BytesIO
from typing import List, Optional
from unittest.mock import MagicMock, Mock

import graphene
import pytest
import pytz
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.forms import ModelForm
from django.test.utils import CaptureQueriesContext as BaseCaptureQueriesContext
from django.utils import timezone
from django_countries import countries
from PIL import Image
from prices import Money, TaxedMoney

from ..account.models import Address, StaffNotificationRecipient, User
from ..app.models import App, AppInstallation
from ..app.types import AppType
from ..attribute import AttributeEntityType, AttributeInputType, AttributeType
from ..attribute.models import (
    Attribute,
    AttributeTranslation,
    AttributeValue,
    AttributeValueTranslation,
)
from ..attribute.utils import associate_attribute_values_to_instance
from ..checkout.models import Checkout
from ..checkout.utils import add_variant_to_checkout
from ..core import JobStatus
from ..core.payments import PaymentInterface
from ..csv.events import ExportEvents
from ..csv.models import ExportEvent, ExportFile
from ..discount import DiscountInfo, DiscountValueType, VoucherType
from ..discount.models import (
    Sale,
    SaleChannelListing,
    SaleTranslation,
    Voucher,
    VoucherChannelListing,
    VoucherCustomer,
    VoucherTranslation,
)
from ..giftcard.models import GiftCard
from ..menu.models import Menu, MenuItem, MenuItemTranslation
from ..order import OrderStatus
from ..order.actions import cancel_fulfillment, fulfill_order_line
from ..order.events import OrderEvents
from ..order.models import FulfillmentStatus, Order, OrderEvent, OrderLine
from ..order.utils import recalculate_order
from ..page.models import Page, PageTranslation, PageType
from ..payment import ChargeStatus, TransactionKind
from ..payment.interface import GatewayConfig, PaymentData
from ..payment.models import Payment
from ..plugins.models import PluginConfiguration
from ..plugins.vatlayer.plugin import VatlayerPlugin
from ..product.models import (
    Category,
    CategoryTranslation,
    Collection,
    CollectionChannelListing,
    CollectionTranslation,
    DigitalContent,
    DigitalContentUrl,
    Product,
    ProductChannelListing,
    ProductImage,
    ProductTranslation,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
    ProductVariantTranslation,
    VariantImage,
)
from ..product.tests.utils import create_image
from ..shipping.models import (
    ShippingMethod,
    ShippingMethodChannelListing,
    ShippingMethodTranslation,
    ShippingMethodType,
    ShippingZone,
)
from ..site.models import SiteSettings
from ..warehouse.models import Allocation, Stock, Warehouse
from ..webhook.event_types import WebhookEventType
from ..webhook.models import Webhook
from ..wishlist.models import Wishlist


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


@pytest.fixture
def setup_vatlayer(settings):
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    data = {
        "active": True,
        "configuration": [
            {"name": "Access key", "value": "vatlayer_access_key"},
        ],
    }
    PluginConfiguration.objects.create(identifier=VatlayerPlugin.PLUGIN_ID, **data)
    return settings


@pytest.fixture(autouse=True)
def setup_dummy_gateways(settings):
    settings.PLUGINS = [
        "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin",
        "saleor.payment.gateways.dummy_credit_card.plugin.DummyCreditCardGatewayPlugin",
    ]
    return settings


@pytest.fixture
def sample_gateway(settings):
    settings.PLUGINS += [
        "saleor.plugins.tests.sample_plugins.ActiveDummyPaymentGateway"
    ]


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
        name=settings.DEFAULT_MENUS["top_menu_name"],
        slug=settings.DEFAULT_MENUS["top_menu_name"],
    )[0]
    secondary_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS["bottom_menu_name"],
        slug=settings.DEFAULT_MENUS["bottom_menu_name"],
    )[0]
    obj.top_menu = main_menu
    obj.bottom_menu = secondary_menu
    obj.save()
    return obj


@pytest.fixture
def checkout(db, channel_USD):
    checkout = Checkout.objects.create(
        currency=channel_USD.currency_code, channel=channel_USD
    )
    checkout.set_country("US", commit=True)
    return checkout


@pytest.fixture
def checkout_with_item(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    checkout.save()
    return checkout


@pytest.fixture
def checkouts_list(channel_USD, channel_PLN):
    checkouts_usd = Checkout.objects.bulk_create(
        [
            Checkout(currency=channel_USD.currency_code, channel=channel_USD),
            Checkout(currency=channel_USD.currency_code, channel=channel_USD),
            Checkout(currency=channel_USD.currency_code, channel=channel_USD),
        ]
    )
    checkouts_pln = Checkout.objects.bulk_create(
        [
            Checkout(currency=channel_PLN.currency_code, channel=channel_PLN),
            Checkout(currency=channel_PLN.currency_code, channel=channel_PLN),
        ]
    )
    return [*checkouts_pln, *checkouts_usd]


@pytest.fixture
def checkouts_assigned_to_customer(channel_USD, channel_PLN, customer_user):
    return Checkout.objects.bulk_create(
        [
            Checkout(
                currency=channel_USD.currency_code,
                channel=channel_USD,
                user=customer_user,
            ),
            Checkout(
                currency=channel_PLN.currency_code,
                channel=channel_PLN,
                user=customer_user,
            ),
        ]
    )


@pytest.fixture
def checkout_ready_to_complete(checkout_with_item, address, shipping_method, gift_card):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
    checkout_with_item.gift_cards.add(gift_card)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_digital_item(checkout, digital_content):
    """Create a checkout with a digital line."""
    variant = digital_content.product_variant
    add_variant_to_checkout(checkout, variant, 1)
    checkout.email = "customer@example.com"
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_shipping_required(checkout_with_item, product):
    checkout = checkout_with_item
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    checkout.save()
    return checkout


@pytest.fixture
def other_shipping_method(shipping_zone, channel_USD):
    method = ShippingMethod.objects.create(
        name="DPD",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.create(
        channel=channel_USD,
        shipping_method=method,
        minimum_order_price=Money(0, "USD"),
        price=Money(9, "USD"),
    )
    return method


@pytest.fixture
def checkout_without_shipping_required(checkout, product_without_shipping):
    variant = product_without_shipping.variants.get()
    add_variant_to_checkout(checkout, variant, 1)
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
    checkout, variant_without_inventory_tracking, address, shipping_method
):
    variant = variant_without_inventory_tracking
    add_variant_to_checkout(checkout, variant, 1)
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.store_value_in_metadata(items={"accepted": "true"})
    checkout.store_value_in_private_metadata(items={"accepted": "false"})
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
def checkout_with_payments(checkout):
    Payment.objects.bulk_create(
        [
            Payment(
                gateway="mirumee.payments.dummy", is_active=True, checkout=checkout
            ),
            Payment(
                gateway="mirumee.payments.dummy", is_active=False, checkout=checkout
            ),
        ]
    )
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
        phone="+40123123123",
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
def user_checkout(customer_user, channel_USD):
    checkout = Checkout.objects.create(
        user=customer_user,
        channel=channel_USD,
        billing_address=customer_user.default_billing_address,
        shipping_address=customer_user.default_shipping_address,
        note="Test notes",
        currency="USD",
    )
    return checkout


@pytest.fixture
def user_checkout_PLN(customer_user, channel_PLN):
    checkout = Checkout.objects.create(
        user=customer_user,
        channel=channel_PLN,
        billing_address=customer_user.default_billing_address,
        shipping_address=customer_user.default_shipping_address,
        note="Test notes",
        currency="PLN",
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
def order(customer_user, channel_USD):
    address = customer_user.default_billing_address.get_copy()
    return Order.objects.create(
        billing_address=address,
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
    )


@pytest.fixture
def order_unconfirmed(order):
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    return order


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
def shipping_zone(db, channel_USD):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(
        name="Europe", countries=[code for code, name in countries]
    )
    method = shipping_zone.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.create(
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_method=method,
        minimum_order_price=Money(0, channel_USD.currency_code),
        price=Money(10, channel_USD.currency_code),
    )
    return shipping_zone


@pytest.fixture
def shipping_zones(db, channel_USD, channel_PLN):
    shipping_zone_poland, shipping_zone_usa = ShippingZone.objects.bulk_create(
        [
            ShippingZone(name="Poland", countries=["PL"]),
            ShippingZone(name="USA", countries=["US"]),
        ]
    )
    method = shipping_zone_poland.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    second_method = shipping_zone_usa.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.bulk_create(
        [
            ShippingMethodChannelListing(
                channel=channel_USD,
                shipping_method=method,
                minimum_order_price=Money(0, "USD"),
                price=Money(10, "USD"),
                currency=channel_USD.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_USD,
                shipping_method=second_method,
                minimum_order_price=Money(0, "USD"),
                currency=channel_USD.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_PLN,
                shipping_method=method,
                minimum_order_price=Money(0, "PLN"),
                price=Money(40, "PLN"),
                currency=channel_PLN.currency_code,
            ),
            ShippingMethodChannelListing(
                channel=channel_PLN,
                shipping_method=second_method,
                minimum_order_price=Money(0, "PLN"),
                currency=channel_PLN.currency_code,
            ),
        ]
    )
    return [shipping_zone_poland, shipping_zone_usa]


@pytest.fixture
def shipping_zone_without_countries(db, channel_USD):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(name="Europe", countries=[])
    method = shipping_zone.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.create(
        channel=channel_USD,
        shipping_method=method,
        minimum_order_price=Money(0, "USD"),
        price=Money(10, "USD"),
    )
    return shipping_zone


@pytest.fixture
def shipping_method(shipping_zone, channel_USD):
    method = ShippingMethod.objects.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
        maximum_delivery_days=10,
        minimum_delivery_days=5,
    )
    ShippingMethodChannelListing.objects.create(
        shipping_method=method,
        channel=channel_USD,
        minimum_order_price=Money(0, "USD"),
        price=Money(10, "USD"),
    )
    return method


@pytest.fixture
def shipping_method_excldued_by_zip_code(shipping_method):
    shipping_method.zip_code_rules.create(start="HB2", end="HB6")
    return shipping_method


@pytest.fixture
def shipping_method_channel_PLN(shipping_zone, channel_PLN):
    method = ShippingMethod.objects.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
    )
    ShippingMethodChannelListing.objects.create(
        shipping_method=method,
        channel=channel_PLN,
        minimum_order_price=Money(0, channel_PLN.currency_code),
        price=Money(10, channel_PLN.currency_code),
        currency=channel_PLN.currency_code,
    )
    return method


@pytest.fixture
def color_attribute(db):  # pylint: disable=W0613
    attribute = Attribute.objects.create(
        slug="color",
        name="Color",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="Red", slug="red")
    AttributeValue.objects.create(attribute=attribute, name="Blue", slug="blue")
    return attribute


@pytest.fixture
def color_attribute_without_values(db):  # pylint: disable=W0613
    return Attribute.objects.create(
        slug="color",
        name="Color",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )


@pytest.fixture
def pink_attribute_value(color_attribute):  # pylint: disable=W0613
    value = AttributeValue.objects.create(
        slug="pink", name="Pink", attribute=color_attribute, value="#FF69B4"
    )
    return value


@pytest.fixture
def size_attribute(db):  # pylint: disable=W0613
    attribute = Attribute.objects.create(
        slug="size",
        name="Size",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="Small", slug="small")
    AttributeValue.objects.create(attribute=attribute, name="Big", slug="big")
    return attribute


@pytest.fixture
def weight_attribute(db):
    attribute = Attribute.objects.create(
        slug="material",
        name="Material",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="Cotton", slug="cotton")
    AttributeValue.objects.create(
        attribute=attribute, name="Poliester", slug="poliester"
    )
    return attribute


@pytest.fixture
def file_attribute(db):
    attribute = Attribute.objects.create(
        slug="image",
        name="Image",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.FILE,
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.txt",
        slug="test_filetxt",
        file_url="http://mirumee.com/test_media/test_file.txt",
        content_type="text/plain",
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.jpeg",
        slug="test_filejpeg",
        file_url="http://mirumee.com/test_media/test_file.jpeg",
        content_type="image/jpeg",
    )
    return attribute


@pytest.fixture
def file_attribute_with_file_input_type_without_values(db):
    return Attribute.objects.create(
        slug="image",
        name="Image",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.FILE,
    )


@pytest.fixture
def product_type_page_reference_attribute(db):
    return Attribute.objects.create(
        slug="page-reference",
        name="Page reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PAGE,
    )


@pytest.fixture
def page_type_page_reference_attribute(db):
    return Attribute.objects.create(
        slug="page-reference",
        name="Page reference",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PAGE,
    )


@pytest.fixture
def product_type_product_reference_attribute(db):
    return Attribute.objects.create(
        slug="product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT,
    )


@pytest.fixture
def page_type_product_reference_attribute(db):
    return Attribute.objects.create(
        slug="product-reference",
        name="Product reference",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT,
    )


@pytest.fixture
def size_page_attribute(db):
    attribute = Attribute.objects.create(
        slug="page-size",
        name="Page size",
        type=AttributeType.PAGE_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="10", slug="10")
    AttributeValue.objects.create(attribute=attribute, name="15", slug="15")
    return attribute


@pytest.fixture
def tag_page_attribute(db):
    attribute = Attribute.objects.create(
        slug="tag",
        name="tag",
        type=AttributeType.PAGE_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="About", slug="about")
    AttributeValue.objects.create(attribute=attribute, name="Help", slug="help")
    return attribute


@pytest.fixture
def author_page_attribute(db):
    attribute = Attribute.objects.create(
        slug="author", name="author", type=AttributeType.PAGE_TYPE
    )
    AttributeValue.objects.create(
        attribute=attribute, name="Test author 1", slug="test-author-1"
    )
    AttributeValue.objects.create(
        attribute=attribute, name="Test author 2", slug="test-author-2"
    )
    return attribute


@pytest.fixture
def page_file_attribute(db):
    attribute = Attribute.objects.create(
        slug="image",
        name="Image",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.FILE,
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.txt",
        slug="test_filetxt",
        file_url="http://mirumee.com/test_media/test_file.txt",
        content_type="text/plain",
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.jpeg",
        slug="test_filejpeg",
        file_url="http://mirumee.com/test_media/test_file.jpeg",
        content_type="image/jpeg",
    )
    return attribute


@pytest.fixture
def product_type_attribute_list() -> List[Attribute]:
    return list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="size", name="Size", type=AttributeType.PRODUCT_TYPE),
                Attribute(
                    slug="weight", name="Weight", type=AttributeType.PRODUCT_TYPE
                ),
                Attribute(
                    slug="thickness", name="Thickness", type=AttributeType.PRODUCT_TYPE
                ),
            ]
        )
    )


@pytest.fixture
def page_type_attribute_list() -> List[Attribute]:
    return list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="size", name="Size", type=AttributeType.PAGE_TYPE),
                Attribute(slug="font", name="Weight", type=AttributeType.PAGE_TYPE),
                Attribute(
                    slug="margin", name="Thickness", type=AttributeType.PAGE_TYPE
                ),
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
def categories_tree(db, product_type, channel_USD):  # pylint: disable=W0613
    parent = Category.objects.create(name="Parent", slug="parent")
    parent.children.create(name="Child", slug="child")
    child = parent.children.first()

    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-10",
        product_type=product_type,
        category=child,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )

    associate_attribute_values_to_instance(product, product_attr, attr_value)
    return parent


@pytest.fixture
def categories_tree_with_published_products(
    categories_tree, product, channel_USD, channel_PLN
):
    parent = categories_tree
    parent_product = product
    parent_product.category = parent

    child = parent.children.first()
    child_product = child.products.first()

    product_list = [child_product, parent_product]

    ProductChannelListing.objects.filter(product__in=product_list).delete()
    product_channel_listings = []
    for product in product_list:
        product.save()
        product_channel_listings.append(
            ProductChannelListing(
                product=product,
                channel=channel_USD,
                publication_date=datetime.date.today(),
                is_published=True,
            )
        )
        product_channel_listings.append(
            ProductChannelListing(
                product=product,
                channel=channel_PLN,
                publication_date=datetime.date.today(),
                is_published=True,
            )
        )
    ProductChannelListing.objects.bulk_create(product_channel_listings)
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
def product(product_type, category, warehouse, channel_USD):
    product_attr = product_type.product_attributes.first()
    product_attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-11",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="10.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase=datetime.date(1999, 1, 1),
    )

    associate_attribute_values_to_instance(product, product_attr, product_attr_value)

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(product=product, sku="123")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)
    return product


@pytest.fixture
def product_with_collections(
    product, published_collection, unpublished_collection, collection
):
    product.collections.add(*[published_collection, unpublished_collection, collection])
    return product


@pytest.fixture
def product_available_in_many_channels(product, channel_PLN):
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_PLN,
        is_published=True,
    )
    variant = product.variants.get()
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(50),
        cost_price_amount=Decimal(1),
        currency=channel_PLN.currency_code,
    )
    return product


@pytest.fixture
def product_with_single_variant(product_type, category, warehouse, channel_USD):
    product = Product.objects.create(
        name="Test product with single variant",
        slug="test-product-with-single-variant",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date(1999, 1, 1),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_SINGLE_VARIANT")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(1.99),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=101)
    return product


@pytest.fixture
def product_with_two_variants(product_type, category, warehouse, channel_USD):
    product = Product.objects.create(
        name="Test product with two variants",
        slug="test-product-with-two-variant",
        product_type=product_type,
        category=category,
    )

    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date(1999, 1, 1),
    )

    variants = [
        ProductVariant(
            product=product,
            sku=f"Product variant #{i}",
        )
        for i in (1, 2)
    ]
    ProductVariant.objects.bulk_create(variants)
    variants_channel_listing = [
        ProductVariantChannelListing(
            variant=variant,
            channel=channel_USD,
            price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )
        for variant in variants
    ]
    ProductVariantChannelListing.objects.bulk_create(variants_channel_listing)
    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=warehouse,
                product_variant=variant,
                quantity=10,
            )
            for variant in variants
        ]
    )

    return product


@pytest.fixture
def product_with_variant_with_two_attributes(
    color_attribute, size_attribute, category, warehouse, channel_USD
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
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase=datetime.date(1999, 1, 1),
    )

    variant = ProductVariant.objects.create(product=product, sku="prodVar1")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )

    associate_attribute_values_to_instance(
        variant, color_attribute, color_attribute.values.first()
    )
    associate_attribute_values_to_instance(
        variant, size_attribute, size_attribute.values.first()
    )

    return product


@pytest.fixture
def product_with_variant_with_file_attribute(
    color_attribute, file_attribute, category, warehouse, channel_USD
):
    product_type = ProductType.objects.create(
        name="Type with variant and file attribute",
        slug="type-with-file-attribute",
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.variant_attributes.add(file_attribute)

    product = Product.objects.create(
        name="Test product with variant and file attribute",
        slug="test-product-with-variant-and-file-attribute",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase=datetime.date(1999, 1, 1),
    )

    variant = ProductVariant.objects.create(
        product=product,
        sku="prodVarTest",
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )

    associate_attribute_values_to_instance(
        variant, file_attribute, file_attribute.values.first()
    )

    return product


@pytest.fixture
def product_with_multiple_values_attributes(product, product_type, category) -> Product:

    attribute = Attribute.objects.create(
        slug="modes",
        name="Available Modes",
        input_type=AttributeInputType.MULTISELECT,
        type=AttributeType.PRODUCT_TYPE,
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
def product_with_default_variant(
    product_type_without_variant, category, warehouse, channel_USD
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-3",
        product_type=product_type_without_variant,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date(1999, 1, 1),
    )
    variant = ProductVariant.objects.create(
        product=product, sku="1234", track_inventory=True
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=100)
    return product


@pytest.fixture
def variant_without_inventory_tracking(
    product_type_without_variant, category, warehouse, channel_USD
):
    product = Product.objects.create(
        name="Test product without inventory tracking",
        slug="test-product-without-tracking",
        product_type=product_type_without_variant,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date.today(),
    )
    variant = ProductVariant.objects.create(
        product=product,
        sku="tracking123",
        track_inventory=False,
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=0)
    return variant


@pytest.fixture
def variant(product, channel_USD) -> ProductVariant:
    product_variant = ProductVariant.objects.create(product=product, sku="SKU_A")
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    return product_variant


@pytest.fixture
def variant_with_many_stocks(variant, warehouses_with_shipping_zone):
    warehouses = warehouses_with_shipping_zone
    Stock.objects.bulk_create(
        [
            Stock(warehouse=warehouses[0], product_variant=variant, quantity=4),
            Stock(warehouse=warehouses[1], product_variant=variant, quantity=3),
        ]
    )
    return variant


@pytest.fixture
def variant_with_many_stocks_different_shipping_zones(
    variant, warehouses_with_different_shipping_zone
):
    warehouses = warehouses_with_different_shipping_zone
    Stock.objects.bulk_create(
        [
            Stock(warehouse=warehouses[0], product_variant=variant, quantity=4),
            Stock(warehouse=warehouses[1], product_variant=variant, quantity=3),
        ]
    )
    return variant


@pytest.fixture
def product_variant_list(product, channel_USD):
    variants = list(
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(product=product, sku="1"),
                ProductVariant(product=product, sku="2"),
                ProductVariant(product=product, sku="3"),
            ]
        )
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=variants[0],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
        ]
    )
    return variants


@pytest.fixture
def product_without_shipping(category, warehouse, channel_USD):
    product_type = ProductType.objects.create(
        name="Type with no shipping",
        slug="no-shipping",
        has_variants=False,
        is_shipping_required=False,
    )
    product = Product.objects.create(
        name="Test product",
        slug="test-product-4",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_B")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=1)
    return product


@pytest.fixture
def product_without_category(product):
    product.category = None
    product.save()
    product.channel_listings.all().update(is_published=False)
    return product


@pytest.fixture
def product_list(product_type, category, warehouse, channel_USD, channel_PLN):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    products = list(
        Product.objects.bulk_create(
            [
                Product(
                    pk=1486,
                    name="Test product 1",
                    slug="test-product-a",
                    category=category,
                    product_type=product_type,
                ),
                Product(
                    pk=1487,
                    name="Test product 2",
                    slug="test-product-b",
                    category=category,
                    product_type=product_type,
                ),
                Product(
                    pk=1489,
                    name="Test product 3",
                    slug="test-product-c",
                    category=category,
                    product_type=product_type,
                ),
            ]
        )
    )
    ProductChannelListing.objects.bulk_create(
        [
            ProductChannelListing(
                product=products[0],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=10,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
            ),
            ProductChannelListing(
                product=products[1],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=20,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
            ),
            ProductChannelListing(
                product=products[2],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=30,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
            ),
        ]
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
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=variants[0],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(20),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(30),
                currency=channel_USD.currency_code,
            ),
        ]
    )
    stocks = []
    for variant in variants:
        stocks.append(Stock(warehouse=warehouse, product_variant=variant, quantity=100))
    Stock.objects.bulk_create(stocks)

    for product in products:
        associate_attribute_values_to_instance(product, product_attr, attr_value)

    return products


@pytest.fixture
def product_list_with_variants_many_channel(
    product_type, category, channel_USD, channel_PLN
):
    products = list(
        Product.objects.bulk_create(
            [
                Product(
                    pk=1486,
                    name="Test product 1",
                    slug="test-product-a",
                    category=category,
                    product_type=product_type,
                ),
                Product(
                    pk=1487,
                    name="Test product 2",
                    slug="test-product-b",
                    category=category,
                    product_type=product_type,
                ),
                Product(
                    pk=1489,
                    name="Test product 3",
                    slug="test-product-c",
                    category=category,
                    product_type=product_type,
                ),
            ]
        )
    )
    ProductChannelListing.objects.bulk_create(
        [
            # Channel: USD
            ProductChannelListing(
                product=products[0],
                channel=channel_USD,
                is_published=True,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
            ),
            # Channel: PLN
            ProductChannelListing(
                product=products[1],
                channel=channel_PLN,
                is_published=True,
                currency=channel_PLN.currency_code,
                visible_in_listings=True,
            ),
            ProductChannelListing(
                product=products[2],
                channel=channel_PLN,
                is_published=True,
                currency=channel_PLN.currency_code,
                visible_in_listings=True,
            ),
        ]
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
    ProductVariantChannelListing.objects.bulk_create(
        [
            # Channel: USD
            ProductVariantChannelListing(
                variant=variants[0],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            # Channel: PLN
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_PLN,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(20),
                currency=channel_PLN.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_PLN,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(30),
                currency=channel_PLN.currency_code,
            ),
        ]
    )


@pytest.fixture
def product_list_with_many_channels(product_list, channel_PLN):
    ProductChannelListing.objects.bulk_create(
        [
            ProductChannelListing(
                product=product_list[0],
                channel=channel_PLN,
                is_published=True,
            ),
            ProductChannelListing(
                product=product_list[1],
                channel=channel_PLN,
                is_published=True,
            ),
            ProductChannelListing(
                product=product_list[2],
                channel=channel_PLN,
                is_published=True,
            ),
        ]
    )
    return product_list


@pytest.fixture
def product_list_unpublished(product_list, channel_USD):
    products = Product.objects.filter(pk__in=[product.pk for product in product_list])
    ProductChannelListing.objects.filter(
        product__in=products, channel=channel_USD
    ).update(is_published=False)
    return products


@pytest.fixture
def product_list_published(product_list, channel_USD):
    products = Product.objects.filter(pk__in=[product.pk for product in product_list])
    ProductChannelListing.objects.filter(
        product__in=products, channel=channel_USD
    ).update(is_published=True)
    return products


@pytest.fixture
def order_list(customer_user, channel_USD):
    address = customer_user.default_billing_address.get_copy()
    data = {
        "billing_address": address,
        "user": customer_user,
        "user_email": customer_user.email,
        "channel": channel_USD,
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
def unavailable_product(product_type, category, channel_USD):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-5",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=False,
        visible_in_listings=False,
    )
    return product


@pytest.fixture
def unavailable_product_with_variant(product_type, category, warehouse, channel_USD):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-6",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=False,
        visible_in_listings=False,
    )

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(
        product=product,
        sku="123",
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)
    return product


@pytest.fixture
def product_with_images(product_type, category, media_root, channel_USD):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-7",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    file_mock_0 = MagicMock(spec=File, name="FileMock0")
    file_mock_0.name = "image0.jpg"
    file_mock_1 = MagicMock(spec=File, name="FileMock1")
    file_mock_1.name = "image1.jpg"
    product.images.create(image=file_mock_0)
    product.images.create(image=file_mock_1)
    return product


@pytest.fixture
def voucher_without_channel(db):
    return Voucher.objects.create(code="mirumee")


@pytest.fixture
def voucher(voucher_without_channel, channel_USD):
    VoucherChannelListing.objects.create(
        voucher=voucher_without_channel,
        channel=channel_USD,
        discount=Money(20, channel_USD.currency_code),
    )
    return voucher_without_channel


@pytest.fixture
def voucher_with_many_channels(voucher, channel_PLN):
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_PLN,
        discount=Money(80, channel_PLN.currency_code),
    )
    return voucher


@pytest.fixture
def voucher_percentage(channel_USD):
    voucher = Voucher.objects.create(
        code="saleor",
        discount_value_type=DiscountValueType.PERCENTAGE,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount_value=10,
        currency=channel_USD.currency_code,
    )
    return voucher


@pytest.fixture
def voucher_specific_product_type(voucher_percentage):
    voucher_percentage.type = VoucherType.SPECIFIC_PRODUCT
    voucher_percentage.save()
    return voucher_percentage


@pytest.fixture
def voucher_with_high_min_spent_amount(channel_USD):
    voucher = Voucher.objects.create(code="mirumee")
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
        min_spent_amount=1_000_000,
    )
    return voucher


@pytest.fixture
def voucher_shipping_type(channel_USD):
    voucher = Voucher.objects.create(
        code="mirumee", type=VoucherType.SHIPPING, countries="IS"
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
    )
    return voucher


@pytest.fixture
def voucher_free_shipping(voucher_percentage, channel_USD):
    voucher_percentage.type = VoucherType.SHIPPING
    voucher_percentage.name = "Free shipping"
    voucher_percentage.save()
    voucher_percentage.channel_listings.filter(channel=channel_USD).update(
        discount_value=100
    )
    return voucher_percentage


@pytest.fixture
def voucher_customer(voucher, customer_user):
    email = customer_user.email
    return VoucherCustomer.objects.create(voucher=voucher, customer_email=email)


@pytest.fixture
def order_line(order, variant):
    product = variant.product
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(product, [], channel, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    return order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )


@pytest.fixture
def order_line_with_allocation_in_many_stocks(
    customer_user, variant_with_many_stocks, channel_USD
):
    address = customer_user.default_billing_address.get_copy()
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")

    order = Order.objects.create(
        billing_address=address,
        user_email=customer_user.email,
        user=customer_user,
        channel=channel_USD,
    )

    product = variant.product
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(product, [], channel_USD, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    order_line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )

    Allocation.objects.bulk_create(
        [
            Allocation(order_line=order_line, stock=stocks[0], quantity_allocated=2),
            Allocation(order_line=order_line, stock=stocks[1], quantity_allocated=1),
        ]
    )

    return order_line


@pytest.fixture
def order_line_with_one_allocation(
    customer_user, variant_with_many_stocks, channel_USD
):
    address = customer_user.default_billing_address.get_copy()
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")

    order = Order.objects.create(
        billing_address=address,
        user_email=customer_user.email,
        user=customer_user,
        channel=channel_USD,
    )

    product = variant.product
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(product, [], channel_USD, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 2
    unit_price = TaxedMoney(net=net, gross=gross)
    order_line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )

    Allocation.objects.create(
        order_line=order_line, stock=stocks[0], quantity_allocated=1
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
def order_with_lines(
    order, product_type, category, shipping_zone, warehouse, channel_USD
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-8",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date.today(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_AA")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    net = variant.get_price(product, [], channel_USD, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    product = Product.objects.create(
        name="Test product 2",
        slug="test-product-9",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date.today(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_B")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_USD.currency_code,
    )
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=2
    )

    net = variant.get_price(product, [], channel_USD, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    quantity = 2
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    order.shipping_address = order.billing_address.get_copy()
    order.channel = channel_USD
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_price = shipping_method.channel_listings.get(channel_id=channel_USD.id)
    order.shipping_method_name = shipping_method.name
    order.shipping_method = shipping_method

    net = shipping_price.get_total()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.shipping_price = TaxedMoney(net=net, gross=gross)
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_with_lines_channel_PLN(
    customer_user,
    product_type,
    category,
    shipping_method_channel_PLN,
    warehouse,
    channel_PLN,
):
    address = customer_user.default_billing_address.get_copy()
    order = Order.objects.create(
        billing_address=address,
        channel=channel_PLN,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
    )
    product = Product.objects.create(
        name="Test product in PLN channel",
        slug="test-product-8-pln",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_PLN,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date.today(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_A_PLN")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_PLN.currency_code,
    )
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    net = variant.get_price(product, [], channel_PLN, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    product = Product.objects.create(
        name="Test product 2 in PLN channel",
        slug="test-product-9-pln",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_PLN,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date.today(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_B_PLN")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_PLN.currency_code,
    )
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=2
    )

    net = variant.get_price(product, [], channel_PLN, channel_listing, None)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 2
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    order.shipping_address = order.billing_address.get_copy()
    order.channel = channel_PLN
    shipping_method = shipping_method_channel_PLN
    shipping_price = shipping_method.channel_listings.get(
        channel_id=channel_PLN.id,
    )
    order.shipping_method_name = shipping_method.name
    order.shipping_method = shipping_method

    net = shipping_price.get_total()
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
    product = variant.product
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(product, [], channel, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        tax_rate=Decimal("0.23"),
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
    invoice = order.invoices.create(
        url="http://www.example.com/invoice.pdf",
        number="01/12/2020/TEST",
        created=datetime.datetime.now(tz=pytz.utc),
        status=JobStatus.SUCCESS,
    )
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
        currency=payment.currency,
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
        currency=payment.currency,
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
        currency=payment.currency,
        kind=TransactionKind.ACTION_TO_CONFIRM,
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
        currency=payment.currency,
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
def dummy_gateway_config():
    return GatewayConfig(
        gateway_name="Dummy",
        auto_capture=True,
        supported_currencies="USD",
        connection_params={"secret-key": "nobodylikesspanishinqusition"},
    )


@pytest.fixture
def dummy_payment_data(payment_dummy):
    return PaymentData(
        amount=Decimal(10),
        currency="USD",
        graphql_payment_id=graphene.Node.to_global_id("Payment", payment_dummy.pk),
        payment_id=payment_dummy.pk,
        billing=None,
        shipping=None,
        order_id=None,
        customer_ip_address=None,
        customer_email="example@test.com",
    )


@pytest.fixture
def new_sale(category, channel_USD):
    sale = Sale.objects.create(name="Sale")
    SaleChannelListing.objects.create(
        sale=sale,
        channel=channel_USD,
        discount_value=5,
        currency=channel_USD.currency_code,
    )
    return sale


@pytest.fixture
def sale(product, category, collection, channel_USD):
    sale = Sale.objects.create(name="Sale")
    SaleChannelListing.objects.create(
        sale=sale,
        channel=channel_USD,
        discount_value=5,
        currency=channel_USD.currency_code,
    )
    sale.products.add(product)
    sale.categories.add(category)
    sale.collections.add(collection)
    return sale


@pytest.fixture
def sale_with_many_channels(product, category, collection, channel_USD, channel_PLN):
    sale = Sale.objects.create(name="Sale")
    SaleChannelListing.objects.create(
        sale=sale,
        channel=channel_USD,
        discount_value=5,
        currency=channel_USD.currency_code,
    )
    SaleChannelListing.objects.create(
        sale=sale,
        channel=channel_PLN,
        discount_value=5,
        currency=channel_PLN.currency_code,
    )
    sale.products.add(product)
    sale.categories.add(category)
    sale.collections.add(collection)
    return sale


@pytest.fixture
def discount_info(category, collection, sale, channel_USD):
    sale_channel_listing = sale.channel_listings.get(channel=channel_USD)

    return DiscountInfo(
        sale=sale,
        channel_listings={channel_USD.slug: sale_channel_listing},
        product_ids=set(),
        category_ids={category.id},  # assumes this category does not have children
        collection_ids={collection.id},
    )


@pytest.fixture
def permission_manage_staff():
    return Permission.objects.get(codename="manage_staff")


@pytest.fixture
def permission_manage_products():
    return Permission.objects.get(codename="manage_products")


@pytest.fixture
def permission_manage_product_types_and_attributes():
    return Permission.objects.get(codename="manage_product_types_and_attributes")


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
def permission_manage_page_types_and_attributes():
    return Permission.objects.get(codename="manage_page_types_and_attributes")


@pytest.fixture
def permission_manage_translations():
    return Permission.objects.get(codename="manage_translations")


@pytest.fixture
def permission_manage_webhooks():
    return Permission.objects.get(codename="manage_webhooks")


@pytest.fixture
def permission_manage_channels():
    return Permission.objects.get(codename="manage_channels")


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
        description="Test description",
    )
    return collection


@pytest.fixture
def published_collection(db, channel_USD):
    collection = Collection.objects.create(
        name="Collection USD",
        slug="collection-usd",
        description="Test description",
    )
    CollectionChannelListing.objects.create(
        channel=channel_USD,
        collection=collection,
        is_published=True,
        publication_date=datetime.date.today(),
    )
    return collection


@pytest.fixture
def published_collection_PLN(db, channel_PLN):
    collection = Collection.objects.create(
        name="Collection PLN",
        slug="collection-pln",
        description="Test description",
    )
    CollectionChannelListing.objects.create(
        channel=channel_PLN,
        collection=collection,
        is_published=True,
        publication_date=datetime.date.today(),
    )
    return collection


@pytest.fixture
def unpublished_collection(db, channel_USD):
    collection = Collection.objects.create(
        name="Unpublished Collection",
        slug="unpublished-collection",
        description="Test description",
    )
    CollectionChannelListing.objects.create(
        channel=channel_USD, collection=collection, is_published=False
    )
    return collection


@pytest.fixture
def unpublished_collection_PLN(db, channel_PLN):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        description="Test description",
    )
    CollectionChannelListing.objects.create(
        channel=channel_PLN, collection=collection, is_published=False
    )
    return collection


@pytest.fixture
def collection_with_products(db, published_collection, product_list_published):
    published_collection.products.set(list(product_list_published))
    return product_list_published


@pytest.fixture
def collection_with_image(db, image, media_root, channel_USD):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        description="Test description",
        background_image=image,
    )
    CollectionChannelListing.objects.create(
        channel=channel_USD, collection=collection, is_published=False
    )
    return collection


@pytest.fixture
def collection_list(db, channel_USD):
    collections = Collection.objects.bulk_create(
        [
            Collection(name="Collection 1", slug="collection-1"),
            Collection(name="Collection 2", slug="collection-2"),
            Collection(name="Collection 3", slug="collection-3"),
        ]
    )
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                channel=channel_USD, collection=collection, is_published=True
            )
            for collection in collections
        ]
    )
    return collections


@pytest.fixture
def page(db, page_type):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "content": "test content",
        "is_published": True,
        "page_type": page_type,
    }
    page = Page.objects.create(**data)

    # associate attribute value
    page_attr = page_type.page_attributes.first()
    page_attr_value = page_attr.values.first()

    associate_attribute_values_to_instance(page, page_attr, page_attr_value)

    return page


@pytest.fixture
def page_list(db, page_type):
    data_1 = {
        "slug": "test-url",
        "title": "Test page",
        "content": "test content",
        "is_published": True,
        "page_type": page_type,
    }
    data_2 = {
        "slug": "test-url-2",
        "title": "Test page",
        "content": "test content",
        "is_published": True,
        "page_type": page_type,
    }
    pages = Page.objects.bulk_create([Page(**data_1), Page(**data_2)])
    return pages


@pytest.fixture
def page_list_unpublished(db, page_type):
    pages = Page.objects.bulk_create(
        [
            Page(
                slug="page-1", title="Page 1", is_published=False, page_type=page_type
            ),
            Page(
                slug="page-2", title="Page 2", is_published=False, page_type=page_type
            ),
            Page(
                slug="page-3", title="Page 3", is_published=False, page_type=page_type
            ),
        ]
    )
    return pages


@pytest.fixture
def page_type(db, size_page_attribute, tag_page_attribute):
    page_type = PageType.objects.create(name="Test page type", slug="test-page-type")
    page_type.page_attributes.add(size_page_attribute)
    page_type.page_attributes.add(tag_page_attribute)

    return page_type


@pytest.fixture
def page_type_list(db, tag_page_attribute):
    page_types = list(
        PageType.objects.bulk_create(
            [
                PageType(name="Test page type 1", slug="test-page-type-1"),
                PageType(name="Example page type 2", slug="page-type-2"),
                PageType(name="Example page type 3", slug="page-type-3"),
            ]
        )
    )

    for i, page_type in enumerate(page_types):
        page_type.page_attributes.add(tag_page_attribute)
        Page.objects.create(
            title=f"Test page {i}",
            slug=f"test-url-{i}",
            is_published=True,
            page_type=page_type,
        )

    return page_types


@pytest.fixture
def model_form_class():
    mocked_form_class = MagicMock(name="test", spec=ModelForm)
    mocked_form_class._meta = Mock(name="_meta")
    mocked_form_class._meta.model = "test_model"
    mocked_form_class._meta.fields = "test_field"
    return mocked_form_class


@pytest.fixture
def menu(db):
    return Menu.objects.get_or_create(name="test-navbar", slug="test-navbar")[0]


@pytest.fixture
def menu_item(menu):
    return MenuItem.objects.create(menu=menu, name="Link 1", url="http://example.com/")


@pytest.fixture
def menu_item_list(menu):
    menu_item_1 = MenuItem.objects.create(menu=menu, name="Link 1")
    menu_item_2 = MenuItem.objects.create(menu=menu, name="Link 2")
    menu_item_3 = MenuItem.objects.create(menu=menu, name="Link 3")
    return menu_item_1, menu_item_2, menu_item_3


@pytest.fixture
def menu_with_items(menu, category, published_collection):
    menu.items.create(name="Link 1", url="http://example.com/")
    menu_item = menu.items.create(name="Link 2", url="http://example.com/")
    menu.items.create(name=category.name, category=category, parent=menu_item)
    menu.items.create(
        name=published_collection.name,
        collection=published_collection,
        parent=menu_item,
    )
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
def collection_translation_fr(published_collection):
    return CollectionTranslation.objects.create(
        language_code="fr",
        collection=published_collection,
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
        cc_brand="visa",
        cc_exp_month=12,
        cc_exp_year=2027,
        total=order_with_lines.total.gross.amount,
        currency=order_with_lines.currency,
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
def payment_dummy_credit_card(db, order_with_lines):
    return Payment.objects.create(
        gateway="mirumee.payments.dummy_credit_card",
        order=order_with_lines,
        is_active=True,
        cc_first_digits="4111",
        cc_last_digits="1111",
        cc_brand="visa",
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
def digital_content(category, media_root, warehouse, channel_USD) -> DigitalContent:
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
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase=datetime.date(1999, 1, 1),
    )
    product_variant = ProductVariant.objects.create(product=product, sku="SKU_554")
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(
        product_variant=product_variant,
        warehouse=warehouse,
        quantity=5,
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
    app = App.objects.create(name="Sample app objects", is_active=True)
    app.tokens.create(name="Default")
    return app


@pytest.fixture
def external_app(db):
    app = App.objects.create(
        name="External App",
        is_active=True,
        type=AppType.THIRDPARTY,
        identifier="mirumee.app.sample",
        about_app="About app text.",
        data_privacy="Data privacy text.",
        data_privacy_url="http://www.example.com/privacy/",
        homepage_url="http://www.example.com/homepage/",
        support_url="http://www.example.com/support/contact/",
        configuration_url="http://www.example.com/app-configuration/",
        app_url="http://www.example.com/app/",
    )
    app.tokens.create(name="Default")
    return app


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
def warehouses_with_different_shipping_zone(warehouses, shipping_zones):
    warehouses[0].shipping_zones.add(shipping_zones[0])
    warehouses[1].shipping_zones.add(shipping_zones[1])
    return warehouses


@pytest.fixture
def warehouse_no_shipping_zone(address):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Warehouse without shipping zone",
        slug="warehouse-no-shipping-zone",
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
def allocations(order_list, stock, channel_USD):
    variant = stock.product_variant
    product = variant.product
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(product, [], channel_USD, channel_listing)
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    price = TaxedMoney(net=net, gross=gross)
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
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
            ),
            OrderLine(
                order=order_list[1],
                variant=variant,
                quantity=2,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                is_shipping_required=variant.is_shipping_required(),
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
            ),
            OrderLine(
                order=order_list[2],
                variant=variant,
                quantity=4,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                is_shipping_required=variant.is_shipping_required(),
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
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


@pytest.fixture
def app_installation():
    app_installation = AppInstallation.objects.create(
        app_name="External App",
        manifest_url="http://localhost:3000/manifest",
    )
    return app_installation


@pytest.fixture
def user_export_file(staff_user):
    job = ExportFile.objects.create(user=staff_user)
    return job


@pytest.fixture
def app_export_file(app):
    job = ExportFile.objects.create(app=app)
    return job


@pytest.fixture
def export_file_list(staff_user):
    export_file_list = list(
        ExportFile.objects.bulk_create(
            [
                ExportFile(user=staff_user),
                ExportFile(
                    user=staff_user,
                ),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.SUCCESS,
                ),
                ExportFile(user=staff_user, status=JobStatus.SUCCESS),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.FAILED,
                ),
            ]
        )
    )

    updated_date = datetime.datetime(
        2019, 4, 18, tzinfo=timezone.get_current_timezone()
    )
    created_date = datetime.datetime(
        2019, 4, 10, tzinfo=timezone.get_current_timezone()
    )
    new_created_and_updated_dates = [
        (created_date, updated_date),
        (created_date, updated_date + datetime.timedelta(hours=2)),
        (
            created_date + datetime.timedelta(hours=2),
            updated_date - datetime.timedelta(days=2),
        ),
        (created_date - datetime.timedelta(days=2), updated_date),
        (
            created_date - datetime.timedelta(days=5),
            updated_date - datetime.timedelta(days=5),
        ),
    ]
    for counter, export_file in enumerate(export_file_list):
        created, updated = new_created_and_updated_dates[counter]
        export_file.created_at = created
        export_file.updated_at = updated

    ExportFile.objects.bulk_update(export_file_list, ["created_at", "updated_at"])

    return export_file_list


@pytest.fixture
def user_export_event(user_export_file):
    return ExportEvent.objects.create(
        type=ExportEvents.EXPORT_FAILED,
        export_file=user_export_file,
        user=user_export_file.user,
        parameters={"message": "Example error message"},
    )


@pytest.fixture
def app_export_event(app_export_file):
    return ExportEvent.objects.create(
        type=ExportEvents.EXPORT_FAILED,
        export_file=app_export_file,
        app=app_export_file.app,
        parameters={"message": "Example error message"},
    )
