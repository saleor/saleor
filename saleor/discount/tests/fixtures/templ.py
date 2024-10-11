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
