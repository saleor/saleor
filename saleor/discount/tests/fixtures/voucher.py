import datetime
import uuid
from contextlib import contextmanager
from decimal import Decimal
from functools import partial
from io import BytesIO
from typing import Callable, Optional
from unittest.mock import MagicMock

import graphene
import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.template.defaultfilters import truncatechars
from django.test.utils import CaptureQueriesContext as BaseCaptureQueriesContext
from django.utils import timezone
from django_countries import countries
from freezegun import freeze_time
from PIL import Image
from prices import Money

from saleor.account.models import Address, Group, StaffNotificationRecipient, User
from saleor.attribute import AttributeEntityType, AttributeInputType, AttributeType
from saleor.attribute.models import (
    Attribute,
    AttributeTranslation,
    AttributeValue,
    AttributeValueTranslation,
)
from saleor.attribute.utils import associate_attribute_values_to_instance
from saleor.checkout import base_calculations
from saleor.checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from saleor.checkout.models import Checkout, CheckoutLine, CheckoutMetadata
from saleor.checkout.utils import (
    add_variant_to_checkout,
    add_voucher_to_checkout,
)
from saleor.core import JobStatus
from saleor.core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from saleor.core.payments import PaymentInterface
from saleor.core.units import MeasurementUnits
from saleor.core.utils.editorjs import clean_editor_js
from saleor.csv.events import ExportEvents
from saleor.csv.models import ExportEvent, ExportFile
from saleor.discount import (
    DiscountType,
    DiscountValueType,
    PromotionEvents,
    PromotionType,
    RewardType,
    RewardValueType,
    VoucherType,
)
from saleor.discount.interface import VariantPromotionRuleInfo
from saleor.discount.models import (
    CheckoutDiscount,
    CheckoutLineDiscount,
    Promotion,
    PromotionEvent,
    PromotionRule,
    PromotionRuleTranslation,
    PromotionTranslation,
    Voucher,
    VoucherChannelListing,
    VoucherCode,
    VoucherCustomer,
    VoucherTranslation,
)
from saleor.giftcard import GiftCardEvents
from saleor.giftcard.models import GiftCard, GiftCardEvent, GiftCardTag
from saleor.menu.models import Menu
from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.interface import (
    AddressData,
    GatewayConfig,
    GatewayResponse,
    PaymentData,
)
from saleor.payment.models import Payment, TransactionEvent, TransactionItem
from saleor.payment.transaction_item_calculations import recalculate_transaction_amounts
from saleor.payment.utils import create_manual_adjustment_events
from saleor.permission.enums import get_permissions
from saleor.permission.models import Permission
from saleor.plugins.manager import get_plugins_manager
from saleor.product.models import (
    CategoryTranslation,
    CollectionTranslation,
    ProductTranslation,
    ProductVariantChannelListing,
    ProductVariantTranslation,
)
from saleor.product.utils.variants import fetch_variants_for_promotion_rules
from saleor.shipping.models import (
    ShippingMethod,
    ShippingMethodChannelListing,
    ShippingMethodTranslation,
    ShippingMethodType,
    ShippingZone,
)
from saleor.shipping.utils import convert_to_shipping_method_data
from saleor.site.models import SiteSettings
from saleor.tax import TaxCalculationStrategy
from saleor.warehouse.models import (
    PreorderReservation,
    Reservation,
    Warehouse,
)
from saleor.webhook.event_types import WebhookEventAsyncType
from saleor.webhook.transport.utils import to_payment_app_id
from saleor.tests.utils import dummy_editorjs


@pytest.fixture
def voucher_without_channel(db):
    voucher = Voucher.objects.create()
    VoucherCode.objects.create(code="mirumee", voucher=voucher)
    return voucher


@pytest.fixture
def voucher(voucher_without_channel, channel_USD):
    VoucherChannelListing.objects.create(
        voucher=voucher_without_channel,
        channel=channel_USD,
        discount=Money(20, channel_USD.currency_code),
    )
    return voucher_without_channel


@pytest.fixture
def voucher_with_many_codes(voucher):
    VoucherCode.objects.bulk_create(
        [
            VoucherCode(code="Multi1", voucher=voucher),
            VoucherCode(code="Multi2", voucher=voucher),
            VoucherCode(code="Multi3", voucher=voucher),
            VoucherCode(code="Multi4", voucher=voucher),
        ]
    )
    return voucher


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
        discount_value_type=DiscountValueType.PERCENTAGE,
    )
    VoucherCode.objects.create(code="saleor", voucher=voucher)
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
    voucher = Voucher.objects.create()
    VoucherCode.objects.create(code="mirumee", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
        min_spent_amount=1_000_000,
    )
    return voucher


@pytest.fixture
def voucher_shipping_type(channel_USD):
    voucher = Voucher.objects.create(type=VoucherType.SHIPPING, countries="IS")
    VoucherCode.objects.create(code="mirumee", voucher=voucher)
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
    code = voucher.codes.first()
    return VoucherCustomer.objects.create(voucher_code=code, customer_email=email)


@pytest.fixture
def voucher_multiple_use(voucher_with_many_codes):
    voucher = voucher_with_many_codes
    voucher.usage_limit = 3
    voucher.save(update_fields=["usage_limit"])
    codes = voucher.codes.all()
    for code in codes:
        code.used = 1
    VoucherCode.objects.bulk_update(codes, ["used"])
    voucher.refresh_from_db()
    return voucher


@pytest.fixture
def voucher_single_use(voucher_with_many_codes):
    voucher = voucher_with_many_codes
    voucher.single_use = True
    voucher.save(update_fields=["single_use"])
    return voucher
