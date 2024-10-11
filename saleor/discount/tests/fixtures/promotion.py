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
def catalogue_promotion(channel_USD, product, collection):
    promotion = Promotion.objects.create(
        name="Promotion",
        type=PromotionType.CATALOGUE,
        description=dummy_editorjs("Test description."),
        end_date=timezone.now() + datetime.timedelta(days=30),
    )
    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Percentage promotion rule",
                promotion=promotion,
                description=dummy_editorjs(
                    "Test description for percentage promotion rule."
                ),
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("10"),
            ),
            PromotionRule(
                name="Fixed promotion rule",
                promotion=promotion,
                description=dummy_editorjs(
                    "Test description for fixes promotion rule."
                ),
                catalogue_predicate={
                    "collectionPredicate": {
                        "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("5"),
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(channel_USD)
    fetch_variants_for_promotion_rules(promotion.rules.all())
    return promotion


@pytest.fixture
def catalogue_promotion_without_rules(db):
    promotion = Promotion.objects.create(
        name="Promotion",
        description=dummy_editorjs("Test description."),
        end_date=timezone.now() + datetime.timedelta(days=30),
        type=PromotionType.CATALOGUE,
    )
    return promotion


@pytest.fixture
def order_promotion_without_rules(db):
    promotion = Promotion.objects.create(
        name="Promotion",
        description=dummy_editorjs("Test description."),
        end_date=timezone.now() + datetime.timedelta(days=30),
        type=PromotionType.ORDER,
    )
    return promotion


@pytest.fixture
def catalogue_promotion_with_single_rule(catalogue_predicate, channel_USD):
    promotion = Promotion.objects.create(
        name="Promotion with single rule", type=PromotionType.CATALOGUE
    )
    rule = PromotionRule.objects.create(
        name="Sale rule",
        promotion=promotion,
        catalogue_predicate=catalogue_predicate,
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
    )
    rule.channels.add(channel_USD)
    return promotion


@pytest.fixture
def order_promotion_with_rule(channel_USD):
    promotion = Promotion.objects.create(
        name="Promotion with order rule", type=PromotionType.ORDER
    )
    rule = PromotionRule.objects.create(
        name="Promotion rule",
        promotion=promotion,
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(channel_USD)
    return promotion


@pytest.fixture
def promotion_list(channel_USD, product, collection):
    collection.products.add(product)
    promotions = Promotion.objects.bulk_create(
        [
            Promotion(
                name="Promotion 1",
                type=PromotionType.CATALOGUE,
                description=dummy_editorjs("Promotion 1 description."),
                start_date=timezone.now() + datetime.timedelta(days=1),
                end_date=timezone.now() + datetime.timedelta(days=10),
            ),
            Promotion(
                name="Promotion 2",
                type=PromotionType.CATALOGUE,
                description=dummy_editorjs("Promotion 2 description."),
                start_date=timezone.now() + datetime.timedelta(days=5),
                end_date=timezone.now() + datetime.timedelta(days=20),
            ),
            Promotion(
                name="Promotion 3",
                type=PromotionType.CATALOGUE,
                description=dummy_editorjs("TePromotion 3 description."),
                start_date=timezone.now() + datetime.timedelta(days=15),
                end_date=timezone.now() + datetime.timedelta(days=30),
            ),
        ]
    )
    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Promotion 1 percentage rule",
                promotion=promotions[0],
                description=dummy_editorjs(
                    "Test description for promotion 1 percentage rule."
                ),
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("10"),
            ),
            PromotionRule(
                name="Promotion 1 fixed rule",
                promotion=promotions[0],
                description=dummy_editorjs(
                    "Test description for promotion 1 fixed rule."
                ),
                catalogue_predicate={
                    "collectionPredicate": {
                        "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("5"),
            ),
            PromotionRule(
                name="Promotion 2 percentage rule",
                promotion=promotions[1],
                description=dummy_editorjs(
                    "Test description for promotion 2 percentage rule."
                ),
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("10"),
            ),
            PromotionRule(
                name="Promotion 3 fixed rule",
                promotion=promotions[2],
                description=dummy_editorjs(
                    "Test description for promotion 3 fixed rule."
                ),
                catalogue_predicate={
                    "collectionPredicate": {
                        "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("5"),
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(channel_USD)
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    return promotions


@pytest.fixture
def promotion_converted_from_sale(catalogue_predicate, channel_USD):
    promotion = Promotion.objects.create(name="Sale", type=PromotionType.CATALOGUE)
    promotion.assign_old_sale_id()

    rule = PromotionRule.objects.create(
        name="Sale rule",
        promotion=promotion,
        catalogue_predicate=catalogue_predicate,
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
        old_channel_listing_id=PromotionRule.get_old_channel_listing_ids(1)[0][0],
    )
    rule.channels.add(channel_USD)
    fetch_variants_for_promotion_rules(promotion.rules.all())
    return promotion


@pytest.fixture
def promotion_converted_from_sale_with_many_channels(
    promotion_converted_from_sale, catalogue_predicate, channel_PLN
):
    promotion = promotion_converted_from_sale
    rule = PromotionRule.objects.create(
        name="Sale rule 2",
        promotion=promotion,
        catalogue_predicate=catalogue_predicate,
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
        old_channel_listing_id=PromotionRule.get_old_channel_listing_ids(1)[0][0],
    )
    rule.channels.add(channel_PLN)
    fetch_variants_for_promotion_rules(promotion.rules.all())
    return promotion


@pytest.fixture
def promotion_converted_from_sale_with_empty_predicate(channel_USD):
    promotion = Promotion.objects.create(
        name="Sale with empty predicate", type=PromotionType.CATALOGUE
    )
    promotion.assign_old_sale_id()
    rule = PromotionRule.objects.create(
        name="Sale with empty predicate rule",
        promotion=promotion,
        catalogue_predicate={},
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
        old_channel_listing_id=PromotionRule.get_old_channel_listing_ids(1)[0][0],
    )
    rule.channels.add(channel_USD)
    return promotion
