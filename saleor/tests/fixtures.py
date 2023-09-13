import datetime
import uuid
from collections import namedtuple
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
from functools import partial
from io import BytesIO
from typing import Callable, List, Optional
from unittest.mock import MagicMock, Mock

import graphene
import pytest
import pytz
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.forms import ModelForm
from django.template.defaultfilters import truncatechars
from django.test.utils import CaptureQueriesContext as BaseCaptureQueriesContext
from django.utils import timezone
from django_countries import countries
from freezegun import freeze_time
from PIL import Image
from prices import Money, TaxedMoney, fixed_discount

from ..account.models import Address, Group, StaffNotificationRecipient, User
from ..app.models import App, AppExtension, AppInstallation
from ..app.types import AppExtensionMount, AppType
from ..attribute import AttributeEntityType, AttributeInputType, AttributeType
from ..attribute.models import (
    Attribute,
    AttributeTranslation,
    AttributeValue,
    AttributeValueTranslation,
)
from ..attribute.utils import associate_attribute_values_to_instance
from ..checkout import base_calculations
from ..checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ..checkout.models import Checkout, CheckoutLine, CheckoutMetadata
from ..checkout.utils import add_variant_to_checkout, add_voucher_to_checkout
from ..core import EventDeliveryStatus, JobStatus
from ..core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ..core.payments import PaymentInterface
from ..core.postgres import FlatConcatSearchVector
from ..core.taxes import zero_money
from ..core.units import MeasurementUnits
from ..core.utils.editorjs import clean_editor_js
from ..csv.events import ExportEvents
from ..csv.models import ExportEvent, ExportFile
from ..discount import DiscountInfo, DiscountValueType, VoucherType
from ..discount.models import (
    NotApplicable,
    Sale,
    SaleChannelListing,
    SaleTranslation,
    Voucher,
    VoucherChannelListing,
    VoucherCustomer,
    VoucherTranslation,
)
from ..giftcard import GiftCardEvents
from ..giftcard.models import GiftCard, GiftCardEvent, GiftCardTag
from ..menu.models import Menu, MenuItem, MenuItemTranslation
from ..order import OrderOrigin, OrderStatus
from ..order.actions import cancel_fulfillment, fulfill_order_lines
from ..order.events import (
    OrderEvents,
    fulfillment_refunded_event,
    order_added_products_event,
)
from ..order.fetch import OrderLineInfo
from ..order.models import (
    FulfillmentLine,
    FulfillmentStatus,
    Order,
    OrderEvent,
    OrderLine,
)
from ..order.search import prepare_order_search_vector_value
from ..order.utils import (
    get_voucher_discount_assigned_to_order,
    get_voucher_discount_for_order,
)
from ..page.models import Page, PageTranslation, PageType
from ..payment import ChargeStatus, TransactionKind
from ..payment.interface import AddressData, GatewayConfig, GatewayResponse, PaymentData
from ..payment.models import Payment, TransactionEvent, TransactionItem
from ..payment.transaction_item_calculations import recalculate_transaction_amounts
from ..payment.utils import create_manual_adjustment_events
from ..permission.enums import get_permissions
from ..permission.models import Permission
from ..plugins.manager import get_plugins_manager
from ..plugins.webhook.tasks import WebhookResponse
from ..plugins.webhook.tests.subscription_webhooks import subscription_queries
from ..plugins.webhook.utils import to_payment_app_id
from ..product import ProductMediaTypes, ProductTypeKind
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
    ProductMedia,
    ProductTranslation,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
    ProductVariantTranslation,
    VariantMedia,
)
from ..product.search import prepare_product_search_vector_value
from ..product.tests.utils import create_image
from ..shipping.models import (
    ShippingMethod,
    ShippingMethodChannelListing,
    ShippingMethodTranslation,
    ShippingMethodType,
    ShippingZone,
)
from ..shipping.utils import convert_to_shipping_method_data
from ..site.models import SiteSettings
from ..tax.utils import calculate_tax_rate, get_tax_class_kwargs_for_order_line
from ..thumbnail.models import Thumbnail
from ..warehouse import WarehouseClickAndCollectOption
from ..warehouse.models import (
    Allocation,
    PreorderAllocation,
    PreorderReservation,
    Reservation,
    Stock,
    Warehouse,
)
from ..webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..webhook.models import Webhook, WebhookEvent
from ..webhook.observability import WebhookData
from .utils import dummy_editorjs


class CaptureQueriesContext(BaseCaptureQueriesContext):
    IGNORED_QUERIES = settings.PATTERNS_IGNORED_IN_QUERY_CAPTURES  # type: ignore

    @property
    def captured_queries(self):
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
    settings.ALLOWED_HOSTS += [site.domain]

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
def site_settings_with_reservations(site_settings):
    site_settings.reserve_stock_duration_anonymous_user = 5
    site_settings.reserve_stock_duration_authenticated_user = 5
    site_settings.save()
    return site_settings


@pytest.fixture
def checkout(db, channel_USD, settings):
    checkout = Checkout.objects.create(
        currency=channel_USD.currency_code,
        channel=channel_USD,
        price_expiration=timezone.now() + settings.CHECKOUT_PRICES_TTL,
        email="user@email.com",
    )
    checkout.set_country("US", commit=True)
    CheckoutMetadata.objects.create(checkout=checkout)
    return checkout


@pytest.fixture
def checkout_JPY(channel_JPY):
    checkout = Checkout.objects.create(
        currency=channel_JPY.currency_code, channel=channel_JPY
    )
    checkout.set_country("JP", commit=True)
    return checkout


@pytest.fixture
def checkout_with_item(checkout, product):
    variant = product.variants.first()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_item_and_transaction_item(checkout_with_item):
    TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout_with_item.pk,
        charged_value=Decimal("10"),
    )
    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_tax_exemption(checkout_with_item):
    checkout_with_item.tax_exemption = True
    checkout_with_item.save(update_fields=["tax_exemption"])
    return checkout_with_item


@pytest.fixture
def checkout_with_same_items_in_multiple_lines(checkout, product):
    variant = product.variants.first()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    add_variant_to_checkout(checkout_info, variant, 1, force_new_line=True)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_item_and_voucher_specific_products(
    checkout_with_item, voucher_specific_product_type
):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    add_voucher_to_checkout(
        manager, checkout_info, lines, voucher_specific_product_type
    )
    checkout_with_item.refresh_from_db()
    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_voucher_once_per_order(checkout_with_item, voucher):
    voucher.apply_once_per_order = True
    voucher.save()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    add_voucher_to_checkout(manager, checkout_info, lines, voucher)
    checkout_with_item.refresh_from_db()
    return checkout_with_item


@pytest.fixture
def checkout_with_item_and_voucher(checkout_with_item, voucher):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, manager)
    add_voucher_to_checkout(manager, checkout_info, lines, voucher)
    checkout_with_item.refresh_from_db()
    return checkout_with_item


@pytest.fixture
def checkout_line(checkout_with_item):
    return checkout_with_item.lines.first()


@pytest.fixture
def checkout_with_item_total_0(checkout, product_price_0):
    variant = product_price_0.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_JPY_with_item(checkout_JPY, product_in_channel_JPY):
    variant = product_in_channel_JPY.variants.get()
    checkout_info = fetch_checkout_info(checkout_JPY, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout_JPY.save()
    return checkout_JPY


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
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout_with_item.gift_cards.add(gift_card)
    checkout.save()
    checkout.metadata_storage.save()
    return checkout


@pytest.fixture
def checkout_with_digital_item(checkout, digital_content, address):
    """Create a checkout with a digital line."""
    variant = digital_content.product_variant
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.discount_amount = Decimal(0)
    checkout.billing_address = address
    checkout.email = "customer@example.com"
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_shipping_required(checkout_with_item, product):
    checkout = checkout_with_item
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_item_and_shipping_method(checkout_with_item, shipping_method):
    checkout = checkout_with_item
    checkout.shipping_method = shipping_method
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_item_and_voucher_and_shipping_method(
    checkout_with_item_and_voucher, shipping_method
):
    checkout = checkout_with_item_and_voucher
    checkout.shipping_method = shipping_method
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
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_single_item(checkout, product):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_variant_without_inventory_tracking(
    checkout, variant_without_inventory_tracking, address, shipping_method
):
    variant = variant_without_inventory_tracking
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    checkout.billing_address = address
    checkout.metadata_storage.store_value_in_metadata(items={"accepted": "true"})
    checkout.metadata_storage.store_value_in_private_metadata(
        items={"accepted": "false"}
    )
    checkout.save()
    checkout.metadata_storage.save()
    return checkout


@pytest.fixture()
def checkout_with_variants(
    checkout,
    stock,
    product_with_default_variant,
    product_with_single_variant,
    product_with_two_variants,
):
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())

    add_variant_to_checkout(
        checkout_info, product_with_default_variant.variants.get(), 1
    )
    add_variant_to_checkout(
        checkout_info, product_with_single_variant.variants.get(), 10
    )
    add_variant_to_checkout(
        checkout_info, product_with_two_variants.variants.first(), 3
    )
    add_variant_to_checkout(checkout_info, product_with_two_variants.variants.last(), 5)

    checkout.save()
    return checkout


@pytest.fixture()
def checkout_with_shipping_address(checkout_with_variants, address):
    checkout = checkout_with_variants

    checkout.shipping_address = address.get_copy()
    checkout.save()

    return checkout


@pytest.fixture
def checkout_with_variants_for_cc(
    checkout, stocks_for_cc, product_variant_list, product_with_two_variants
):
    CheckoutLine.objects.bulk_create(
        [
            CheckoutLine(
                checkout=checkout,
                variant=product_variant_list[0],
                quantity=3,
                currency="USD",
            ),
            CheckoutLine(
                checkout=checkout,
                variant=product_variant_list[1],
                quantity=10,
                currency="USD",
            ),
            CheckoutLine(
                checkout=checkout,
                variant=product_with_two_variants.variants.last(),
                quantity=5,
                currency="USD",
            ),
        ]
    )
    return checkout


@pytest.fixture()
def checkout_with_shipping_address_for_cc(checkout_with_variants_for_cc, address):
    checkout = checkout_with_variants_for_cc

    checkout.shipping_address = address.get_copy()
    checkout.save()

    return checkout


@pytest.fixture
def checkout_with_items(checkout, product_list, product):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 1)
    for prod in product_list:
        variant = prod.variants.get()
        add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()
    checkout.refresh_from_db()
    return checkout


@pytest.fixture
def checkout_with_items_and_shipping(checkout_with_items, address, shipping_method):
    checkout_with_items.shipping_address = address
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.billing_address = address
    checkout_with_items.save()
    return checkout_with_items


@pytest.fixture
def checkout_with_voucher(checkout, product, voucher):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout.voucher_code = voucher.code
    checkout.discount = Money("20.00", "USD")
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_voucher_percentage(checkout, product, voucher_percentage):
    variant = product.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, variant, 3)
    checkout.voucher_code = voucher_percentage.code
    checkout.discount = Money("3.00", "USD")
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_voucher_free_shipping(
    checkout_with_items_and_shipping, voucher_free_shipping
):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_items_and_shipping)
    checkout_info = fetch_checkout_info(
        checkout_with_items_and_shipping, lines, manager
    )
    add_voucher_to_checkout(manager, checkout_info, lines, voucher_free_shipping)
    return checkout_with_items_and_shipping


@pytest.fixture
def checkout_with_gift_card(checkout_with_item, gift_card):
    checkout_with_item.gift_cards.add(gift_card)
    checkout_with_item.save()
    return checkout_with_item


@pytest.fixture()
def checkout_with_preorders_only(
    checkout,
    stocks_for_cc,
    preorder_variant_with_end_date,
    preorder_variant_channel_threshold,
):
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, get_plugins_manager())
    add_variant_to_checkout(checkout_info, preorder_variant_with_end_date, 2)
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 2)

    checkout.save()
    return checkout


@pytest.fixture()
def checkout_with_preorders_and_regular_variant(
    checkout, stocks_for_cc, preorder_variant_with_end_date, product_variant_list
):
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, get_plugins_manager())
    add_variant_to_checkout(checkout_info, preorder_variant_with_end_date, 2)
    add_variant_to_checkout(checkout_info, product_variant_list[0], 2)

    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_gift_card_items(
    checkout, non_shippable_gift_card_product, shippable_gift_card_product
):
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    non_shippable_variant = non_shippable_gift_card_product.variants.get()
    shippable_variant = shippable_gift_card_product.variants.get()
    add_variant_to_checkout(checkout_info, non_shippable_variant, 1)
    add_variant_to_checkout(checkout_info, shippable_variant, 2)
    checkout.save()
    return checkout


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
def checkout_with_item_and_preorder_item(
    checkout_with_item, product, preorder_variant_channel_threshold
):
    checkout_info = fetch_checkout_info(checkout_with_item, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 1)
    return checkout_with_item


@pytest.fixture
def checkout_with_problems(
    checkout_with_items,
    product_type,
    address,
    shipping_method,
    category,
    default_tax_class,
    channel_USD,
    warehouse,
):
    checkout_with_items.shipping_address = address
    checkout_with_items.billing_address = address
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.save(
        update_fields=["shipping_address", "shipping_method", "billing_address"]
    )

    first_line = checkout_with_items.lines.first()
    first_line.variant.track_inventory = True
    first_line.variant.save(update_fields=["track_inventory"])

    product_type = first_line.variant.product.product_type
    product_type.is_shipping_required = True
    product_type.save(update_fields=["is_shipping_required"])

    first_line.variant.stocks.all().delete()

    second_line = checkout_with_items.lines.last()

    available_at = datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=5)
    product = second_line.variant.product
    product.channel_listings.update(
        available_for_purchase_at=available_at, is_published=False
    )

    return checkout_with_items


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
def address_with_areas(db):
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
        country_area="test_country_area",
        city_area="test_city_area",
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
        "metadata": [{"key": "public", "value": "public_value"}],
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
        external_reference="LeslieWade",
        metadata={"key": "value"},
        private_metadata={"secret_key": "secret_value"},
    )
    user.addresses.add(default_address)
    user._password = "password"
    return user


@pytest.fixture
def customer_user2(address):
    default_address = address.get_copy()
    user = User.objects.create_user(
        "test2@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Jane",
        last_name="Doe",
        external_reference="JaneDoe",
    )
    user.addresses.add(default_address)
    user._password = "password"
    return user


@pytest.fixture
def customer_users(address, customer_user, customer_user2):
    default_address = address.get_copy()
    customer_user3 = User.objects.create_user(
        "test3@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Chris",
        last_name="Duck",
    )
    customer_user3.addresses.add(default_address)
    customer_user3._password = "password"

    return [customer_user, customer_user2, customer_user3]


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
    CheckoutMetadata.objects.create(checkout=checkout)
    return checkout


@pytest.fixture
def user_checkout_for_cc(customer_user, channel_USD, warehouse_for_cc):
    checkout = Checkout.objects.create(
        user=customer_user,
        email=customer_user.email,
        channel=channel_USD,
        billing_address=customer_user.default_billing_address,
        shipping_address=warehouse_for_cc.address,
        collection_point=warehouse_for_cc,
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
    checkout_info = fetch_checkout_info(user_checkout, [], get_plugins_manager())
    for product in product_list:
        variant = product.variants.get()
        add_variant_to_checkout(checkout_info, variant, 1)
    user_checkout.refresh_from_db()
    return user_checkout


@pytest.fixture
def user_checkout_with_items_for_cc(user_checkout_for_cc, product_list):
    checkout_info = fetch_checkout_info(user_checkout_for_cc, [], get_plugins_manager())
    for product in product_list:
        variant = product.variants.get()
        add_variant_to_checkout(checkout_info, variant, 1)
    user_checkout_for_cc.refresh_from_db()
    return user_checkout_for_cc


@pytest.fixture
def user_checkouts(request, user_checkout_with_items, user_checkout_with_items_for_cc):
    if request.param == "regular":
        return user_checkout_with_items
    elif request.param == "click_and_collect":
        return user_checkout_with_items_for_cc
    else:
        raise ValueError("Internal test error")


@pytest.fixture
def orders(customer_user, channel_USD, channel_PLN):
    return Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                status=OrderStatus.CANCELED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.UNFULFILLED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.PARTIALLY_FULFILLED,
                channel=channel_USD,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                channel=channel_PLN,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.DRAFT,
                channel=channel_PLN,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.UNCONFIRMED,
                channel=channel_PLN,
            ),
        ]
    )


@pytest.fixture
def orders_from_checkout(customer_user, checkout):
    return Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                status=OrderStatus.CANCELED,
                channel=checkout.channel,
                checkout_token=checkout.token,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.UNFULFILLED,
                channel=checkout.channel,
                checkout_token=checkout.token,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                channel=checkout.channel,
                checkout_token=checkout.token,
            ),
            Order(
                user=customer_user,
                status=OrderStatus.FULFILLED,
                channel=checkout.channel,
                checkout_token=checkout.token,
            ),
        ]
    )


@pytest.fixture
def order_generator(customer_user, channel_USD):
    address = customer_user.default_billing_address.get_copy()

    def create_order(
        billing_address=address,
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
        origin=OrderOrigin.CHECKOUT,
        should_refresh_prices=False,
        metadata={"key": "value"},
        private_metadata={"secret_key": "secret_value"},
        checkout_token="",
        status=OrderStatus.UNFULFILLED,
        search_vector_class=None,
    ):
        order = Order.objects.create(
            billing_address=billing_address,
            channel=channel,
            currency=currency,
            shipping_address=shipping_address,
            user_email=user_email,
            user=user,
            origin=origin,
            should_refresh_prices=should_refresh_prices,
            metadata=metadata,
            private_metadata=private_metadata,
            checkout_token=checkout_token,
            status=status,
        )
        if search_vector_class:
            search_vector = search_vector_class(
                *prepare_order_search_vector_value(order)
            )
            order.search_vector = search_vector
            order.save(update_fields=["search_vector"])
        return order

    return create_order


@pytest.fixture
def order(order_generator):
    return order_generator()


@pytest.fixture
def order_unconfirmed(order):
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def product_type_generator(
    attribute_generator, attribute_value_generator, default_tax_class
):
    def create_product_type(
        name="Default Type",
        slug="default-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
        tax_class=default_tax_class,
        product_attributes=None,
        variant_attributes=None,
    ):
        product_type = ProductType.objects.create(
            name=name,
            slug=slug,
            kind=kind,
            has_variants=has_variants,
            is_shipping_required=is_shipping_required,
            tax_class=tax_class,
        )
        if product_attributes is None:
            product_attribute = attribute_generator(
                external_reference="colorAttributeExternalReference",
                slug="color",
                name="Color",
                type=AttributeType.PRODUCT_TYPE,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
                available_in_grid=True,
            )

            attribute_value_generator(
                external_reference="colorAttributeValue1ExternalReference",
                name="Red",
                slug="red",
                attribute=product_attribute,
            )

            product_attributes = [product_attribute]
        if variant_attributes is None:
            variant_attribute = attribute_generator(
                external_reference="sizeAttributeExternalReference",
                slug="size",
                name="Size",
                type=AttributeType.PRODUCT_TYPE,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
                available_in_grid=True,
            )

            attribute_value_generator(
                name="Small",
                slug="small",
                attribute=variant_attribute,
            )
            variant_attributes = [variant_attribute]

        product_type.product_attributes.add(*product_attributes)
        product_type.variant_attributes.add(
            *variant_attributes, through_defaults={"variant_selection": True}
        )
        return product_type

    return create_product_type


@pytest.fixture
def admin_user(db):
    """Return a Django admin user."""
    return User.objects.create_user(
        "admin@example.com",
        "password",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )


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
def shipping_zone(db, channel_USD, default_tax_class):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(
        name="Europe", countries=[code for code, name in countries]
    )
    shipping_zone.channels.add(channel_USD)
    method = shipping_zone.shipping_methods.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
        tax_class=default_tax_class,
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
def shipping_zone_JPY(shipping_zone, channel_JPY):
    shipping_zone.channels.add(channel_JPY)
    method = shipping_zone.shipping_methods.get()
    ShippingMethodChannelListing.objects.create(
        channel=channel_JPY,
        currency=channel_JPY.currency_code,
        shipping_method=method,
        minimum_order_price=Money(0, channel_JPY.currency_code),
        price=Money(700, channel_JPY.currency_code),
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

    shipping_zone_poland.channels.add(channel_PLN, channel_USD)
    shipping_zone_usa.channels.add(channel_PLN, channel_USD)

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


def chunks(it, n):
    for i in range(0, len(it), n):
        yield it[i : i + n]


@pytest.fixture
def shipping_zones_with_warehouses(address, channel_USD):
    zones = [ShippingZone(name=f"{i}_zone") for i in range(10)]
    warehouses = [Warehouse(slug=f"{i}_warehouse", address=address) for i in range(20)]
    warehouses = Warehouse.objects.bulk_create(warehouses)
    warehouses_in_batches = list(chunks(warehouses, 2))
    for i, zone in enumerate(ShippingZone.objects.bulk_create(zones)):
        zone.channels.add(channel_USD)
        for warehouse in warehouses_in_batches[i]:
            zone.warehouses.add(warehouse)
    return zones


@pytest.fixture
def shipping_zones_with_different_channels(db, channel_USD, channel_PLN):
    shipping_zone_poland, shipping_zone_usa = ShippingZone.objects.bulk_create(
        [
            ShippingZone(name="Poland", countries=["PL"]),
            ShippingZone(name="USA", countries=["US"]),
        ]
    )

    shipping_zone_poland.channels.add(channel_PLN, channel_USD)
    shipping_zone_usa.channels.add(channel_USD)

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
def shipping_method(shipping_zone, channel_USD, default_tax_class):
    method = ShippingMethod.objects.create(
        name="DHL",
        type=ShippingMethodType.PRICE_BASED,
        shipping_zone=shipping_zone,
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        tax_class=default_tax_class,
    )
    ShippingMethodChannelListing.objects.create(
        shipping_method=method,
        channel=channel_USD,
        minimum_order_price=Money(0, "USD"),
        price=Money(10, "USD"),
    )
    return method


@pytest.fixture
def shipping_method_data(shipping_method, channel_USD):
    listing = ShippingMethodChannelListing.objects.filter(
        channel=channel_USD, shipping_method=shipping_method
    ).get()
    return convert_to_shipping_method_data(shipping_method, listing)


@pytest.fixture
def shipping_method_weight_based(shipping_zone, channel_USD):
    method = ShippingMethod.objects.create(
        name="weight based method",
        type=ShippingMethodType.WEIGHT_BASED,
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
def shipping_method_excluded_by_postal_code(shipping_method):
    shipping_method.postal_code_rules.create(start="HB2", end="HB6")
    return shipping_method


@pytest.fixture
def shipping_method_channel_PLN(shipping_zone, channel_PLN):
    shipping_zone.channels.add(channel_PLN)
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
def attribute_generator():
    def create_attribute(
        external_reference="attributeExtRef",
        slug="attr",
        name="Attr",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    ):
        attribute, _ = Attribute.objects.get_or_create(
            external_reference=external_reference,
            slug=slug,
            name=name,
            type=type,
            filterable_in_storefront=filterable_in_storefront,
            filterable_in_dashboard=filterable_in_dashboard,
            available_in_grid=available_in_grid,
        )

        return attribute

    return create_attribute


@pytest.fixture
def attribute_value_generator(attribute_generator):
    def create_attribute_value(
        attribute=None,
        external_reference=None,
        name="Attr Value",
        slug="attr-value",
        value="",
    ):
        if attribute is None:
            attribute = attribute_generator()
        attribute_value, _ = AttributeValue.objects.get_or_create(
            attribute=attribute,
            external_reference=external_reference,
            name=name,
            slug=slug,
            value=value,
        )

        return attribute_value

    return create_attribute_value


@pytest.fixture
def attribute_values_generator(attribute_generator):
    def create_attribute_values(
        external_references=None,
        names=None,
        slugs=None,
        attribute=None,
        values=None,
    ):
        if attribute is None:
            attribute = attribute_generator()

        if slugs is None:
            slugs = ["attr-value"]

        if external_references is None:
            external_references = [None] * len(slugs)

        if names is None:
            names = [""] * len(slugs)

        if values is None:
            values = [""] * len(slugs)

        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=attribute,
                    external_reference=ext_ref,
                    name=name,
                    slug=slug,
                    value=value,
                )
                for slug, name, ext_ref, value in zip(
                    slugs, names, external_references, values
                )
            ],
            ignore_conflicts=True,
        )

        return list(AttributeValue.objects.filter(slug__in=slugs))

    return create_attribute_values


@pytest.fixture
def color_attribute(db, attribute_generator, attribute_values_generator):
    attribute = attribute_generator(
        external_reference="colorAttributeExternalReference",
        slug="color",
        name="Color",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    external_references = [
        "colorAttributeValue1ExternalReference",
        "colorAttributeValue2ExternalReference",
    ]
    slugs = ["red", "blue"]
    names = ["Red", "Blue"]
    attribute_values_generator(
        attribute=attribute,
        external_references=external_references,
        names=names,
        slugs=slugs,
    )

    return attribute


@pytest.fixture
def color_attribute_with_translations(db):
    attribute = Attribute.objects.create(
        slug="color",
        name="Color",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    value1 = AttributeValue.objects.create(attribute=attribute, name="Red", slug="red")
    AttributeValue.objects.create(attribute=attribute, name="Blue", slug="blue")
    attribute.translations.create(language_code="pl", name="Czerwony")
    attribute.translations.create(language_code="de", name="Rot")
    value1.translations.create(language_code="pl", plain_text="Old Kolor")
    value1.translations.create(language_code="de", name="Rot", plain_text="Old Kolor")

    return attribute


@pytest.fixture
def attribute_without_values():
    return Attribute.objects.create(
        slug="dropdown",
        name="Dropdown",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
        visible_in_storefront=True,
        entity_type=None,
    )


@pytest.fixture
def product_type_with_product_attributes(attribute_without_values):
    product_type = ProductType.objects.create(
        name="product_type_with_product_attributes",
        slug="product-type-with-product-attributes",
        has_variants=False,
        is_shipping_required=False,
        weight=0,
    )
    product_type.product_attributes.add(attribute_without_values)
    return product_type


@pytest.fixture
def product_type_with_variant_attributes(attribute_without_values):
    product_type = ProductType.objects.create(
        name="product_type_with_variant_attributes",
        slug="product-type-with-variant-attributes",
        has_variants=False,
        is_shipping_required=False,
        weight=0,
    )
    product_type.variant_attributes.add(attribute_without_values)
    return product_type


@pytest.fixture
def product_with_product_attributes(
    product_type_with_product_attributes, non_default_category
):
    return Product.objects.create(
        name="product_with_product_attributes",
        slug="product-with-product-attributes",
        product_type=product_type_with_product_attributes,
        category=non_default_category,
    )


@pytest.fixture
def product_with_variant_attributes(
    product_type_with_variant_attributes, non_default_category
):
    return Product.objects.create(
        name="product_with_variant_attributes",
        slug="product-with-variant-attributes",
        product_type=product_type_with_variant_attributes,
        category=non_default_category,
    )


@pytest.fixture
def date_attribute(db):
    attribute = Attribute.objects.create(
        slug="release-date",
        name="Release date",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.DATE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=attribute,
                name=f"{attribute.name}: {value.date()}",
                slug=f"{value.date()}_{attribute.id}",
                date_time=value,
            )
            for value in [
                datetime.datetime(2020, 10, 5, tzinfo=pytz.utc),
                datetime.datetime(2020, 11, 5, tzinfo=pytz.utc),
            ]
        ]
    )

    return attribute


@pytest.fixture
def date_time_attribute(db):
    attribute = Attribute.objects.create(
        slug="release-date-time",
        name="Release date time",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.DATE_TIME,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )

    AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=attribute,
                name=f"{attribute.name}: {value.date()}",
                slug=f"{value.date()}_{attribute.id}",
                date_time=value,
            )
            for value in [
                datetime.datetime(2020, 10, 5, tzinfo=pytz.utc),
                datetime.datetime(2020, 11, 5, tzinfo=pytz.utc),
            ]
        ]
    )

    return attribute


@pytest.fixture
def attribute_choices_for_sorting(db):
    attribute = Attribute.objects.create(
        slug="sorting",
        name="Sorting",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="Global", slug="summer")
    AttributeValue.objects.create(attribute=attribute, name="Apex", slug="zet")
    AttributeValue.objects.create(attribute=attribute, name="Police", slug="absorb")
    return attribute


@pytest.fixture
def boolean_attribute(db):
    attribute = Attribute.objects.create(
        slug="boolean",
        name="Boolean",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.BOOLEAN,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name=f"{attribute.name}: Yes",
        slug=f"{attribute.id}_true",
        boolean=True,
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name=f"{attribute.name}: No",
        slug=f"{attribute.id}_false",
        boolean=False,
    )
    return attribute


@pytest.fixture
def rich_text_attribute(db):
    attribute = Attribute.objects.create(
        slug="text",
        name="Text",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.RICH_TEXT,
        filterable_in_storefront=False,
        filterable_in_dashboard=False,
        available_in_grid=False,
    )
    text = "Rich text attribute content."
    AttributeValue.objects.create(
        attribute=attribute,
        name=truncatechars(clean_editor_js(dummy_editorjs(text), to_string=True), 50),
        slug=f"instance_{attribute.id}",
        rich_text=dummy_editorjs(text),
    )
    return attribute


@pytest.fixture
def rich_text_attribute_page_type(db):
    attribute = Attribute.objects.create(
        slug="text",
        name="Text",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.RICH_TEXT,
        filterable_in_storefront=False,
        filterable_in_dashboard=False,
        available_in_grid=False,
    )
    text = "Rich text attribute content."
    AttributeValue.objects.create(
        attribute=attribute,
        name=truncatechars(clean_editor_js(dummy_editorjs(text), to_string=True), 50),
        slug=f"instance_{attribute.id}",
        rich_text=dummy_editorjs(text),
    )
    return attribute


@pytest.fixture
def rich_text_attribute_with_many_values(rich_text_attribute):
    attribute = rich_text_attribute
    values = []
    for i in range(5):
        text = f"Rich text attribute content{i}."
        values.append(
            AttributeValue(
                attribute=attribute,
                name=truncatechars(
                    clean_editor_js(dummy_editorjs(text), to_string=True), 50
                ),
                slug=f"instance_{attribute.id}_{i}",
                rich_text=dummy_editorjs(text),
            )
        )
    AttributeValue.objects.bulk_create(values)
    return rich_text_attribute


@pytest.fixture
def plain_text_attribute(db):
    attribute = Attribute.objects.create(
        slug="plain-text",
        name="Plain text",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.PLAIN_TEXT,
        filterable_in_storefront=False,
        filterable_in_dashboard=False,
        available_in_grid=False,
    )
    text = "Plain text attribute content."
    AttributeValue.objects.create(
        attribute=attribute,
        name=truncatechars(text, 50),
        slug=f"instance_{attribute.id}",
        plain_text=text,
    )
    return attribute


@pytest.fixture
def plain_text_attribute_page_type(db):
    attribute = Attribute.objects.create(
        slug="plain-text",
        name="Plain text",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.PLAIN_TEXT,
        filterable_in_storefront=False,
        filterable_in_dashboard=False,
        available_in_grid=False,
    )
    text = "Plain text attribute content."
    AttributeValue.objects.create(
        attribute=attribute,
        name=truncatechars(text, 50),
        slug=f"instance_{attribute.id}",
        plain_text=text,
    )
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
def size_attribute(
    db, attribute_generator, attribute_values_generator
):  # pylint: disable=W0613
    attribute = attribute_generator(
        external_reference="sizeAttributeExternalReference",
        slug="size",
        name="Size",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )

    slugs = ["small", "big"]
    names = ["Small", "Big"]
    attribute_values_generator(
        attribute=attribute,
        names=names,
        slugs=slugs,
    )

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
def numeric_attribute(db):
    attribute = Attribute.objects.create(
        slug="length",
        name="Length",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.NUMERIC,
        unit=MeasurementUnits.CM,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="9.5", slug="10_5")
    AttributeValue.objects.create(attribute=attribute, name="15.2", slug="15_2")
    return attribute


@pytest.fixture
def numeric_attribute_without_unit(db):
    attribute = Attribute.objects.create(
        slug="count",
        name="Count",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.NUMERIC,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="9", slug="9")
    AttributeValue.objects.create(attribute=attribute, name="15", slug="15")
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
        file_url="test_file.txt",
        content_type="text/plain",
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.jpeg",
        slug="test_filejpeg",
        file_url="test_file.jpeg",
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
def swatch_attribute(db):
    attribute = Attribute.objects.create(
        slug="T-shirt color",
        name="t-shirt-color",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.SWATCH,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(
        attribute=attribute, name="Red", slug="red", value="#ff0000"
    )
    AttributeValue.objects.create(
        attribute=attribute, name="White", slug="whit", value="#fffff"
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="Logo",
        slug="logo",
        file_url="http://mirumee.com/test_media/test_file.jpeg",
        content_type="image/jpeg",
    )
    return attribute


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
def product_type_variant_reference_attribute(db):
    return Attribute.objects.create(
        slug="variant-reference",
        name="Variant reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT_VARIANT,
    )


@pytest.fixture
def page_type_variant_reference_attribute(db):
    return Attribute.objects.create(
        slug="variant-reference",
        name="Variant reference",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT_VARIANT,
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
        file_url="test_file.txt",
        content_type="text/plain",
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.jpeg",
        slug="test_filejpeg",
        file_url="test_file.jpeg",
        content_type="image/jpeg",
    )
    return attribute


@pytest.fixture
def product_type_attribute_list() -> List[Attribute]:
    return list(
        Attribute.objects.bulk_create(
            [
                Attribute(
                    slug="height", name="Height", type=AttributeType.PRODUCT_TYPE
                ),
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
def icon_image():
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="PNG")
    return SimpleUploadedFile("logo.png", img_data.getvalue())


@pytest.fixture
def image_list():
    img_data_1 = BytesIO()
    image_1 = Image.new("RGB", size=(1, 1))
    image_1.save(img_data_1, format="JPEG")

    img_data_2 = BytesIO()
    image_2 = Image.new("RGB", size=(1, 1))
    image_2.save(img_data_2, format="JPEG")
    return [
        SimpleUploadedFile("image1.jpg", img_data_1.getvalue()),
        SimpleUploadedFile("image2.jpg", img_data_2.getvalue()),
    ]


@pytest.fixture
def category_generator():
    def create_category(
        name="Default",
        slug="default",
    ):
        category = Category.objects.create(
            name=name,
            slug=slug,
        )
        return category

    return create_category


@pytest.fixture
def category(category_generator):  # pylint: disable=W0613
    return category_generator()


@pytest.fixture
def category_with_image(db, image, media_root):  # pylint: disable=W0613
    return Category.objects.create(
        name="Default2", slug="default2", background_image=image
    )


@pytest.fixture
def categories(db):
    category1 = Category.objects.create(name="Category1", slug="cat1")
    category2 = Category.objects.create(name="Category2", slug="cat2")
    return [category1, category2]


@pytest.fixture
def category_list():
    category_1 = Category.objects.create(name="Category 1", slug="category-1")
    category_2 = Category.objects.create(name="Category 2", slug="category-2")
    category_3 = Category.objects.create(name="Category 3", slug="category-3")
    return category_1, category_2, category_3


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
                published_at=datetime.datetime.now(pytz.UTC),
                is_published=True,
            )
        )
        product_channel_listings.append(
            ProductChannelListing(
                product=product,
                channel=channel_PLN,
                published_at=datetime.datetime.now(pytz.UTC),
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
def permission_manage_orders_import():
    return Permission.objects.get(codename="manage_orders_import")


@pytest.fixture
def permission_manage_checkouts():
    return Permission.objects.get(codename="manage_checkouts")


@pytest.fixture
def permission_handle_checkouts():
    return Permission.objects.get(codename="handle_checkouts")


@pytest.fixture
def permission_manage_plugins():
    return Permission.objects.get(codename="manage_plugins")


@pytest.fixture
def permission_manage_apps():
    return Permission.objects.get(codename="manage_apps")


@pytest.fixture
def permission_handle_taxes():
    return Permission.objects.get(codename="handle_taxes")


@pytest.fixture
def permission_manage_observability():
    return Permission.objects.get(codename="manage_observability")


@pytest.fixture
def permission_manage_taxes():
    return Permission.objects.get(codename="manage_taxes")


@pytest.fixture
def product_type(product_type_generator):
    return product_type_generator()


@pytest.fixture
def product_type_list():
    product_type_1 = ProductType.objects.create(
        name="Type 1", slug="type-1", kind=ProductTypeKind.NORMAL
    )
    product_type_2 = ProductType.objects.create(
        name="Type 2", slug="type-2", kind=ProductTypeKind.NORMAL
    )
    product_type_3 = ProductType.objects.create(
        name="Type 3", slug="type-3", kind=ProductTypeKind.NORMAL
    )
    return product_type_1, product_type_2, product_type_3


@pytest.fixture
def non_shippable_gift_card_product_type(db):
    product_type = ProductType.objects.create(
        name="Gift card type no shipping",
        slug="gift-card-type-no-shipping",
        kind=ProductTypeKind.GIFT_CARD,
        has_variants=True,
        is_shipping_required=False,
    )
    return product_type


@pytest.fixture
def shippable_gift_card_product_type(db):
    product_type = ProductType.objects.create(
        name="Gift card type with shipping",
        slug="gift-card-type-with-shipping",
        kind=ProductTypeKind.GIFT_CARD,
        has_variants=True,
        is_shipping_required=True,
    )
    return product_type


@pytest.fixture
def product_type_with_rich_text_attribute(rich_text_attribute):
    product_type = ProductType.objects.create(
        name="Default Type",
        slug="default-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(rich_text_attribute)
    product_type.variant_attributes.add(rich_text_attribute)
    return product_type


@pytest.fixture
def product_type_without_variant():
    product_type = ProductType.objects.create(
        name="Type",
        slug="type",
        has_variants=False,
        is_shipping_required=True,
        kind=ProductTypeKind.NORMAL,
    )
    return product_type


@pytest.fixture
def product(product_type, category, warehouse, channel_USD, default_tax_class):
    product_attr = product_type.product_attributes.first()
    product_attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-11",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="10.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )

    associate_attribute_values_to_instance(product, product_attr, product_attr_value)

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(product=product, sku="123")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)

    return product


@pytest.fixture
def product_with_translations(product):
    product.translations.create(language_code="pl", name="OldProduct PL")
    product.translations.create(language_code="de", name="OldProduct DE")

    return product


@pytest.fixture
def shippable_gift_card_product(
    shippable_gift_card_product_type, category, warehouse, channel_USD
):
    product_type = shippable_gift_card_product_type

    product = Product.objects.create(
        name="Shippable gift card",
        slug="shippable-gift-card",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="100.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )

    variant = ProductVariant.objects.create(
        product=product, sku="958", track_inventory=False
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(100),
        discounted_price_amount=Decimal(100),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=1)

    return product


@pytest.fixture
def product_price_0(category, warehouse, channel_USD):
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
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_C")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(0),
        discounted_price_amount=Decimal(0),
        cost_price_amount=Decimal(0),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=1)
    return product


@pytest.fixture
def product_in_channel_JPY(product, channel_JPY, warehouse_JPY):
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_JPY,
        is_published=True,
        discounted_price_amount="1200",
        currency=channel_JPY.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )
    variant = product.variants.get()
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_JPY,
        price_amount=Decimal(1200),
        discounted_price_amount=Decimal(1200),
        cost_price_amount=Decimal(300),
        currency=channel_JPY.currency_code,
    )
    Stock.objects.create(warehouse=warehouse_JPY, product_variant=variant, quantity=10)
    return product


@pytest.fixture
def non_shippable_gift_card_product(
    non_shippable_gift_card_product_type, category, warehouse, channel_USD
):
    product_type = non_shippable_gift_card_product_type

    product = Product.objects.create(
        name="Non shippable gift card",
        slug="non-shippable-gift-card",
        product_type=product_type,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="200.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )

    variant = ProductVariant.objects.create(
        product=product, sku="785", track_inventory=False
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(250),
        discounted_price_amount=Decimal(250),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=1)

    return product


@pytest.fixture
def product_with_rich_text_attribute(
    product_type_with_rich_text_attribute, category, warehouse, channel_USD
):
    product_attr = product_type_with_rich_text_attribute.product_attributes.first()
    product_attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-11",
        product_type=product_type_with_rich_text_attribute,
        category=category,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        discounted_price_amount="10.00",
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )

    associate_attribute_values_to_instance(product, product_attr, product_attr_value)

    variant_attr = product_type_with_rich_text_attribute.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(product=product, sku="123")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)
    return [product, variant]


@pytest.fixture
def product_with_collections(
    product, published_collection, unpublished_collection, collection
):
    product.collections.add(*[published_collection, unpublished_collection, collection])
    return product


@pytest.fixture
def product_available_in_many_channels(product, channel_PLN, channel_USD):
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
        discounted_price_amount=Decimal(50),
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
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_SINGLE_VARIANT")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(1.99),
        discounted_price_amount=Decimal(10),
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
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
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
            discounted_price_amount=Decimal(10),
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
    product.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product)
    )
    product.save(update_fields=["search_vector"])

    return product


@pytest.fixture
def product_with_variant_with_two_attributes(
    color_attribute, size_attribute, category, warehouse, channel_USD
):
    product_type = ProductType.objects.create(
        name="Type with two variants",
        slug="two-variants",
        kind=ProductTypeKind.NORMAL,
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
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )

    variant = ProductVariant.objects.create(product=product, sku="prodVar1")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
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
def product_with_variant_with_external_media(
    color_attribute,
    size_attribute,
    category,
    warehouse,
    channel_USD,
):
    product_type = ProductType.objects.create(
        name="Type with two variants",
        slug="two-variants",
        kind=ProductTypeKind.NORMAL,
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
    media_obj = ProductMedia.objects.create(
        product=product,
        external_url="https://www.youtube.com/watch?v=di8_dJ3Clyo",
        alt="video_1",
        type=ProductMediaTypes.VIDEO,
        oembed_data="{}",
    )
    product.media.add(media_obj)

    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        currency=channel_USD.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )

    variant = ProductVariant.objects.create(product=product, sku="prodVar1")
    variant.media.add(media_obj)
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
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
        kind=ProductTypeKind.NORMAL,
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
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )

    variant = ProductVariant.objects.create(
        product=product,
        sku="prodVarTest",
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
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
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )
    variant = ProductVariant.objects.create(
        product=product, sku="1234", track_inventory=True
    )
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=100)

    product.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product)
    )
    product.save(update_fields=["search_vector"])

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
        available_for_purchase_at=datetime.datetime.now(pytz.UTC),
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
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=0)
    return variant


@pytest.fixture
def variant(product, channel_USD) -> ProductVariant:
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_A", external_reference="SKU_A"
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    return product_variant


@pytest.fixture
def variant_with_translations(variant):
    variant.translations.create(language_code="pl", name="OldVariant PL")
    variant.translations.create(language_code="de", name="OldVariant DE")
    return variant


@pytest.fixture
def variant_with_image(variant, image_list, media_root):
    media = ProductMedia.objects.create(product=variant.product, image=image_list[0])
    VariantMedia.objects.create(variant=variant, media=media)
    return variant


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
def preorder_variant_global_threshold(product, channel_USD):
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_A_P", is_preorder=True, preorder_global_threshold=10
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    return product_variant


@pytest.fixture
def preorder_variant_channel_threshold(product, channel_USD):
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_B_P", is_preorder=True, preorder_global_threshold=None
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
        preorder_quantity_threshold=10,
    )
    return product_variant


@pytest.fixture
def preorder_variant_global_and_channel_threshold(product, channel_USD, channel_PLN):
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_C_P", is_preorder=True, preorder_global_threshold=10
    )
    ProductVariantChannelListing.objects.bulk_create(
        [
            ProductVariantChannelListing(
                variant=product_variant,
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_USD.currency_code,
                preorder_quantity_threshold=8,
            ),
            ProductVariantChannelListing(
                variant=product_variant,
                channel=channel_PLN,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                currency=channel_PLN.currency_code,
                preorder_quantity_threshold=4,
            ),
        ]
    )
    return product_variant


@pytest.fixture
def preorder_variant_with_end_date(product, channel_USD):
    product_variant = ProductVariant.objects.create(
        product=product,
        sku="SKU_D_P",
        is_preorder=True,
        preorder_global_threshold=10,
        preorder_end_date=timezone.now() + datetime.timedelta(days=10),
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    return product_variant


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
def gift_card_shippable_variant(shippable_gift_card_product, channel_USD, warehouse):
    product = shippable_gift_card_product
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_CARD_A", track_inventory=False
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(
        warehouse=warehouse, product_variant=product_variant, quantity=1
    )
    return product_variant


@pytest.fixture
def gift_card_non_shippable_variant(
    non_shippable_gift_card_product, channel_USD, warehouse
):
    product = non_shippable_gift_card_product
    product_variant = ProductVariant.objects.create(
        product=product, sku="SKU_CARD_B", track_inventory=False
    )
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(
        warehouse=warehouse, product_variant=product_variant, quantity=1
    )
    return product_variant


@pytest.fixture
def product_variant_list(product, channel_USD, channel_PLN):
    variants = list(
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(product=product, sku="1"),
                ProductVariant(product=product, sku="2"),
                ProductVariant(product=product, sku="3"),
                ProductVariant(product=product, sku="4"),
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
                discounted_price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                discounted_price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_PLN,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                discounted_price_amount=Decimal(10),
                currency=channel_PLN.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[3],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(10),
                discounted_price_amount=Decimal(10),
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
        kind=ProductTypeKind.NORMAL,
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
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_E")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
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
def product_list(
    product_type, category, warehouse, channel_USD, channel_PLN, default_tax_class
):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    products = list(
        Product.objects.bulk_create(
            [
                Product(
                    name="Test product 1",
                    slug="test-product-a",
                    description_plaintext="big blue product",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
                Product(
                    name="Test product 2",
                    slug="test-product-b",
                    description_plaintext="big orange product",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
                Product(
                    name="Test product 3",
                    slug="test-product-c",
                    description_plaintext="small red",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
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
                available_for_purchase_at=(
                    datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC)
                ),
            ),
            ProductChannelListing(
                product=products[1],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=20,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
                available_for_purchase_at=(
                    datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC)
                ),
            ),
            ProductChannelListing(
                product=products[2],
                channel=channel_USD,
                is_published=True,
                discounted_price_amount=30,
                currency=channel_USD.currency_code,
                visible_in_listings=True,
                available_for_purchase_at=(
                    datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC)
                ),
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
                discounted_price_amount=Decimal(10),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[1],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(20),
                discounted_price_amount=Decimal(20),
                currency=channel_USD.currency_code,
            ),
            ProductVariantChannelListing(
                variant=variants[2],
                channel=channel_USD,
                cost_price_amount=Decimal(1),
                price_amount=Decimal(30),
                discounted_price_amount=Decimal(30),
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
        product.search_vector = FlatConcatSearchVector(
            *prepare_product_search_vector_value(product)
        )

    Product.objects.bulk_update(products, ["search_vector"])

    return products


@pytest.fixture
def product_list_with_variants_many_channel(
    product_type, category, channel_USD, channel_PLN, default_tax_class
):
    products = list(
        Product.objects.bulk_create(
            [
                Product(
                    name="Test product 1",
                    slug="test-product-a",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
                Product(
                    name="Test product 2",
                    slug="test-product-b",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
                ),
                Product(
                    name="Test product 3",
                    slug="test-product-c",
                    category=category,
                    product_type=product_type,
                    tax_class=default_tax_class,
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
        "origin": OrderOrigin.CHECKOUT,
    }
    order = Order.objects.create(**data)
    order1 = Order.objects.create(**data)
    order2 = Order.objects.create(**data)

    return [order, order1, order2]


@pytest.fixture
def draft_order_list(order_list):
    for order in order_list:
        order.status = OrderStatus.DRAFT
        order.origin = OrderOrigin.DRAFT

    Order.objects.bulk_update(order_list, ["status", "origin"])
    return order_list


@pytest.fixture
def product_with_image(product, image, media_root):
    ProductMedia.objects.create(product=product, image=image)
    return product


@pytest.fixture
def product_with_image_list(product, image_list, media_root):
    ProductMedia.objects.create(product=product, image=image_list[0])
    ProductMedia.objects.create(product=product, image=image_list[1])
    return product


@pytest.fixture
def product_with_image_list_and_one_null_sort_order(product_with_image_list):
    """
    As we allow to have `null` in `sort_order` in database, but our logic
    covers changing any new `null` values to proper `int` need to execute
    raw SQL query on database to test behaviour of `null` `sort_order`.

    SQL query behaviour:
    Updates one of the product media `sort_order` to `null`.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE PRODUCT_PRODUCTMEDIA
            SET SORT_ORDER = NULL
            WHERE ID IN (
                SELECT ID FROM PRODUCT_PRODUCTMEDIA
                WHERE PRODUCT_ID = %s
                ORDER BY ID
                LIMIT 1
            )
            """,
            [product_with_image_list.pk],
        )
    product_with_image_list.refresh_from_db()
    return product_with_image_list


@pytest.fixture
def unavailable_product(product_type, category, channel_USD, default_tax_class):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-5",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=False,
        visible_in_listings=False,
    )
    return product


@pytest.fixture
def unavailable_product_with_variant(
    product_type, category, warehouse, channel_USD, default_tax_class
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-6",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
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
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=10)

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)
    return product


@pytest.fixture
def product_with_images(
    product_type, category, media_root, channel_USD, default_tax_class
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-7",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
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
    product.media.create(image=file_mock_0)
    product.media.create(image=file_mock_1)
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
def voucher_specific_product_type(voucher_percentage, product):
    voucher_percentage.products.add(product)
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
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
        tax_class=variant.product.tax_class,
    )


@pytest.fixture
def gift_card_non_shippable_order_line(
    order, gift_card_non_shippable_variant, warehouse
):
    variant = gift_card_non_shippable_variant
    product = variant.product
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(product, [], channel, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 1
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
    )
    Allocation.objects.create(
        order_line=line, stock=variant.stocks.first(), quantity_allocated=line.quantity
    )
    return line


@pytest.fixture
def gift_card_shippable_order_line(order, gift_card_shippable_variant, warehouse):
    variant = gift_card_shippable_variant
    product = variant.product
    channel = order.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    net = variant.get_price(product, [], channel, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
    )
    Allocation.objects.create(
        order_line=line, stock=variant.stocks.first(), quantity_allocated=line.quantity
    )
    return line


@pytest.fixture
def order_line_JPY(order_generator, channel_JPY, product_in_channel_JPY):
    order_JPY = order_generator(
        channel=channel_JPY,
        currency=channel_JPY.currency_code,
    )
    product = product_in_channel_JPY
    variant = product_in_channel_JPY.variants.get()
    channel = order_JPY.channel
    channel_listing = variant.channel_listings.get(channel=channel)
    base_price = variant.get_price(product, [], channel, channel_listing)
    currency = base_price.currency
    gross = Money(amount=base_price.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=base_price, gross=gross)
    return order_JPY.lines.create(
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=base_price,
        undiscounted_base_unit_price=base_price,
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
        origin=OrderOrigin.CHECKOUT,
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
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
    )

    Allocation.objects.bulk_create(
        [
            Allocation(order_line=order_line, stock=stocks[0], quantity_allocated=2),
            Allocation(order_line=order_line, stock=stocks[1], quantity_allocated=1),
        ]
    )

    stocks_to_update = list(stocks)
    stocks_to_update[0].quantity_allocated = 2
    stocks_to_update[1].quantity_allocated = 1

    Stock.objects.bulk_update(stocks_to_update, ["quantity_allocated"])

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
        origin=OrderOrigin.CHECKOUT,
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
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
    )

    Allocation.objects.create(
        order_line=order_line, stock=stocks[0], quantity_allocated=1
    )
    stock = stocks[0]
    stock.quantity_allocated = 1
    stock.save(update_fields=["quantity_allocated"])

    return order_line


@pytest.fixture
def checkout_line_with_reservation_in_many_stocks(
    customer_user, variant_with_many_stocks, checkout
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")
    checkout_line = checkout.lines.create(
        variant=variant,
        quantity=3,
    )

    reserved_until = timezone.now() + timedelta(minutes=5)

    Reservation.objects.bulk_create(
        [
            Reservation(
                checkout_line=checkout_line,
                stock=stocks[0],
                quantity_reserved=2,
                reserved_until=reserved_until,
            ),
            Reservation(
                checkout_line=checkout_line,
                stock=stocks[1],
                quantity_reserved=1,
                reserved_until=reserved_until,
            ),
        ]
    )

    return checkout_line


@pytest.fixture
def checkout_line_with_one_reservation(
    customer_user, variant_with_many_stocks, checkout
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all().order_by("pk")
    checkout_line = checkout.lines.create(
        variant=variant,
        quantity=2,
    )

    reserved_until = timezone.now() + timedelta(minutes=5)

    Reservation.objects.create(
        checkout_line=checkout_line,
        stock=stocks[0],
        quantity_reserved=2,
        reserved_until=reserved_until,
    )

    return checkout_line


@pytest.fixture
def checkout_line_with_preorder_item(
    checkout, product, preorder_variant_channel_threshold
):
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 1)
    return checkout.lines.last()


@pytest.fixture
def checkout_line_with_reserved_preorder_item(
    checkout, product, preorder_variant_channel_threshold
):
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    add_variant_to_checkout(checkout_info, preorder_variant_channel_threshold, 2)
    checkout_line = checkout.lines.last()

    reserved_until = timezone.now() + timedelta(minutes=5)

    PreorderReservation.objects.create(
        checkout_line=checkout_line,
        product_variant_channel_listing=checkout_line.variant.channel_listings.first(),
        quantity_reserved=2,
        reserved_until=reserved_until,
    )

    return checkout_line


@pytest.fixture
def gift_card_tag_list(db):
    tags = [GiftCardTag(name=f"test-tag-{i}") for i in range(5)]
    return GiftCardTag.objects.bulk_create(tags)


@pytest.fixture
def gift_card(customer_user):
    gift_card = GiftCard.objects.create(
        code="never_expiry",
        created_by=customer_user,
        created_by_email=customer_user.email,
        initial_balance=Money(10, "USD"),
        current_balance=Money(10, "USD"),
    )
    tag, _ = GiftCardTag.objects.get_or_create(name="test-tag")
    gift_card.tags.add(tag)
    return gift_card


@pytest.fixture
def gift_card_with_metadata(customer_user):
    return GiftCard.objects.create(
        code="card_with_meta",
        created_by=customer_user,
        created_by_email=customer_user.email,
        initial_balance=Money(10, "USD"),
        current_balance=Money(10, "USD"),
        metadata={"test": "value"},
    )


@pytest.fixture
def gift_card_expiry_date(customer_user):
    gift_card = GiftCard.objects.create(
        code="expiry_date",
        created_by=customer_user,
        created_by_email=customer_user.email,
        initial_balance=Money(20, "USD"),
        current_balance=Money(20, "USD"),
        expiry_date=datetime.date.today() + datetime.timedelta(days=100),
    )
    tag = GiftCardTag.objects.create(name="another-tag")
    gift_card.tags.add(tag)
    return gift_card


@pytest.fixture
def gift_card_used(staff_user, customer_user):
    gift_card = GiftCard.objects.create(
        code="giftcard_used",
        created_by=staff_user,
        used_by=customer_user,
        created_by_email=staff_user.email,
        used_by_email=customer_user.email,
        initial_balance=Money(100, "USD"),
        current_balance=Money(80, "USD"),
    )
    tag = GiftCardTag.objects.create(name="tag")
    gift_card.tags.add(tag)
    return gift_card


@pytest.fixture
def gift_card_created_by_staff(staff_user):
    gift_card = GiftCard.objects.create(
        code="created_by_staff",
        created_by=staff_user,
        created_by_email=staff_user.email,
        initial_balance=Money(10, "USD"),
        current_balance=Money(10, "USD"),
    )
    tag, _ = GiftCardTag.objects.get_or_create(name="test-tag")
    gift_card.tags.add(tag)
    return gift_card


@pytest.fixture
def gift_card_event(gift_card, order, app, staff_user):
    parameters = {
        "message": "test message",
        "email": "testemail@email.com",
        "tags": ["test tag"],
        "old_tags": ["test old tag"],
        "balance": {
            "currency": "USD",
            "initial_balance": 10,
            "old_initial_balance": 20,
            "current_balance": 10,
            "old_current_balance": 5,
        },
        "expiry_date": datetime.date(2050, 1, 1),
        "old_expiry_date": datetime.date(2010, 1, 1),
    }
    return GiftCardEvent.objects.create(
        user=staff_user,
        app=app,
        gift_card=gift_card,
        order=order,
        type=GiftCardEvents.UPDATED,
        parameters=parameters,
        date=timezone.now() + datetime.timedelta(days=10),
    )


@pytest.fixture
def gift_card_list():
    gift_cards = list(
        GiftCard.objects.bulk_create(
            [
                GiftCard(
                    code="code-test-1",
                    initial_balance=Money(10, "USD"),
                    current_balance=Money(10, "USD"),
                ),
                GiftCard(
                    code="code-test-2",
                    initial_balance=Money(10, "USD"),
                    current_balance=Money(10, "USD"),
                ),
                GiftCard(
                    code="code-test-3",
                    initial_balance=Money(10, "USD"),
                    current_balance=Money(10, "USD"),
                ),
            ]
        )
    )
    return gift_cards


def recalculate_order(order):
    lines = OrderLine.objects.filter(order_id=order.pk)
    prices = [line.total_price for line in lines]
    total = sum(prices, order.shipping_price)
    undiscounted_total = TaxedMoney(total.net, total.gross)

    try:
        discount = get_voucher_discount_for_order(order)
    except NotApplicable:
        discount = zero_money(order.currency)

    discount = min(discount, total.gross)
    total -= discount

    order.total = total
    order.undiscounted_total = undiscounted_total

    if discount:
        assigned_order_discount = get_voucher_discount_assigned_to_order(order)
        if assigned_order_discount:
            assigned_order_discount.amount_value = discount.amount
            assigned_order_discount.value = discount.amount
            assigned_order_discount.save(update_fields=["value", "amount_value"])

    order.save()


@pytest.fixture
def order_with_lines(
    order,
    product_type,
    category,
    shipping_zone,
    warehouse,
    channel_USD,
    default_tax_class,
):
    product = Product.objects.create(
        name="Test product",
        slug="test-product-8",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime.now(pytz.UTC),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_AA")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    stock = Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=5
    )
    base_price = variant.get_price(product, [], channel_USD, channel_listing)
    currency = base_price.currency
    gross = Money(amount=base_price.amount * Decimal(1.23), currency=currency)
    quantity = 3
    unit_price = TaxedMoney(net=base_price, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=base_price,
        undiscounted_base_unit_price=base_price,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
    )
    Allocation.objects.create(
        order_line=line, stock=stock, quantity_allocated=line.quantity
    )

    product = Product.objects.create(
        name="Test product 2",
        slug="test-product-9",
        product_type=product_type,
        category=category,
        tax_class=default_tax_class,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
        available_for_purchase_at=timezone.now(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_B")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(20),
        discounted_price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_USD.currency_code,
    )
    stock = Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=2
    )
    stock.refresh_from_db()

    base_price = variant.get_price(product, [], channel_USD, channel_listing)
    currency = base_price.currency
    gross = Money(amount=base_price.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=base_price, gross=gross)
    quantity = 2
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=base_price,
        undiscounted_base_unit_price=base_price,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
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
    order.shipping_tax_class = shipping_method.tax_class
    order.shipping_tax_class_name = shipping_method.tax_class.name
    order.shipping_tax_class_metadata = shipping_method.tax_class.metadata
    order.shipping_tax_class_private_metadata = (
        shipping_method.tax_class.private_metadata
    )  # noqa: E501

    net = shipping_price.get_total()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.shipping_price = TaxedMoney(net=net, gross=gross)
    order.base_shipping_price = net
    order.shipping_tax_rate = calculate_tax_rate(order.shipping_price)
    order.total += order.shipping_price
    order.undiscounted_total += order.shipping_price
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_with_lines_for_cc(
    warehouse_for_cc,
    channel_USD,
    customer_user,
    product_variant_list,
):
    address = customer_user.default_billing_address.get_copy()

    order = Order.objects.create(
        billing_address=address,
        channel=channel_USD,
        currency=channel_USD.currency_code,
        shipping_address=address,
        user_email=customer_user.email,
        user=customer_user,
        origin=OrderOrigin.CHECKOUT,
    )

    order.collection_point = warehouse_for_cc
    order.collection_point_name = warehouse_for_cc.name
    order.save()

    variant = product_variant_list[0]
    channel_listing = variant.channel_listings.get(channel=channel_USD)
    quantity = 1
    net = variant.get_price(product, [], channel_USD, channel_listing)
    currency = net.currency
    gross = Money(amount=net.amount * Decimal(1.23), currency=currency)
    unit_price = TaxedMoney(net=net, gross=gross)
    line = order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(variant.product.product_type.tax_class),
    )
    Allocation.objects.create(
        order_line=line,
        stock=warehouse_for_cc.stock_set.filter(product_variant=variant).first(),
        quantity_allocated=line.quantity,
    )

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_fulfill_data(order_with_lines, warehouse):
    FulfillmentData = namedtuple("FulfillmentData", "order variables warehouse")
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)
    order_line, order_line2 = order.lines.all()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.id)
    order_line2_id = graphene.Node.to_global_id("OrderLine", order_line2.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    variables = {
        "order": order_id,
        "input": {
            "notifyCustomer": False,
            "allowStockToBeExceeded": True,
            "lines": [
                {
                    "orderLineId": order_line_id,
                    "stocks": [{"quantity": 3, "warehouse": warehouse_id}],
                },
                {
                    "orderLineId": order_line2_id,
                    "stocks": [{"quantity": 2, "warehouse": warehouse_id}],
                },
            ],
        },
    }

    return FulfillmentData(order, variables, warehouse)


@pytest.fixture
def lines_info(order_with_lines):
    return [
        OrderLineInfo(
            line=line,
            quantity=line.quantity,
            variant=line.variant,
            warehouse_pk=line.allocations.first().stock.warehouse.pk,
        )
        for line in order_with_lines.lines.all()
    ]


@pytest.fixture
def order_with_lines_and_events(order_with_lines, staff_user):
    events = []
    for event_type, _ in OrderEvents.CHOICES:
        events.append(
            OrderEvent(
                type=event_type,
                order=order_with_lines,
                user=staff_user,
            )
        )
    OrderEvent.objects.bulk_create(events)
    fulfillment_refunded_event(
        order=order_with_lines,
        user=staff_user,
        app=None,
        refunded_lines=[(1, order_with_lines.lines.first())],
        amount=Decimal("10.0"),
        shipping_costs_included=False,
    )
    order_added_products_event(
        order=order_with_lines,
        user=staff_user,
        app=None,
        order_lines=[order_with_lines.lines.first()],
        quantity_diff=1,
    )
    return order_with_lines


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
        origin=OrderOrigin.CHECKOUT,
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
        available_for_purchase_at=timezone.now(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_A_PLN")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
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
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
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
        available_for_purchase_at=timezone.now(),
    )
    variant = ProductVariant.objects.create(product=product, sku="SKU_B_PLN")
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=Decimal(20),
        discounted_price_amount=Decimal(20),
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
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
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
    order.base_shipping_price = net
    order.shipping_tax_rate = calculate_tax_rate(order.shipping_price)
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
    order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(product.product_type.tax_class),
    )

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_with_preorder_lines(
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
        available_for_purchase_at=timezone.now(),
    )
    variant = ProductVariant.objects.create(
        product=product, sku="SKU_AA_P", is_preorder=True
    )
    channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
        preorder_quantity_threshold=10,
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
        is_gift_card=variant.is_gift_card(),
        quantity=quantity,
        variant=variant,
        unit_price=unit_price,
        total_price=unit_price * quantity,
        undiscounted_unit_price=unit_price,
        undiscounted_total_price=unit_price * quantity,
        base_unit_price=unit_price.gross,
        undiscounted_base_unit_price=unit_price.gross,
        tax_rate=Decimal("0.23"),
        **get_tax_class_kwargs_for_order_line(product_type.tax_class),
    )
    PreorderAllocation.objects.create(
        order_line=line,
        product_variant_channel_listing=channel_listing,
        quantity=line.quantity,
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
    order.base_shipping_price = net
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_events(order):
    order_events = [
        OrderEvent(type=event_type, order=order)
        for event_type, _ in OrderEvents.CHOICES
    ]
    OrderEvent.objects.bulk_create(order_events)
    return order_events


@pytest.fixture
def fulfilled_order(order_with_lines):
    order = order_with_lines
    order.invoices.create(
        url="http://www.example.com/invoice.pdf",
        number="01/12/2020/TEST",
        created_at=datetime.datetime.now(tz=pytz.utc),
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
    fulfillment.lines.create(order_line=line_2, quantity=line_2.quantity, stock=stock_2)
    fulfill_order_lines(
        [
            OrderLineInfo(
                line=line_1, quantity=line_1.quantity, warehouse_pk=warehouse_1_pk
            ),
            OrderLineInfo(
                line=line_2, quantity=line_2.quantity, warehouse_pk=warehouse_2_pk
            ),
        ],
        manager=get_plugins_manager(),
    )
    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def unconfirmed_order_with_lines(order_with_lines):
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
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
    fulfill_order_lines(
        [OrderLineInfo(line=line, quantity=line.quantity, warehouse_pk=warehouse_pk)],
        get_plugins_manager(),
    )
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
    cancel_fulfillment(fulfillment, staff_user, None, warehouse, get_plugins_manager())
    return fulfilled_order


@pytest.fixture
def fulfillment(fulfilled_order):
    return fulfilled_order.fulfillments.first()


@pytest.fixture
def fulfillment_awaiting_approval(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.save(update_fields=["status"])

    quantity = 1
    fulfillment_lines_to_update = []
    order_lines_to_update = []
    for f_line in fulfillment.lines.all():
        f_line.quantity = quantity
        fulfillment_lines_to_update.append(f_line)

        order_line = f_line.order_line
        order_line.quantity_fulfilled = quantity
        order_lines_to_update.append(order_line)

    FulfillmentLine.objects.bulk_update(fulfillment_lines_to_update, ["quantity"])
    OrderLine.objects.bulk_update(order_lines_to_update, ["quantity_fulfilled"])

    return fulfillment


@pytest.fixture
def draft_order(order_with_lines):
    Allocation.objects.filter(order_line__order=order_with_lines).delete()
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.origin = OrderOrigin.DRAFT
    order_with_lines.save(update_fields=["status", "origin"])
    return order_with_lines


@pytest.fixture
def draft_order_with_fixed_discount_order(draft_order):
    value = Decimal("20")
    discount = partial(fixed_discount, discount=Money(value, draft_order.currency))
    draft_order.total = discount(draft_order.total)
    draft_order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=value,
        reason="Discount reason",
        amount=(draft_order.undiscounted_total - draft_order.total).gross,
    )
    draft_order.save()
    return draft_order


@pytest.fixture
def draft_order_without_inventory_tracking(order_with_line_without_inventory_tracking):
    order_with_line_without_inventory_tracking.status = OrderStatus.DRAFT
    order_with_line_without_inventory_tracking.origin = OrderStatus.DRAFT
    order_with_line_without_inventory_tracking.save(update_fields=["status", "origin"])
    return order_with_line_without_inventory_tracking


@pytest.fixture
def draft_order_with_preorder_lines(order_with_preorder_lines):
    PreorderAllocation.objects.filter(
        order_line__order=order_with_preorder_lines
    ).delete()
    order_with_preorder_lines.status = OrderStatus.DRAFT
    order_with_preorder_lines.origin = OrderOrigin.DRAFT
    order_with_preorder_lines.save(update_fields=["status", "origin"])
    return order_with_preorder_lines


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
def payment_txn_capture_failed(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.charge_status = ChargeStatus.REFUSED
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        currency=payment.currency,
        kind=TransactionKind.CAPTURE_FAILED,
        gateway_response={
            "status": 403,
            "errorCode": "901",
            "message": "Invalid Merchant Account",
            "errorType": "security",
        },
        error="invalid",
        is_success=False,
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
        gateway=payment_dummy.gateway,
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
def dummy_address_data(address):
    return AddressData(
        first_name=address.first_name,
        last_name=address.last_name,
        company_name=address.company_name,
        street_address_1=address.street_address_1,
        street_address_2=address.street_address_2,
        city=address.city,
        city_area=address.city_area,
        postal_code=address.postal_code,
        country=address.country,
        country_area=address.country_area,
        phone=address.phone,
        metadata=address.metadata,
        private_metadata=address.private_metadata,
    )


@pytest.fixture
def dummy_webhook_app_payment_data(dummy_payment_data, payment_app):
    dummy_payment_data.gateway = to_payment_app_id(payment_app, "credit-card")
    return dummy_payment_data


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
def sale(product, category, collection, variant, channel_USD):
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
    sale.variants.add(variant)
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
        variants_ids=set(),
    )


@pytest.fixture
def discount_info_JPY(sale, product_in_channel_JPY, channel_JPY):
    sale_channel_listing = sale.channel_listings.create(
        channel=channel_JPY,
        discount_value=5,
        currency=channel_JPY.currency_code,
    )

    return DiscountInfo(
        sale=sale,
        channel_listings={channel_JPY.slug: sale_channel_listing},
        product_ids={product_in_channel_JPY.id},
        category_ids=set(),
        collection_ids=set(),
        variants_ids=set(),
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
def permission_impersonate_user():
    return Permission.objects.get(codename="impersonate_user")


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
def permission_manage_payments():
    return Permission.objects.get(codename="handle_payments")


@pytest.fixture
def permission_group_manage_orders(permission_manage_orders, staff_users):
    group = Group.objects.create(
        name="Manage orders group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_orders)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_shipping(permission_manage_shipping, staff_users):
    group = Group.objects.create(
        name="Manage shipping group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_shipping)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_users(permission_manage_users, staff_users):
    group = Group.objects.create(
        name="Manage user group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_users)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_staff(permission_manage_staff, staff_users):
    group = Group.objects.create(
        name="Manage staff group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_staff)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_apps(permission_manage_apps, staff_users):
    group = Group.objects.create(
        name="Manage apps group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_apps)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_handle_payments(permission_manage_payments, staff_users):
    group = Group.objects.create(
        name="Manage apps group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_payments)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_all_perms_all_channels(
    permission_manage_users, staff_users, channel_USD, channel_PLN
):
    group = Group.objects.create(
        name="All permissions for all channels.",
        restricted_access_to_channels=False,
    )
    permissions = get_permissions()
    group.permissions.add(*permissions)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_no_perms_all_channels(staff_users, channel_USD, channel_PLN):
    group = Group.objects.create(
        name="All permissions for all channels.",
        restricted_access_to_channels=False,
    )
    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_all_perms_channel_USD_only(
    permission_manage_users, staff_users, channel_USD, channel_PLN
):
    group = Group.objects.create(
        name="All permissions for USD channel only.",
        restricted_access_to_channels=True,
    )
    permissions = get_permissions()
    group.permissions.add(*permissions)

    group.channels.add(channel_USD)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_all_perms_without_any_channel(
    permission_manage_users, staff_users, channel_USD, channel_PLN
):
    group = Group.objects.create(
        name="All permissions without any channel access.",
        restricted_access_to_channels=True,
    )
    permissions = get_permissions()
    group.permissions.add(*permissions)
    return group


@pytest.fixture
def collection(db):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        description=dummy_editorjs("Test description."),
    )
    return collection


@pytest.fixture
def published_collection(db, channel_USD):
    collection = Collection.objects.create(
        name="Collection USD",
        slug="collection-usd",
        description=dummy_editorjs("Test description."),
    )
    CollectionChannelListing.objects.create(
        channel=channel_USD,
        collection=collection,
        is_published=True,
        published_at=timezone.now(),
    )
    return collection


@pytest.fixture
def published_collections(db, channel_USD):
    collections = Collection.objects.bulk_create(
        [
            Collection(
                name="Collection1",
                slug="coll1",
            ),
            Collection(
                name="Collection2",
                slug="coll2",
            ),
            Collection(
                name="Collection3",
                slug="coll3",
            ),
        ]
    )
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                channel=channel_USD,
                collection=collection,
                is_published=True,
                published_at=datetime.datetime(
                    2019, 4, 10, tzinfo=timezone.get_current_timezone()
                ),
            )
            for collection in collections
        ]
    )

    return collections


@pytest.fixture
def published_collection_PLN(db, channel_PLN):
    collection = Collection.objects.create(
        name="Collection PLN",
        slug="collection-pln",
        description=dummy_editorjs("Test description."),
    )
    CollectionChannelListing.objects.create(
        channel=channel_PLN,
        collection=collection,
        is_published=True,
        published_at=timezone.now(),
    )
    return collection


@pytest.fixture
def unpublished_collection(db, channel_USD):
    collection = Collection.objects.create(
        name="Unpublished Collection",
        slug="unpublished-collection",
        description=dummy_editorjs("Test description."),
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
        description=dummy_editorjs("Test description."),
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
        description=dummy_editorjs("Test description."),
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
        "content": dummy_editorjs("Test content."),
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
def second_page(page):
    data = {
        "slug": "test-url-2",
        "title": "Test page 2",
        "content": dummy_editorjs("Test content 2."),
        "is_published": True,
        "page_type": page.page_type,
    }
    page2 = Page.objects.create(**data)

    # associate attribute value to the second page
    page_attr = page.page_type.page_attributes.first()
    page_attr_value = page_attr.values.first()

    associate_attribute_values_to_instance(page2, page_attr, page_attr_value)

    attribute = Attribute.objects.create(
        slug="test-attribute",
        name="Test Attribute",
        type="some_attribute_type",
        input_type=AttributeInputType.DROPDOWN,
    )
    attribute.page_types.add(page.page_type)

    attribute_values = []
    for i in range(10):
        attribute_values.append(
            AttributeValue.objects.create(
                attribute=attribute,
                name=f"Test-name-attribute-value-{i}",
                slug=f"test-slug-attribute-value-{i}",
            )
        )
    associate_attribute_values_to_instance(page2, attribute, *attribute_values)
    return page, page2


@pytest.fixture
def page_with_rich_text_attribute(db, page_type_with_rich_text_attribute):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "content": dummy_editorjs("Test content."),
        "is_published": True,
        "page_type": page_type_with_rich_text_attribute,
    }
    page = Page.objects.create(**data)

    # associate attribute value
    page_attr = page_type_with_rich_text_attribute.page_attributes.first()
    page_attr_value = page_attr.values.first()

    associate_attribute_values_to_instance(page, page_attr, page_attr_value)

    return page


@pytest.fixture
def page_list(db, page_type):
    data_1 = {
        "slug": "test-url-1",
        "title": "Test page",
        "content": dummy_editorjs("Test content."),
        "is_published": True,
        "page_type": page_type,
    }
    data_2 = {
        "slug": "test-url-2",
        "title": "Test page",
        "content": dummy_editorjs("Test content."),
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
def page_type_with_rich_text_attribute(db, rich_text_attribute_page_type):
    page_type = PageType.objects.create(name="Test page type", slug="test-page-type")
    page_type.page_attributes.add(rich_text_attribute_page_type)
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
def translated_page_unique_attribute_value(page, rich_text_attribute_page_type):
    page_type = page.page_type
    page_type.page_attributes.add(rich_text_attribute_page_type)
    attribute_value = rich_text_attribute_page_type.values.first()
    associate_attribute_values_to_instance(
        page, rich_text_attribute_page_type, attribute_value
    )
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attribute_value,
        rich_text=dummy_editorjs("French description."),
    )


@pytest.fixture
def translated_product_unique_attribute_value(product, rich_text_attribute):
    product_type = product.product_type
    product_type.product_attributes.add(rich_text_attribute)
    attribute_value = rich_text_attribute.values.first()
    associate_attribute_values_to_instance(
        product, rich_text_attribute, attribute_value
    )
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attribute_value,
        rich_text=dummy_editorjs("French description."),
    )


@pytest.fixture
def translated_variant_unique_attribute_value(variant, rich_text_attribute):
    product_type = variant.product.product_type
    product_type.variant_attributes.add(rich_text_attribute)
    attribute_value = rich_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, rich_text_attribute, attribute_value
    )
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=attribute_value,
        rich_text=dummy_editorjs("French description."),
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
        description=dummy_editorjs("French description."),
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
        description=dummy_editorjs("French description."),
    )


@pytest.fixture
def category_translation_fr(category):
    return CategoryTranslation.objects.create(
        language_code="fr",
        category=category,
        name="French category name",
        description=dummy_editorjs("French category description."),
    )


@pytest.fixture
def page_translation_fr(page):
    return PageTranslation.objects.create(
        language_code="fr",
        page=page,
        title="French page title",
        content=dummy_editorjs("French page content."),
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
def new_sale_translation_fr(new_sale):
    return SaleTranslation.objects.create(
        language_code="fr", sale=new_sale, name="French sale name"
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
def payments_dummy(order_with_lines):
    return Payment.objects.bulk_create(
        [
            Payment(
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
            for _ in range(3)
        ]
    )


@pytest.fixture
def payment(payment_dummy, payment_app):
    gateway_id = "credit-card"
    gateway = to_payment_app_id(payment_app, gateway_id)
    payment_dummy.gateway = gateway
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def payment_cancelled(payment_dummy):
    payment_dummy.charge_status = ChargeStatus.CANCELLED
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def payment_dummy_fully_charged(payment_dummy):
    payment_dummy.captured_amount = payment_dummy.total
    payment_dummy.charge_status = ChargeStatus.FULLY_CHARGED
    payment_dummy.save()
    return payment_dummy


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
def transaction_item_generator():
    def create_transaction(
        order_id=None,
        checkout_id=None,
        app=None,
        user=None,
        psp_reference="PSP ref1",
        name="Credit card",
        message="Transasction details",
        available_actions=None,
        authorized_value=Decimal(0),
        charged_value=Decimal(0),
        refunded_value=Decimal(0),
        canceled_value=Decimal(0),
        use_old_id=False,
    ):
        if available_actions is None:
            available_actions = []
        transaction = TransactionItem.objects.create(
            token=uuid.uuid4(),
            name=name,
            message=message,
            psp_reference=psp_reference,
            available_actions=available_actions,
            currency="USD",
            order_id=order_id,
            checkout_id=checkout_id,
            app_identifier=app.identifier if app else None,
            app=app,
            user=user,
            use_old_id=use_old_id,
        )
        create_manual_adjustment_events(
            transaction=transaction,
            money_data={
                "authorized_value": authorized_value,
                "charged_value": charged_value,
                "refunded_value": refunded_value,
                "canceled_value": canceled_value,
            },
            user=user,
            app=app,
        )
        recalculate_transaction_amounts(transaction)
        return transaction

    return create_transaction


@pytest.fixture
def transaction_events_generator() -> (
    Callable[
        [List[str], List[str], List[Decimal], TransactionItem], List[TransactionEvent]
    ]
):
    def factory(
        psp_references: List[str],
        types: List[str],
        amounts: List[Decimal],
        transaction: TransactionItem,
    ):
        return TransactionEvent.objects.bulk_create(
            TransactionEvent(
                transaction=transaction,
                psp_reference=reference,
                type=event_type,
                amount_value=amount,
                include_in_calculations=True,
                currency=transaction.currency,
            )
            for reference, event_type, amount in zip(psp_references, types, amounts)
        )

    return factory


@pytest.fixture
def transaction_item_created_by_app(order, app, transaction_item_generator):
    charged_amount = Decimal("10.0")
    return transaction_item_generator(
        order_id=order.pk,
        checkout_id=None,
        app=app,
        user=None,
        charged_value=charged_amount,
    )


@pytest.fixture
def transaction_item_created_by_user(order, staff_user, transaction_item_generator):
    charged_amount = Decimal("10.0")
    return transaction_item_generator(
        order_id=order.pk,
        checkout_id=None,
        user=staff_user,
        app=None,
        charged_value=charged_amount,
    )


@pytest.fixture
def transaction_item(order, transaction_item_generator):
    return transaction_item_generator(
        order_id=order.pk,
    )


@pytest.fixture
def digital_content(category, media_root, warehouse, channel_USD) -> DigitalContent:
    product_type = ProductType.objects.create(
        name="Digital Type",
        slug="digital-type",
        kind=ProductTypeKind.NORMAL,
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
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=pytz.UTC),
    )
    product_variant = ProductVariant.objects.create(product=product, sku="SKU_554")
    ProductVariantChannelListing.objects.create(
        variant=product_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        discounted_price_amount=Decimal(10),
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
                "data": {
                    "text": "E-commerce for the PWA era",
                },
                "text": "E-commerce for the PWA era",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {
                    "text": (
                        "A modular, high performance e-commerce storefront "
                        "built with GraphQL, Django, and ReactJS."
                    )
                },
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "",
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {
                    "text": (
                        "Saleor is a rapidly-growing open source e-commerce platform "
                        "that has served high-volume companies from branches "
                        "like publishing and apparel since 2012. Based on Python "
                        "and Django, the latest major update introduces a modular "
                        "front end with a GraphQL API and storefront and dashboard "
                        "written in React to make Saleor a full-functionality "
                        "open source e-commerce."
                    ),
                },
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {"text": ""},
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {
                    "text": "Get Saleor today!",
                },
                "type": "paragraph",
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
                "data": {
                    "text": (
                        "A GRAPHQL-FIRST <b>ECOMMERCE</b> PLATFORM FOR PERFECTIONISTS"
                    ),
                },
                "text": "A GRAPHQL-FIRST ECOMMERCE PLATFORM FOR PERFECTIONISTS",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {
                    "text": (
                        "Saleor is powered by a GraphQL server running on "
                        "top of Python 3 and a Django 2 framework."
                    ),
                },
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
        ],
        "entityMap": {},
    }


@pytest.fixture
def app(db):
    app = App.objects.create(
        name="Sample app objects",
        is_active=True,
        identifier="saleor.app.test",
    )
    return app


@pytest.fixture
def webhook_app(
    db,
    permission_manage_shipping,
    permission_manage_gift_card,
    permission_manage_discounts,
    permission_manage_menus,
    permission_manage_products,
    permission_manage_staff,
    permission_manage_orders,
    permission_manage_users,
):
    app = App.objects.create(name="Webhook app", is_active=True)
    app.permissions.add(permission_manage_shipping)
    app.permissions.add(permission_manage_gift_card)
    app.permissions.add(permission_manage_discounts)
    app.permissions.add(permission_manage_menus)
    app.permissions.add(permission_manage_products)
    app.permissions.add(permission_manage_staff)
    app.permissions.add(permission_manage_orders)
    app.permissions.add(permission_manage_users)
    return app


@pytest.fixture
def app_with_token(db):
    app = App.objects.create(name="Sample app objects", is_active=True)
    app.tokens.create(name="Test")
    return app


@pytest.fixture
def app_with_extensions(app_with_token, permission_manage_products):
    first_app_extension = AppExtension(
        app=app_with_token,
        label="Create product with App",
        url="www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    extensions = AppExtension.objects.bulk_create(
        [
            first_app_extension,
            AppExtension(
                app=app_with_token,
                label="Update product with App",
                url="www.example.com/app-product-update",
                mount=AppExtensionMount.PRODUCT_DETAILS_MORE_ACTIONS,
            ),
        ]
    )
    first_app_extension.permissions.add(permission_manage_products)
    return app_with_token, extensions


@pytest.fixture
def payment_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment App", is_active=True, identifier="saleor.payment.test.app"
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment-webhook-1",
        app=app,
        target_url="https://payment-gateway.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in WebhookEventSyncType.PAYMENT_EVENTS
        ]
    )
    return app


@pytest.fixture
def payment_app_with_subscription_webhooks(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment App", is_active=True, identifier="saleor.payment.test.app"
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment-subscription-webhook-1",
        app=app,
        target_url="https://payment-gateway.com/api/",
        subscription_query=subscription_queries.PAYMENT_AUTHORIZE,
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in WebhookEventSyncType.PAYMENT_EVENTS
        ]
    )
    return app


@pytest.fixture
def shipping_app(db, permission_manage_shipping):
    app = App.objects.create(name="Shipping App", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_shipping)

    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-app.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                WebhookEventAsyncType.FULFILLMENT_CREATED,
            ]
        ]
    )
    return app


@pytest.fixture
def list_stored_payment_methods_app(db, permission_manage_payments):
    app = App.objects.create(
        name="List payment methods app",
        is_active=True,
        identifier="saleor.payment.app.list.stored.method",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="list_stored_payment_methods",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
    )
    return app


@pytest.fixture
def stored_payment_method_request_delete_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment method request delete",
        is_active=True,
        identifier="saleor.payment.app.payment.method.request.delete",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="stored_payment_method_request_delete",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.STORED_PAYMENT_METHOD_DELETE_REQUESTED,
    )
    return app


@pytest.fixture
def payment_gateway_initialize_tokenization_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment method request delete",
        is_active=True,
        identifier="saleor.payment.app.payment.gateway.initialize.tokenization",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment_gateway_initialize_tokenization",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION,
    )
    return app


@pytest.fixture
def payment_method_initialize_tokenization_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment method initialize tokenization",
        is_active=True,
        identifier="saleor.payment.app.payment.method.initialize.tokenization",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment_method_initialize_tokenization",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION,
    )
    return app


@pytest.fixture
def payment_method_process_tokenization_app(db, permission_manage_payments):
    app = App.objects.create(
        name="Payment method process tokenization",
        is_active=True,
        identifier="saleor.payment.app.payment.method.process.tokenization",
    )
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_payments)

    webhook = Webhook.objects.create(
        name="payment_method_process_tokenization",
        app=app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION,
    )
    return app


@pytest.fixture
def tax_app(db, permission_handle_taxes):
    app = App.objects.create(name="Tax App", is_active=True)
    app.permissions.add(permission_handle_taxes)

    webhook = Webhook.objects.create(
        name="tax-webhook-1",
        app=app,
        target_url="https://tax-app.com/api/",
    )
    webhook.events.bulk_create(
        [
            WebhookEvent(event_type=event_type, webhook=webhook)
            for event_type in [
                WebhookEventSyncType.ORDER_CALCULATE_TAXES,
                WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            ]
        ]
    )
    return app


@pytest.fixture
def observability_webhook(db, permission_manage_observability):
    app = App.objects.create(name="Observability App", is_active=True)
    app.tokens.create(name="Default")
    app.permissions.add(permission_manage_observability)

    webhook = Webhook.objects.create(
        name="observability-webhook-1",
        app=app,
        target_url="https://observability-app.com/api/",
    )
    webhook.events.create(event_type=WebhookEventAsyncType.OBSERVABILITY)
    return webhook


@pytest.fixture
def observability_webhook_data(observability_webhook):
    return WebhookData(
        id=observability_webhook.id,
        saleor_domain="mirumee.com",
        target_url=observability_webhook.target_url,
        secret_key=observability_webhook.secret_key,
    )


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
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    return webhook


@pytest.fixture
def webhook_without_name(app):
    webhook = Webhook.objects.create(app=app, target_url="http://www.example.com/test")
    webhook.events.create(event_type=WebhookEventAsyncType.ORDER_CREATED)
    return webhook


@pytest.fixture
def any_webhook(app):
    webhook = Webhook.objects.create(
        name="Any webhook", app=app, target_url="http://www.example.com/any"
    )
    webhook.events.create(event_type=WebhookEventAsyncType.ANY)
    return webhook


@pytest.fixture
def fake_payment_interface(mocker):
    return mocker.Mock(spec=PaymentInterface)


@pytest.fixture
def staff_notification_recipient(db, staff_user):
    return StaffNotificationRecipient.objects.create(active=True, user=staff_user)


@pytest.fixture
def warehouse(address, shipping_zone, channel_USD):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Example Warehouse",
        slug="example-warehouse",
        email="test@example.com",
    )
    warehouse.shipping_zones.add(shipping_zone)
    warehouse.channels.add(channel_USD)
    warehouse.save()
    return warehouse


@pytest.fixture
def warehouse_with_external_ref(address, shipping_zone, channel_USD):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Example Warehouse With Ref",
        slug="example-warehouse-with-ref",
        email="test@example.com",
        external_reference="example-warehouse-with-ref",
    )
    warehouse.shipping_zones.add(shipping_zone)
    warehouse.channels.add(channel_USD)
    warehouse.save()
    return warehouse


@pytest.fixture
def warehouse_JPY(address, shipping_zone_JPY, channel_JPY):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Example Warehouse JPY",
        slug="example-warehouse-jpy",
        email="test-jpy@example.com",
    )
    warehouse.shipping_zones.add(shipping_zone_JPY)
    warehouse.channels.add(channel_JPY)
    warehouse.save()
    return warehouse


@pytest.fixture
def warehouses(address, address_usa, channel_USD):
    warehouses = Warehouse.objects.bulk_create(
        [
            Warehouse(
                address=address.get_copy(),
                name="Warehouse PL",
                slug="warehouse1",
                email="warehouse1@example.com",
                external_reference="warehouse1",
            ),
            Warehouse(
                address=address_usa.get_copy(),
                name="Warehouse USA",
                slug="warehouse2",
                email="warehouse2@example.com",
                external_reference="warehouse2",
            ),
        ]
    )
    for warehouse in warehouses:
        warehouse.channels.add(channel_USD)
    return warehouses


@pytest.fixture()
def warehouses_for_cc(address, shipping_zones, channel_USD):
    warehouses = Warehouse.objects.bulk_create(
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
                click_and_collect_option=WarehouseClickAndCollectOption.ALL_WAREHOUSES,
            ),
            Warehouse(
                address=address.get_copy(),
                name="Warehouse3",
                slug="warehouse3",
                email="warehouse3@example.com",
                click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
                is_private=False,
            ),
            Warehouse(
                address=address.get_copy(),
                name="Warehouse4",
                slug="warehouse4",
                email="warehouse4@example.com",
                click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
                is_private=False,
            ),
        ]
    )
    # add to shipping zones only not click and collect warehouses
    warehouses[0].shipping_zones.add(*shipping_zones)
    channel_USD.warehouses.add(*warehouses)
    return warehouses


@pytest.fixture
def warehouse_for_cc(address, product_variant_list, channel_USD):
    warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="Local Warehouse",
        slug="local-warehouse",
        email="local@example.com",
        is_private=False,
        click_and_collect_option=WarehouseClickAndCollectOption.LOCAL_STOCK,
    )
    warehouse.channels.add(channel_USD)

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=warehouse, product_variant=product_variant_list[0], quantity=1
            ),
            Stock(
                warehouse=warehouse, product_variant=product_variant_list[1], quantity=2
            ),
            Stock(
                warehouse=warehouse, product_variant=product_variant_list[2], quantity=2
            ),
        ]
    )
    return warehouse


@pytest.fixture(params=["warehouse_for_cc", "shipping_method"])
def delivery_method(request, warehouse_for_cc, shipping_method):
    if request.param == "warehouse":
        return warehouse_for_cc
    if request.param == "shipping_method":
        return shipping_method


@pytest.fixture
def stocks_for_cc(warehouses_for_cc, product_variant_list, product_with_two_variants):
    return Stock.objects.bulk_create(
        [
            Stock(
                warehouse=warehouses_for_cc[0],
                product_variant=product_variant_list[0],
                quantity=5,
            ),
            Stock(
                warehouse=warehouses_for_cc[1],
                product_variant=product_variant_list[0],
                quantity=3,
            ),
            Stock(
                warehouse=warehouses_for_cc[1],
                product_variant=product_variant_list[1],
                quantity=10,
            ),
            Stock(
                warehouse=warehouses_for_cc[1],
                product_variant=product_variant_list[2],
                quantity=10,
            ),
            Stock(
                warehouse=warehouses_for_cc[2],
                product_variant=product_variant_list[0],
                quantity=3,
            ),
            Stock(
                warehouse=warehouses_for_cc[3],
                product_variant=product_variant_list[0],
                quantity=3,
            ),
            Stock(
                warehouse=warehouses_for_cc[3],
                product_variant=product_variant_list[1],
                quantity=3,
            ),
            Stock(
                warehouse=warehouses_for_cc[3],
                product_variant=product_with_two_variants.variants.last(),
                quantity=7,
            ),
            Stock(
                warehouse=warehouses_for_cc[3],
                product_variant=product_variant_list[2],
                quantity=3,
            ),
        ]
    )


@pytest.fixture
def checkout_for_cc(channel_USD, customer_user):
    checkout = Checkout.objects.create(
        channel=channel_USD,
        billing_address=customer_user.default_billing_address,
        shipping_address=customer_user.default_shipping_address,
        note="Test notes",
        currency="USD",
        email=customer_user.email,
    )
    CheckoutMetadata.objects.create(checkout=checkout)
    return checkout


@pytest.fixture
def checkout_with_items_for_cc(checkout_for_cc, product_variant_list):
    CheckoutLine.objects.bulk_create(
        [
            CheckoutLine(
                checkout=checkout_for_cc,
                variant=product_variant_list[0],
                quantity=1,
                currency=checkout_for_cc.currency,
            ),
            CheckoutLine(
                checkout=checkout_for_cc,
                variant=product_variant_list[1],
                quantity=1,
                currency=checkout_for_cc.currency,
            ),
            CheckoutLine(
                checkout=checkout_for_cc,
                variant=product_variant_list[2],
                quantity=1,
                currency=checkout_for_cc.currency,
            ),
        ]
    )
    checkout_for_cc.set_country("US", commit=True)

    return checkout_for_cc


@pytest.fixture
def checkout_with_item_for_cc(checkout_for_cc, product_variant_list):
    CheckoutLine.objects.create(
        checkout=checkout_for_cc,
        variant=product_variant_list[0],
        quantity=1,
        currency=checkout_for_cc.currency,
    )
    return checkout_for_cc


@pytest.fixture
def checkout_with_prices(
    checkout_with_items,
    address,
    address_other_country,
    warehouse,
    customer_user,
    shipping_method,
    voucher,
):
    # Need to save shipping_method before fetching checkout info.
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.save(update_fields=["shipping_method"])

    manager = get_plugins_manager()
    channel = checkout_with_items.channel
    lines = checkout_with_items.lines.all()
    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines, manager)

    for line, line_info in zip(lines, lines_info):
        line.total_price_net_amount = base_calculations.calculate_base_line_total_price(
            line_info, channel
        ).amount
        line.total_price_gross_amount = line.total_price_net_amount * Decimal("1.230")

    checkout_with_items.discount_amount = Decimal("5.000")
    checkout_with_items.discount_name = "Voucher 5 USD"
    checkout_with_items.user = customer_user
    checkout_with_items.billing_address = address
    checkout_with_items.shipping_address = address_other_country
    checkout_with_items.collection_point = warehouse
    checkout_with_items.subtotal_net_amount = Decimal("100.000")
    checkout_with_items.subtotal_gross_amount = Decimal("123.000")
    checkout_with_items.total_net_amount = Decimal("150.000")
    checkout_with_items.total_gross_amount = Decimal("178.000")
    shipping_amount = base_calculations.base_checkout_delivery_price(
        checkout_info, lines_info
    ).amount
    checkout_with_items.shipping_price_net_amount = shipping_amount
    checkout_with_items.shipping_price_gross_amount = shipping_amount * Decimal("1.08")
    checkout_with_items.metadata_storage.metadata = {"meta_key": "meta_value"}
    checkout_with_items.metadata_storage.private_metadata = {
        "priv_meta_key": "priv_meta_value"
    }

    checkout_with_items.lines.bulk_update(
        lines,
        [
            "total_price_net_amount",
            "total_price_gross_amount",
        ],
    )

    checkout_with_items.save(
        update_fields=[
            "discount_amount",
            "discount_name",
            "user",
            "billing_address",
            "shipping_address",
            "collection_point",
            "subtotal_net_amount",
            "subtotal_gross_amount",
            "total_net_amount",
            "total_gross_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
        ]
    )
    checkout_with_items.metadata_storage.save(
        update_fields=["metadata", "private_metadata"]
    )

    user = checkout_with_items.user
    user.metadata = {"user_public_meta_key": "user_public_meta_value"}
    user.save(update_fields=["metadata"])

    return checkout_with_items


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
def warehouse_no_shipping_zone(address, channel_USD):
    warehouse = Warehouse.objects.create(
        address=address,
        name="Warehouse without shipping zone",
        slug="warehouse-no-shipping-zone",
        email="test2@example.com",
    )
    warehouse.channels.add(channel_USD)
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
                product_variant_id=variant.get_global_id(),
                is_shipping_required=variant.is_shipping_required(),
                is_gift_card=variant.is_gift_card(),
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
                **get_tax_class_kwargs_for_order_line(product.product_type.tax_class),
            ),
            OrderLine(
                order=order_list[1],
                variant=variant,
                quantity=2,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                product_variant_id=variant.get_global_id(),
                is_shipping_required=variant.is_shipping_required(),
                is_gift_card=variant.is_gift_card(),
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
                **get_tax_class_kwargs_for_order_line(product.product_type.tax_class),
            ),
            OrderLine(
                order=order_list[2],
                variant=variant,
                quantity=4,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                product_variant_id=variant.get_global_id(),
                is_shipping_required=variant.is_shipping_required(),
                is_gift_card=variant.is_gift_card(),
                unit_price=price,
                total_price=price,
                tax_rate=Decimal("0.23"),
                **get_tax_class_kwargs_for_order_line(product.product_type.tax_class),
            ),
        ]
    )

    for order in order_list:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(order_list, ["search_vector"])

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
def preorder_allocation(
    order_line, preorder_variant_global_and_channel_threshold, channel_PLN
):
    variant = preorder_variant_global_and_channel_threshold
    product_variant_channel_listing = variant.channel_listings.get(channel=channel_PLN)
    return PreorderAllocation.objects.create(
        order_line=order_line,
        product_variant_channel_listing=product_variant_channel_listing,
        quantity=order_line.quantity,
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


@pytest.fixture
def app_manifest():
    return {
        "name": "Sample Saleor App",
        "version": "0.1",
        "about": "Sample Saleor App serving as an example.",
        "dataPrivacy": "",
        "dataPrivacyUrl": "",
        "homepageUrl": "http://172.17.0.1:5000/homepageUrl",
        "supportUrl": "http://172.17.0.1:5000/supportUrl",
        "id": "saleor-complex-sample",
        "permissions": ["MANAGE_PRODUCTS", "MANAGE_USERS"],
        "appUrl": "",
        "configurationUrl": "http://127.0.0.1:5000/configuration/",
        "tokenTargetUrl": "http://127.0.0.1:5000/configuration/install",
    }


@pytest.fixture
def app_manifest_webhook():
    return {
        "name": "webhook",
        "asyncEvents": [
            "ORDER_CREATED",
            "ORDER_FULLY_PAID",
            "CUSTOMER_CREATED",
            "FULFILLMENT_CREATED",
        ],
        "query": """
            subscription {
                event {
                    ... on OrderCreated {
                        order {
                            id
                        }
                    }
                    ... on OrderFullyPaid {
                        order {
                            id
                        }
                    }
                    ... on CustomerCreated {
                        user {
                            id
                        }
                    }
                    ... on FulfillmentCreated {
                        fulfillment {
                            id
                        }
                    }
                }
            }
        """,
        "targetUrl": "https://app.example/api/webhook",
    }


@pytest.fixture
def event_payload():
    """Return event payload."""
    return EventPayload.objects.create(payload='{"payload_key": "payload_value"}')


@pytest.fixture
def event_delivery(event_payload, webhook, app):
    """Return event delivery object"""
    return EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )


@pytest.fixture
def event_attempt(event_delivery):
    """Return event delivery attempt object"""
    return EventDeliveryAttempt.objects.create(
        delivery=event_delivery,
        task_id="example_task_id",
        duration=None,
        response="example_response",
        response_headers=None,
        request_headers=None,
    )


@pytest.fixture
def webhook_list_stored_payment_methods_response():
    return {
        "paymentMethods": [
            {
                "id": "method-1",
                "supportedPaymentFlows": ["INTERACTIVE"],
                "type": "Credit Card",
                "creditCardInfo": {
                    "brand": "visa",
                    "lastDigits": "1234",
                    "expMonth": 1,
                    "expYear": 2023,
                    "firstDigits": "123456",
                },
                "name": "***1234",
                "data": {"some": "data"},
            }
        ]
    }


@pytest.fixture
def webhook_response():
    return WebhookResponse(
        content="test_content",
        request_headers={"headers": "test_request"},
        response_headers={"headers": "test_response"},
        response_status_code=200,
        duration=2.0,
        status=EventDeliveryStatus.SUCCESS,
    )


@pytest.fixture
def webhook_response_failed():
    return WebhookResponse(
        content="example_content_response",
        request_headers={"headers": "test_request"},
        response_headers={"headers": "test_response"},
        response_status_code=500,
        duration=2.0,
        status=EventDeliveryStatus.FAILED,
    )


@pytest.fixture
def check_payment_balance_input():
    return {
        "gatewayId": "mirumee.payments.gateway",
        "channel": "channel_default",
        "method": "givex",
        "card": {
            "cvc": "9891",
            "code": "12345678910",
            "money": {"currency": "GBP", "amount": 100.0},
        },
    }


@pytest.fixture
def delivery_attempts(event_delivery):
    """Return consecutive deliveries attempts ids"""
    with freeze_time("2020-03-18 12:00:00"):
        attempt_1 = EventDeliveryAttempt.objects.create(
            delivery=event_delivery,
            task_id="example_task_id_1",
            duration=None,
            response="example_response",
            response_headers=None,
            request_headers=None,
        )

    with freeze_time("2020-03-18 13:00:00"):
        attempt_2 = EventDeliveryAttempt.objects.create(
            delivery=event_delivery,
            task_id="example_task_id_2",
            duration=None,
            response="example_response",
            response_headers=None,
            request_headers=None,
        )

    with freeze_time("2020-03-18 14:00:00"):
        attempt_3 = EventDeliveryAttempt.objects.create(
            delivery=event_delivery,
            task_id="example_task_id_3",
            duration=None,
            response="example_response",
            response_headers=None,
            request_headers=None,
        )

    attempt_1 = graphene.Node.to_global_id("EventDeliveryAttempt", attempt_1.pk)
    attempt_2 = graphene.Node.to_global_id("EventDeliveryAttempt", attempt_2.pk)
    attempt_3 = graphene.Node.to_global_id("EventDeliveryAttempt", attempt_3.pk)
    webhook_id = graphene.Node.to_global_id("Webhook", event_delivery.webhook.pk)

    return {
        "webhook_id": webhook_id,
        "attempt_1_id": attempt_1,
        "attempt_2_id": attempt_2,
        "attempt_3_id": attempt_3,
    }


@pytest.fixture
def event_deliveries(event_payload, webhook, app):
    """Return consecutive event deliveries ids"""
    delivery_1 = EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )
    delivery_2 = EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )
    delivery_3 = EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    delivery_1 = graphene.Node.to_global_id("EventDelivery", delivery_1.pk)
    delivery_2 = graphene.Node.to_global_id("EventDelivery", delivery_2.pk)
    delivery_3 = graphene.Node.to_global_id("EventDelivery", delivery_3.pk)

    return {
        "webhook_id": webhook_id,
        "delivery_1_id": delivery_1,
        "delivery_2_id": delivery_2,
        "delivery_3_id": delivery_3,
    }


@pytest.fixture
def action_required_gateway_response():
    return GatewayResponse(
        is_success=True,
        action_required=True,
        action_required_data={
            "paymentData": "test",
            "paymentMethodType": "scheme",
            "url": "https://test.adyen.com/hpp/3d/validate.shtml",
            "data": {
                "MD": "md-test-data",
                "PaReq": "PaReq-test-data",
                "TermUrl": "http://127.0.0.1:3000/",
            },
            "method": "POST",
            "type": "redirect",
        },
        kind=TransactionKind.CAPTURE,
        amount=Decimal(3.0),
        currency="usd",
        transaction_id="1234",
        error=None,
    )


@pytest.fixture
def product_media_image(product, image, media_root):
    return ProductMedia.objects.create(
        product=product,
        image=image,
        alt="image",
        type=ProductMediaTypes.IMAGE,
        oembed_data="{}",
    )


@pytest.fixture
def thumbnail_product_media(product_media_image, image_list, media_root):
    return Thumbnail.objects.create(
        product_media=product_media_image,
        size=128,
        image=image_list[1],
    )


@pytest.fixture
def thumbnail_category(category_with_image, image_list, media_root):
    return Thumbnail.objects.create(
        category=category_with_image,
        size=128,
        image=image_list[1],
    )


@pytest.fixture
def thumbnail_collection(collection_with_image, image_list, media_root):
    return Thumbnail.objects.create(
        collection=collection_with_image,
        size=128,
        image=image_list[1],
    )


@pytest.fixture
def thumbnail_user(customer_user, image_list, media_root):
    customer_user.avatar = image_list[0]
    return Thumbnail.objects.create(
        user=customer_user,
        size=128,
        image=image_list[1],
    )


@pytest.fixture
def transaction_session_response():
    return {
        "pspReference": "psp-123",
        "data": {"some-json": "data"},
        "result": "CHARGE_SUCCESS",
        "amount": "10.00",
        "time": "2022-11-18T13:25:58.169685+00:00",
        "externalUrl": "http://127.0.0.1:9090/external-reference",
        "message": "Message related to the payment",
    }


class Info:
    def __init__(self, request):
        self.context = request


@pytest.fixture
def dummy_info(request):
    return Info(request)


@pytest.fixture
def async_subscription_webhooks_with_root_objects(
    subscription_account_deleted_webhook,
    subscription_account_confirmed_webhook,
    subscription_account_email_changed_webhook,
    subscription_account_set_password_requested_webhook,
    subscription_account_confirmation_requested_webhook,
    subscription_account_delete_requested_webhook,
    subscription_account_change_email_requested_webhook,
    subscription_staff_set_password_requested_webhook,
    subscription_address_created_webhook,
    subscription_address_updated_webhook,
    subscription_address_deleted_webhook,
    subscription_app_installed_webhook,
    subscription_app_updated_webhook,
    subscription_app_deleted_webhook,
    subscription_app_status_changed_webhook,
    subscription_attribute_created_webhook,
    subscription_attribute_updated_webhook,
    subscription_attribute_deleted_webhook,
    subscription_attribute_value_created_webhook,
    subscription_attribute_value_updated_webhook,
    subscription_attribute_value_deleted_webhook,
    subscription_category_created_webhook,
    subscription_category_updated_webhook,
    subscription_category_deleted_webhook,
    subscription_channel_created_webhook,
    subscription_channel_updated_webhook,
    subscription_channel_deleted_webhook,
    subscription_channel_status_changed_webhook,
    subscription_gift_card_created_webhook,
    subscription_gift_card_updated_webhook,
    subscription_gift_card_deleted_webhook,
    subscription_gift_card_sent_webhook,
    subscription_gift_card_status_changed_webhook,
    subscription_gift_card_metadata_updated_webhook,
    subscription_gift_card_export_completed_webhook,
    subscription_menu_created_webhook,
    subscription_menu_updated_webhook,
    subscription_menu_deleted_webhook,
    subscription_menu_item_created_webhook,
    subscription_menu_item_updated_webhook,
    subscription_menu_item_deleted_webhook,
    subscription_shipping_price_created_webhook,
    subscription_shipping_price_updated_webhook,
    subscription_shipping_price_deleted_webhook,
    subscription_shipping_zone_created_webhook,
    subscription_shipping_zone_updated_webhook,
    subscription_shipping_zone_deleted_webhook,
    subscription_shipping_zone_metadata_updated_webhook,
    subscription_product_updated_webhook,
    subscription_product_created_webhook,
    subscription_product_deleted_webhook,
    subscription_product_export_completed_webhook,
    subscription_product_media_updated_webhook,
    subscription_product_media_created_webhook,
    subscription_product_media_deleted_webhook,
    subscription_product_metadata_updated_webhook,
    subscription_product_variant_created_webhook,
    subscription_product_variant_updated_webhook,
    subscription_product_variant_deleted_webhook,
    subscription_product_variant_metadata_updated_webhook,
    subscription_product_variant_out_of_stock_webhook,
    subscription_product_variant_back_in_stock_webhook,
    subscription_order_created_webhook,
    subscription_order_updated_webhook,
    subscription_order_confirmed_webhook,
    subscription_order_fully_paid_webhook,
    subscription_order_refunded_webhook,
    subscription_order_fully_refunded_webhook,
    subscription_order_paid_webhook,
    subscription_order_cancelled_webhook,
    subscription_order_expired_webhook,
    subscription_order_fulfilled_webhook,
    subscription_order_metadata_updated_webhook,
    subscription_order_bulk_created_webhook,
    subscription_draft_order_created_webhook,
    subscription_draft_order_updated_webhook,
    subscription_draft_order_deleted_webhook,
    subscription_sale_created_webhook,
    subscription_sale_updated_webhook,
    subscription_sale_deleted_webhook,
    subscription_sale_toggle_webhook,
    subscription_invoice_requested_webhook,
    subscription_invoice_deleted_webhook,
    subscription_invoice_sent_webhook,
    subscription_fulfillment_canceled_webhook,
    subscription_fulfillment_created_webhook,
    subscription_fulfillment_approved_webhook,
    subscription_fulfillment_metadata_updated_webhook,
    subscription_fulfillment_tracking_number_updated,
    subscription_customer_created_webhook,
    subscription_customer_updated_webhook,
    subscription_customer_deleted_webhook,
    subscription_customer_metadata_updated_webhook,
    subscription_collection_created_webhook,
    subscription_collection_updated_webhook,
    subscription_collection_deleted_webhook,
    subscription_collection_metadata_updated_webhook,
    subscription_checkout_created_webhook,
    subscription_checkout_updated_webhook,
    subscription_checkout_fully_paid_webhook,
    subscription_checkout_metadata_updated_webhook,
    subscription_page_created_webhook,
    subscription_page_updated_webhook,
    subscription_page_deleted_webhook,
    subscription_page_type_created_webhook,
    subscription_page_type_updated_webhook,
    subscription_page_type_deleted_webhook,
    subscription_permission_group_created_webhook,
    subscription_permission_group_updated_webhook,
    subscription_permission_group_deleted_webhook,
    subscription_product_created_multiple_events_webhook,
    subscription_staff_created_webhook,
    subscription_staff_updated_webhook,
    subscription_staff_deleted_webhook,
    subscription_transaction_item_metadata_updated_webhook,
    subscription_translation_created_webhook,
    subscription_translation_updated_webhook,
    subscription_warehouse_created_webhook,
    subscription_warehouse_updated_webhook,
    subscription_warehouse_deleted_webhook,
    subscription_warehouse_metadata_updated_webhook,
    subscription_voucher_created_webhook,
    subscription_voucher_updated_webhook,
    subscription_voucher_deleted_webhook,
    subscription_voucher_webhook_with_meta,
    subscription_voucher_metadata_updated_webhook,
    address,
    app,
    numeric_attribute,
    category,
    channel_PLN,
    gift_card,
    menu_item,
    shipping_method,
    product,
    fulfilled_order,
    sale,
    fulfillment,
    stock,
    customer_user,
    collection,
    checkout,
    page,
    permission_group_manage_users,
    shipping_zone,
    staff_user,
    voucher,
    warehouse,
    translated_attribute,
    transaction_item_created_by_app,
    product_media_image,
    user_export_file,
):
    events = WebhookEventAsyncType
    attr = numeric_attribute
    attr_value = attr.values.first()
    menu = menu_item.menu
    order = fulfilled_order
    invoice = order.invoices.first()
    page_type = page.page_type
    transaction_item_created_by_app.use_old_id = True
    transaction_item_created_by_app.save()

    return {
        events.ACCOUNT_DELETED: [
            subscription_account_deleted_webhook,
            customer_user,
        ],
        events.ACCOUNT_EMAIL_CHANGED: [
            subscription_account_email_changed_webhook,
            customer_user,
        ],
        events.ACCOUNT_CONFIRMED: [
            subscription_account_confirmed_webhook,
            customer_user,
        ],
        events.ACCOUNT_DELETE_REQUESTED: [
            subscription_account_delete_requested_webhook,
            customer_user,
        ],
        events.ACCOUNT_SET_PASSWORD_REQUESTED: [
            subscription_account_set_password_requested_webhook,
            customer_user,
        ],
        events.ACCOUNT_CHANGE_EMAIL_REQUESTED: [
            subscription_account_change_email_requested_webhook,
            customer_user,
        ],
        events.ACCOUNT_CONFIRMATION_REQUESTED: [
            subscription_account_confirmation_requested_webhook,
            customer_user,
        ],
        events.STAFF_SET_PASSWORD_REQUESTED: [
            subscription_staff_set_password_requested_webhook,
            staff_user,
        ],
        events.ADDRESS_UPDATED: [subscription_address_updated_webhook, address],
        events.ADDRESS_CREATED: [subscription_address_created_webhook, address],
        events.ADDRESS_DELETED: [subscription_address_deleted_webhook, address],
        events.APP_UPDATED: [subscription_app_updated_webhook, app],
        events.APP_DELETED: [subscription_app_deleted_webhook, app],
        events.APP_INSTALLED: [subscription_app_installed_webhook, app],
        events.APP_STATUS_CHANGED: [subscription_app_status_changed_webhook, app],
        events.ATTRIBUTE_CREATED: [subscription_attribute_created_webhook, attr],
        events.ATTRIBUTE_UPDATED: [subscription_attribute_updated_webhook, attr],
        events.ATTRIBUTE_DELETED: [subscription_attribute_deleted_webhook, attr],
        events.ATTRIBUTE_VALUE_UPDATED: [
            subscription_attribute_value_updated_webhook,
            attr_value,
        ],
        events.ATTRIBUTE_VALUE_CREATED: [
            subscription_attribute_value_created_webhook,
            attr_value,
        ],
        events.ATTRIBUTE_VALUE_DELETED: [
            subscription_attribute_value_deleted_webhook,
            attr_value,
        ],
        events.CATEGORY_CREATED: [subscription_category_created_webhook, category],
        events.CATEGORY_UPDATED: [subscription_category_updated_webhook, category],
        events.CATEGORY_DELETED: [subscription_category_deleted_webhook, category],
        events.CHANNEL_CREATED: [subscription_channel_created_webhook, channel_PLN],
        events.CHANNEL_UPDATED: [subscription_channel_updated_webhook, channel_PLN],
        events.CHANNEL_DELETED: [subscription_channel_deleted_webhook, channel_PLN],
        events.CHANNEL_STATUS_CHANGED: [
            subscription_channel_status_changed_webhook,
            channel_PLN,
        ],
        events.GIFT_CARD_CREATED: [subscription_gift_card_created_webhook, gift_card],
        events.GIFT_CARD_UPDATED: [subscription_gift_card_updated_webhook, gift_card],
        events.GIFT_CARD_DELETED: [subscription_gift_card_deleted_webhook, gift_card],
        events.GIFT_CARD_SENT: [subscription_gift_card_sent_webhook, gift_card],
        events.GIFT_CARD_STATUS_CHANGED: [
            subscription_gift_card_status_changed_webhook,
            gift_card,
        ],
        events.GIFT_CARD_METADATA_UPDATED: [
            subscription_gift_card_metadata_updated_webhook,
            gift_card,
        ],
        events.GIFT_CARD_EXPORT_COMPLETED: [
            subscription_gift_card_export_completed_webhook,
            user_export_file,
        ],
        events.MENU_CREATED: [subscription_menu_created_webhook, menu],
        events.MENU_UPDATED: [subscription_menu_updated_webhook, menu],
        events.MENU_DELETED: [subscription_menu_deleted_webhook, menu],
        events.MENU_ITEM_CREATED: [subscription_menu_item_created_webhook, menu_item],
        events.MENU_ITEM_UPDATED: [subscription_menu_item_updated_webhook, menu_item],
        events.MENU_ITEM_DELETED: [subscription_menu_item_deleted_webhook, menu_item],
        events.ORDER_CREATED: [subscription_order_created_webhook, order],
        events.ORDER_UPDATED: [subscription_order_updated_webhook, order],
        events.ORDER_CONFIRMED: [subscription_order_confirmed_webhook, order],
        events.ORDER_FULLY_PAID: [subscription_order_fully_paid_webhook, order],
        events.ORDER_PAID: [subscription_order_paid_webhook, order],
        events.ORDER_REFUNDED: [subscription_order_refunded_webhook, order],
        events.ORDER_FULLY_REFUNDED: [subscription_order_fully_refunded_webhook, order],
        events.ORDER_FULFILLED: [subscription_order_fulfilled_webhook, order],
        events.ORDER_CANCELLED: [subscription_order_cancelled_webhook, order],
        events.ORDER_EXPIRED: [subscription_order_expired_webhook, order],
        events.ORDER_METADATA_UPDATED: [
            subscription_order_metadata_updated_webhook,
            order,
        ],
        events.ORDER_BULK_CREATED: [subscription_order_bulk_created_webhook, order],
        events.DRAFT_ORDER_CREATED: [subscription_draft_order_created_webhook, order],
        events.DRAFT_ORDER_UPDATED: [subscription_draft_order_updated_webhook, order],
        events.DRAFT_ORDER_DELETED: [subscription_draft_order_deleted_webhook, order],
        events.PRODUCT_CREATED: [subscription_product_created_webhook, product],
        events.PRODUCT_UPDATED: [subscription_product_updated_webhook, product],
        events.PRODUCT_DELETED: [subscription_product_deleted_webhook, product],
        events.PRODUCT_EXPORT_COMPLETED: [
            subscription_product_export_completed_webhook,
            user_export_file,
        ],
        events.PRODUCT_MEDIA_CREATED: [
            subscription_product_media_created_webhook,
            product_media_image,
        ],
        events.PRODUCT_MEDIA_UPDATED: [
            subscription_product_media_updated_webhook,
            product_media_image,
        ],
        events.PRODUCT_MEDIA_DELETED: [
            subscription_product_media_deleted_webhook,
            product_media_image,
        ],
        events.PRODUCT_METADATA_UPDATED: [
            subscription_product_metadata_updated_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_CREATED: [
            subscription_product_variant_created_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_UPDATED: [
            subscription_product_variant_updated_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_OUT_OF_STOCK: [
            subscription_product_variant_out_of_stock_webhook,
            stock,
        ],
        events.PRODUCT_VARIANT_BACK_IN_STOCK: [
            subscription_product_variant_back_in_stock_webhook,
            stock,
        ],
        events.PRODUCT_VARIANT_DELETED: [
            subscription_product_variant_deleted_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_METADATA_UPDATED: [
            subscription_product_variant_metadata_updated_webhook,
            product,
        ],
        events.SALE_CREATED: [subscription_sale_created_webhook, sale],
        events.SALE_UPDATED: [subscription_sale_updated_webhook, sale],
        events.SALE_DELETED: [subscription_sale_deleted_webhook, sale],
        events.SALE_TOGGLE: [subscription_sale_toggle_webhook, sale],
        events.INVOICE_REQUESTED: [subscription_invoice_requested_webhook, invoice],
        events.INVOICE_DELETED: [subscription_invoice_deleted_webhook, invoice],
        events.INVOICE_SENT: [subscription_invoice_sent_webhook, invoice],
        events.FULFILLMENT_CANCELED: [
            subscription_fulfillment_canceled_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_CREATED: [
            subscription_fulfillment_created_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_APPROVED: [
            subscription_fulfillment_approved_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_METADATA_UPDATED: [
            subscription_fulfillment_metadata_updated_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_TRACKING_NUMBER_UPDATED: [
            subscription_fulfillment_tracking_number_updated,
            fulfillment,
        ],
        events.CUSTOMER_CREATED: [subscription_customer_created_webhook, customer_user],
        events.CUSTOMER_UPDATED: [subscription_customer_updated_webhook, customer_user],
        events.CUSTOMER_METADATA_UPDATED: [
            subscription_customer_metadata_updated_webhook,
            customer_user,
        ],
        events.COLLECTION_CREATED: [
            subscription_collection_created_webhook,
            collection,
        ],
        events.COLLECTION_UPDATED: [
            subscription_collection_updated_webhook,
            collection,
        ],
        events.COLLECTION_DELETED: [
            subscription_collection_deleted_webhook,
            collection,
        ],
        events.COLLECTION_METADATA_UPDATED: [
            subscription_collection_metadata_updated_webhook,
            collection,
        ],
        events.CHECKOUT_CREATED: [subscription_checkout_created_webhook, checkout],
        events.CHECKOUT_UPDATED: [subscription_checkout_updated_webhook, checkout],
        events.CHECKOUT_FULLY_PAID: [
            subscription_checkout_fully_paid_webhook,
            checkout,
        ],
        events.CHECKOUT_METADATA_UPDATED: [
            subscription_checkout_metadata_updated_webhook,
            checkout,
        ],
        events.PAGE_CREATED: [subscription_page_created_webhook, page],
        events.PAGE_UPDATED: [subscription_page_updated_webhook, page],
        events.PAGE_DELETED: [subscription_page_deleted_webhook, page],
        events.PAGE_TYPE_CREATED: [subscription_page_type_created_webhook, page_type],
        events.PAGE_TYPE_UPDATED: [subscription_page_type_updated_webhook, page_type],
        events.PAGE_TYPE_DELETED: [subscription_page_type_deleted_webhook, page_type],
        events.PERMISSION_GROUP_CREATED: [
            subscription_permission_group_created_webhook,
            permission_group_manage_users,
        ],
        events.PERMISSION_GROUP_UPDATED: [
            subscription_permission_group_updated_webhook,
            permission_group_manage_users,
        ],
        events.PERMISSION_GROUP_DELETED: [
            subscription_permission_group_deleted_webhook,
            permission_group_manage_users,
        ],
        events.SHIPPING_PRICE_CREATED: [
            subscription_shipping_price_created_webhook,
            shipping_method,
        ],
        events.SHIPPING_PRICE_UPDATED: [
            subscription_shipping_price_updated_webhook,
            shipping_method,
        ],
        events.SHIPPING_PRICE_DELETED: [
            subscription_shipping_price_deleted_webhook,
            shipping_method,
        ],
        events.SHIPPING_ZONE_CREATED: [
            subscription_shipping_zone_created_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_UPDATED: [
            subscription_shipping_zone_updated_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_DELETED: [
            subscription_shipping_zone_deleted_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_METADATA_UPDATED: [
            subscription_shipping_zone_metadata_updated_webhook,
            shipping_zone,
        ],
        events.STAFF_CREATED: [subscription_staff_created_webhook, staff_user],
        events.STAFF_UPDATED: [subscription_staff_updated_webhook, staff_user],
        events.STAFF_DELETED: [subscription_staff_deleted_webhook, staff_user],
        events.TRANSACTION_ITEM_METADATA_UPDATED: [
            subscription_transaction_item_metadata_updated_webhook,
            transaction_item_created_by_app,
        ],
        events.TRANSLATION_CREATED: [
            subscription_translation_created_webhook,
            translated_attribute,
        ],
        events.TRANSLATION_UPDATED: [
            subscription_translation_updated_webhook,
            translated_attribute,
        ],
        events.VOUCHER_CREATED: [subscription_voucher_created_webhook, voucher],
        events.VOUCHER_UPDATED: [subscription_voucher_updated_webhook, voucher],
        events.VOUCHER_DELETED: [subscription_voucher_deleted_webhook, voucher],
        events.VOUCHER_METADATA_UPDATED: [
            subscription_voucher_metadata_updated_webhook,
            voucher,
        ],
        events.WAREHOUSE_CREATED: [subscription_warehouse_created_webhook, warehouse],
        events.WAREHOUSE_UPDATED: [subscription_warehouse_updated_webhook, warehouse],
        events.WAREHOUSE_DELETED: [subscription_warehouse_deleted_webhook, warehouse],
        events.WAREHOUSE_METADATA_UPDATED: [
            subscription_warehouse_metadata_updated_webhook,
            warehouse,
        ],
    }
