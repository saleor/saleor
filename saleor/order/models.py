from decimal import ROUND_HALF_UP, Decimal
from operator import attrgetter
from re import match
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.indexes import BTreeIndex, GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MinValueValidator
from django.db import connection, models
from django.db.models import F, JSONField, Max
from django.db.models.expressions import Exists, OuterRef
from django.utils.timezone import now
from django_measurement.models import MeasurementField
from measurement.measures import Weight

from ..app.models import App
from ..channel.models import Channel
from ..core.db.fields import MoneyField, TaxedMoneyField
from ..core.models import ModelWithExternalReference, ModelWithMetadata
from ..core.taxes import TAX_ERROR_FIELD_LENGTH
from ..core.units import WeightUnits
from ..core.utils.json_serializer import CustomJsonEncoder
from ..core.weight import zero_weight
from ..discount import DiscountValueType
from ..discount.models import Voucher
from ..giftcard.models import GiftCard
from ..payment import ChargeStatus, TransactionKind
from ..payment.model_helpers import get_subtotal
from ..payment.models import Payment
from ..permission.enums import OrderPermissions
from ..shipping import IncoTerm
from ..shipping.models import ShippingMethod
from . import (
    FulfillmentStatus,
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderGrantedRefundStatus,
    OrderOrigin,
    OrderStatus,
    PickStatus,
)

if TYPE_CHECKING:
    from ..account.models import User


class OrderQueryset(models.QuerySet["Order"]):
    def get_by_checkout_token(self, token):
        """Return non-draft order with matched checkout token."""
        return self.non_draft().filter(checkout_token=token).first()

    def confirmed(self):
        """Return orders that aren't draft or unconfirmed."""
        return self.exclude(status__in=[OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])

    def non_draft(self):
        """Return orders that aren't draft."""
        return self.exclude(status=OrderStatus.DRAFT)

    def drafts(self):
        """Return draft orders."""
        return self.filter(status=OrderStatus.DRAFT)

    def ready_to_fulfill(self):
        """Return orders that can be fulfilled.

        Orders ready to fulfill are fully paid but unfulfilled (or partially
        fulfilled).
        """
        statuses = {OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED}
        payments = Payment.objects.filter(is_active=True).values("id")
        return self.filter(
            Exists(payments.filter(order_id=OuterRef("id"))),
            status__in=statuses,
            total_gross_amount__lte=F("total_charged_amount"),
        )

    def ready_to_capture(self):
        """Return orders with payments to capture.

        Orders ready to capture are those which are not draft or canceled and
        have a preauthorized payment. The preauthorized payment can not
        already be partially or fully captured.
        """
        payments = Payment.objects.filter(
            is_active=True, charge_status=ChargeStatus.NOT_CHARGED
        ).values("id")
        qs = self.filter(Exists(payments.filter(order_id=OuterRef("id"))))
        return qs.exclude(
            status={OrderStatus.DRAFT, OrderStatus.CANCELED, OrderStatus.EXPIRED}
        )

    def ready_to_confirm(self):
        """Return unconfirmed orders."""
        return self.filter(status=OrderStatus.UNCONFIRMED)

    def ready_to_fulfill_with_inventory(self):
        """Return UNCONFIRMED orders where all inventory has arrived in owned warehouses.

        These orders meet the criteria:
        1. Status is UNCONFIRMED
        2. All allocations are in owned warehouses
        3. All allocations have AllocationSources (inventory received from POs)
        4. AllocationSources quantities match allocation quantities

        Use this to find orders that are waiting for confirmation but have
        inventory ready to ship.
        """
        from django.db.models import OuterRef, Q, Subquery, Sum

        from ..warehouse.models import Allocation

        return self.filter(
            status=OrderStatus.UNCONFIRMED,
            # Has at least one allocation
            id__in=Subquery(
                Allocation.objects.filter(
                    order_line__order__status=OrderStatus.UNCONFIRMED
                )
                .values("order_line__order_id")
                .distinct()
            ),
        ).exclude(
            # Exclude orders with allocation violations
            id__in=Subquery(
                Allocation.objects.filter(order_line__order_id=OuterRef("id"))
                .annotate(total_sourced=Sum("allocation_sources__quantity"))
                .filter(
                    Q(stock__warehouse__is_owned=False)
                    | Q(total_sourced__isnull=True)
                    | ~Q(total_sourced=F("quantity_allocated"))
                )
                .values("order_line__order_id")
                .distinct()
            )
        )


OrderManager = models.Manager.from_queryset(OrderQueryset)


def get_order_number():
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('order_order_number_seq')")
        result = cursor.fetchone()
        return result[0]


class Order(ModelWithMetadata, ModelWithExternalReference):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    number = models.IntegerField(unique=True, default=get_order_number, editable=False)
    use_old_id = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False, db_index=True)
    expired_at = models.DateTimeField(blank=True, null=True)

    status = models.CharField(
        max_length=32, default=OrderStatus.UNFULFILLED, choices=OrderStatus.CHOICES
    )
    authorize_status = models.CharField(
        max_length=32,
        default=OrderAuthorizeStatus.NONE,
        choices=OrderAuthorizeStatus.CHOICES,
        db_index=True,
    )
    charge_status = models.CharField(
        max_length=32,
        default=OrderChargeStatus.NONE,
        choices=OrderChargeStatus.CHOICES,
        db_index=True,
    )
    user = models.ForeignKey(
        "account.User",
        blank=True,
        null=True,
        related_name="orders",
        on_delete=models.SET_NULL,
    )
    language_code = models.CharField(
        max_length=35, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )
    tracking_client_id = models.CharField(max_length=36, blank=True, editable=False)
    billing_address = models.ForeignKey(
        "account.Address",
        related_name="+",
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
    )
    shipping_address = models.ForeignKey(
        "account.Address",
        related_name="+",
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
    )
    # The flag is only applicable to draft orders and should be null for orders
    # with a status other than `DRAFT`.
    draft_save_billing_address = models.BooleanField(null=True, blank=True)
    draft_save_shipping_address = models.BooleanField(null=True, blank=True)
    user_email = models.EmailField(blank=True, default="")
    original = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    origin = models.CharField(max_length=32, choices=OrderOrigin.CHOICES)

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )

    shipping_method = models.ForeignKey(
        ShippingMethod,
        blank=True,
        null=True,
        related_name="orders",
        on_delete=models.SET_NULL,
    )
    collection_point = models.ForeignKey(
        "warehouse.Warehouse",
        blank=True,
        null=True,
        related_name="orders",
        on_delete=models.SET_NULL,
    )
    shipping_method_name = models.CharField(
        max_length=255, null=True, default=None, blank=True, editable=False
    )
    collection_point_name = models.CharField(
        max_length=255, null=True, default=None, blank=True, editable=False
    )

    channel = models.ForeignKey(
        Channel,
        related_name="orders",
        on_delete=models.PROTECT,
    )
    shipping_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
        editable=False,
    )
    shipping_price_net = MoneyField(
        amount_field="shipping_price_net_amount", currency_field="currency"
    )

    shipping_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
        editable=False,
    )
    shipping_price_gross = MoneyField(
        amount_field="shipping_price_gross_amount", currency_field="currency"
    )

    # Price with applied shipping voucher discount
    shipping_price = TaxedMoneyField(
        net_amount_field="shipping_price_net_amount",
        gross_amount_field="shipping_price_gross_amount",
        currency_field="currency",
    )
    base_shipping_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    # Shipping price with applied shipping voucher discount, without tax
    base_shipping_price = MoneyField(
        amount_field="base_shipping_price_amount", currency_field="currency"
    )
    undiscounted_base_shipping_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    # Shipping price before applying any discounts
    undiscounted_base_shipping_price = MoneyField(
        amount_field="undiscounted_base_shipping_price_amount",
        currency_field="currency",
    )
    shipping_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4, blank=True, null=True
    )
    shipping_tax_class = models.ForeignKey(
        "tax.TaxClass",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    shipping_tax_class_name = models.CharField(max_length=255, blank=True, null=True)
    shipping_tax_class_private_metadata = JSONField(
        blank=True, db_default={}, default=dict, encoder=CustomJsonEncoder
    )
    shipping_tax_class_metadata = JSONField(
        blank=True, db_default={}, default=dict, encoder=CustomJsonEncoder
    )
    shipping_xero_tax_code = models.CharField(max_length=50, blank=True, null=True)
    shipping_method_private_metadata = JSONField(
        blank=True, null=True, default=dict, encoder=CustomJsonEncoder
    )
    shipping_method_metadata = JSONField(
        blank=True, null=True, default=dict, encoder=CustomJsonEncoder
    )

    inco_term = models.CharField(
        max_length=3,
        null=True,
        blank=True,
        default=None,
        choices=IncoTerm.CHOICES,
    )

    # Token of a checkout instance that this order was created from
    checkout_token = models.CharField(max_length=36, blank=True)

    lines_count = models.PositiveIntegerField()

    total_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    undiscounted_total_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )

    total_net = MoneyField(amount_field="total_net_amount", currency_field="currency")
    undiscounted_total_net = MoneyField(
        amount_field="undiscounted_total_net_amount", currency_field="currency"
    )

    total_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    undiscounted_total_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )

    total_gross = MoneyField(
        amount_field="total_gross_amount", currency_field="currency"
    )
    undiscounted_total_gross = MoneyField(
        amount_field="undiscounted_total_gross_amount", currency_field="currency"
    )

    total = TaxedMoneyField(
        net_amount_field="total_net_amount",
        gross_amount_field="total_gross_amount",
        currency_field="currency",
    )
    undiscounted_total = TaxedMoneyField(
        net_amount_field="undiscounted_total_net_amount",
        gross_amount_field="undiscounted_total_gross_amount",
        currency_field="currency",
    )

    total_charged_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    total_authorized_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    total_authorized = MoneyField(
        amount_field="total_authorized_amount", currency_field="currency"
    )
    total_charged = MoneyField(
        amount_field="total_charged_amount", currency_field="currency"
    )
    subtotal_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    subtotal_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    subtotal = TaxedMoneyField(
        net_amount_field="subtotal_net_amount",
        gross_amount_field="subtotal_gross_amount",
    )

    voucher = models.ForeignKey(
        Voucher, blank=True, null=True, related_name="+", on_delete=models.SET_NULL
    )

    voucher_code = models.CharField(
        max_length=255, null=True, blank=True, db_index=False
    )
    gift_cards = models.ManyToManyField(GiftCard, blank=True, related_name="orders")
    allowed_warehouses = models.ManyToManyField(
        "warehouse.Warehouse",
        blank=True,
        related_name="orders_with_restricted_warehouses",
    )
    display_gross_prices = models.BooleanField(default=True)
    customer_note = models.TextField(blank=True, default="")
    weight = MeasurementField(
        measurement=Weight,
        unit_choices=WeightUnits.CHOICES,
        default=zero_weight,
    )
    redirect_url = models.URLField(blank=True, null=True)
    search_document = models.TextField(blank=True, default="")
    search_vector = SearchVectorField(blank=True, null=True)
    # this field is used only for draft/unconfirmed orders
    should_refresh_prices = models.BooleanField(default=True)
    tax_exemption = models.BooleanField(default=False)
    tax_error = models.CharField(
        max_length=TAX_ERROR_FIELD_LENGTH, null=True, blank=True
    )

    deposit_required = models.BooleanField(default=False)
    deposit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    deposit_paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Timestamp when the deposit threshold was met by cumulative Xero payments."
        ),
    )
    deposit_threshold_met_override = models.BooleanField(default=False)
    allow_variant_reallocation = models.BooleanField(default=True)
    xero_deposit_prepayment_id = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        help_text="Xero prepayment UUID for the deposit on this order.",
    )
    xero_bank_account_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Xero bank account code used for deposit prepayments on this order.",
    )
    xero_bank_account_sort_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Bank sort code for the Xero bank account used for deposit prepayments.",
    )
    xero_bank_account_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Bank account number for the Xero bank account used for deposit prepayments.",
    )

    objects = OrderManager()

    class Meta:
        ordering = ("-number",)
        permissions = (
            (OrderPermissions.MANAGE_ORDERS.codename, "Manage orders."),
            (OrderPermissions.MANAGE_ORDERS_IMPORT.codename, "Manage orders import."),
        )
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            GinIndex(
                name="order_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["search_document"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="order_tsearch",
                fields=["search_vector"],
            ),
            GinIndex(
                name="order_email_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["user_email"],
                opclasses=["gin_trgm_ops"],
            ),
            models.Index(fields=["created_at"], name="idx_order_created_at"),
            GinIndex(fields=["voucher_code"], name="order_voucher_code_idx"),
            GinIndex(
                fields=["user_email", "user_id"],
                name="order_user_email_user_id_idx",
            ),
            BTreeIndex(fields=["checkout_token"], name="checkout_token_btree_idx"),
            BTreeIndex(fields=["lines_count"], name="lines_count_idx"),
            BTreeIndex(
                fields=["total_gross_amount"],
                name="order_totalgrossamount_idx",
            ),
            BTreeIndex(
                fields=["total_net_amount"],
                name="order_totalnetamount_idx",
            ),
            BTreeIndex(fields=["status"], name="order_status_idx"),
        ]

    def is_fully_paid(self):
        return self.total_charged >= self.total.gross

    def is_partly_paid(self):
        return self.total_charged_amount > 0

    @property
    def total_deposit_paid(self):
        from django.db.models import Sum

        from ..payment import CustomPaymentChoices

        result = self.payments.filter(
            gateway=CustomPaymentChoices.XERO,
            is_active=True,
        ).aggregate(total=Sum("captured_amount"))
        return result["total"] or Decimal(0)

    @property
    def deposit_threshold_met(self):
        if not self.deposit_required:
            return True
        if not self.deposit_percentage:
            return False
        if self.deposit_threshold_met_override:
            return True
        required = (
            self.total_gross_amount * (self.deposit_percentage / Decimal(100))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return self.total_deposit_paid >= required

    def get_remaining_deposit(self):
        from decimal import Decimal

        total_paid = self.total_deposit_paid
        if not total_paid:
            return Decimal(0)
        total_allocated = sum(
            f.deposit_allocated_amount or Decimal(0) for f in self.fulfillments.all()
        )
        return total_paid - total_allocated

    def get_customer_email(self):
        if self.user_email:
            return self.user_email
        if self.user_id:
            return cast("User", self.user).email
        return None

    def __repr__(self):
        return f"<Order #{self.id!r}>"

    def __str__(self):
        return f"#{self.id}"

    def get_last_payment(self) -> Payment | None:
        # Skipping a partial payment is a temporary workaround for storing a basic data
        # about partial payment from Adyen plugin. This is something that will removed
        # in 3.1 by introducing a partial payments feature.
        payments: list[Payment] = [
            payment for payment in self.payments.all() if not payment.partial
        ]
        return max(payments, default=None, key=attrgetter("pk"))

    def is_pre_authorized(self):
        return (
            self.payments.filter(
                is_active=True,
                transactions__kind=TransactionKind.AUTH,
                transactions__action_required=False,
            )
            .filter(transactions__is_success=True)
            .exists()
        )

    def is_captured(self):
        return (
            self.payments.filter(
                is_active=True,
                transactions__kind=TransactionKind.CAPTURE,
                transactions__action_required=False,
            )
            .filter(transactions__is_success=True)
            .exists()
        )

    def get_subtotal(self):
        return get_subtotal(self.lines.all(), self.currency)

    def is_shipping_required(
        self, database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME
    ):
        return any(
            line.is_shipping_required
            for line in self.lines.using(database_connection_name).all()
        )

    def get_total_quantity(self):
        return sum([line.quantity for line in self.lines.all()])

    def is_draft(self):
        return self.status == OrderStatus.DRAFT

    def is_unconfirmed(self):
        return self.status == OrderStatus.UNCONFIRMED

    def is_expired(self):
        return self.status == OrderStatus.EXPIRED

    def is_open(self):
        statuses = {OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED}
        return self.status in statuses

    def can_cancel(self):
        statuses_allowed_to_cancel = [
            FulfillmentStatus.CANCELED,
            FulfillmentStatus.REFUNDED,
            FulfillmentStatus.REPLACED,
            FulfillmentStatus.REFUNDED_AND_RETURNED,
            FulfillmentStatus.RETURNED,
        ]
        return (
            not self.fulfillments.exclude(
                status__in=statuses_allowed_to_cancel
            ).exists()
        ) and self.status not in {
            OrderStatus.CANCELED,
            OrderStatus.DRAFT,
            OrderStatus.EXPIRED,
        }

    def can_capture(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        order_status_ok = self.status not in {
            OrderStatus.DRAFT,
            OrderStatus.CANCELED,
            OrderStatus.EXPIRED,
        }
        return payment.can_capture() and order_status_ok

    def can_void(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        return payment.can_void()

    def can_refund(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        return payment.can_refund()

    def can_mark_as_paid(self, payments=None):
        if not payments:
            payments = self.payments.all()
        return len(payments) == 0

    @property
    def total_balance(self):
        return self.total_charged - self.total.gross


class OrderLineQueryset(models.QuerySet["OrderLine"]):
    def digital(self):
        """Return lines with digital products."""
        for line in self.all():
            if line.is_digital:
                yield line

    def physical(self):
        """Return lines with physical products."""
        for line in self.all():
            if not line.is_digital:
                yield line


OrderLineManager = models.Manager.from_queryset(OrderLineQueryset)


class OrderLine(ModelWithMetadata):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    old_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(
        Order,
        related_name="lines",
        editable=False,
        on_delete=models.CASCADE,
    )
    variant = models.ForeignKey(
        "product.ProductVariant",
        related_name="order_lines",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    # max_length is as produced by ProductVariant's display_product method
    product_name = models.CharField(max_length=386)
    variant_name = models.CharField(max_length=255, default="", blank=True)
    translated_product_name = models.CharField(max_length=386, default="", blank=True)
    translated_variant_name = models.CharField(max_length=255, default="", blank=True)
    product_sku = models.CharField(max_length=255, null=True, blank=True)
    # str with GraphQL ID used as fallback when product SKU is not available
    product_variant_id = models.CharField(max_length=255, null=True, blank=True)

    # denormalized product type id
    product_type_id = models.IntegerField(null=True, blank=True)

    is_shipping_required = models.BooleanField()
    is_gift_card = models.BooleanField()
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_fulfilled = models.IntegerField(
        validators=[MinValueValidator(0)], default=0
    )
    is_gift = models.BooleanField(default=False)

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )

    unit_discount_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    unit_discount = MoneyField(
        amount_field="unit_discount_amount", currency_field="currency"
    )
    unit_discount_type = models.CharField(
        max_length=10,
        choices=DiscountValueType.CHOICES,
        null=True,
        blank=True,
    )
    unit_discount_reason = models.TextField(blank=True, null=True)

    unit_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    # stores the value of the applied discount. Like 20 of %
    unit_discount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    unit_price_net = MoneyField(
        amount_field="unit_price_net_amount", currency_field="currency"
    )

    unit_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    unit_price_gross = MoneyField(
        amount_field="unit_price_gross_amount", currency_field="currency"
    )

    unit_price = TaxedMoneyField(
        net_amount_field="unit_price_net_amount",
        gross_amount_field="unit_price_gross_amount",
        currency_field="currency",
    )

    total_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    total_price_net = MoneyField(
        amount_field="total_price_net_amount",
        currency_field="currency",
    )

    total_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    total_price_gross = MoneyField(
        amount_field="total_price_gross_amount",
        currency_field="currency",
    )

    total_price = TaxedMoneyField(
        net_amount_field="total_price_net_amount",
        gross_amount_field="total_price_gross_amount",
        currency_field="currency",
    )

    undiscounted_unit_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    undiscounted_unit_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    undiscounted_unit_price = TaxedMoneyField(
        net_amount_field="undiscounted_unit_price_net_amount",
        gross_amount_field="undiscounted_unit_price_gross_amount",
        currency_field="currency",
    )

    undiscounted_total_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    undiscounted_total_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    undiscounted_total_price = TaxedMoneyField(
        net_amount_field="undiscounted_total_price_net_amount",
        gross_amount_field="undiscounted_total_price_gross_amount",
        currency_field="currency",
    )

    base_unit_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    base_unit_price = MoneyField(
        amount_field="base_unit_price_amount", currency_field="currency"
    )

    undiscounted_base_unit_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    undiscounted_base_unit_price = MoneyField(
        amount_field="undiscounted_base_unit_price_amount", currency_field="currency"
    )

    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4, blank=True, null=True
    )
    tax_class = models.ForeignKey(
        "tax.TaxClass",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    tax_class_name = models.CharField(max_length=255, blank=True, null=True)
    tax_class_private_metadata = JSONField(
        blank=True, db_default={}, default=dict, encoder=CustomJsonEncoder
    )
    tax_class_metadata = JSONField(
        blank=True, db_default={}, default=dict, encoder=CustomJsonEncoder
    )
    tax_class_country_rate = models.ForeignKey(
        "tax.TaxClassCountryRate",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    xero_tax_code = models.CharField(max_length=50, blank=True, null=True)

    is_price_overridden = models.BooleanField(null=True, blank=True)

    # Fulfilled when voucher code was used for product in the line
    voucher_code = models.CharField(max_length=255, null=True, blank=True)

    # Fulfilled when sale was applied to product in the line
    sale_id = models.CharField(max_length=255, null=True, blank=True)

    # The date time when the line should refresh its prices.
    # It depends on channel.draft_order_line_price_freeze_period setting.
    draft_base_price_expire_at = models.DateTimeField(blank=True, null=True)

    objects = OrderLineManager()

    class Meta(ModelWithMetadata.Meta):
        ordering = ("created_at", "id")

        indexes = [
            *ModelWithMetadata.Meta.indexes,
            BTreeIndex(fields=["product_type_id"], name="product_type_id_btree_idx"),
        ]

    def __str__(self):
        return (
            f"{self.product_name} ({self.variant_name})"
            if self.variant_name
            else self.product_name
        )

    @property
    def quantity_unfulfilled(self):
        return self.quantity - self.quantity_fulfilled

    @property
    def is_digital(self) -> bool:
        """Check if a variant is digital and contains digital content."""
        if not self.variant:
            return False
        is_digital = self.variant.is_digital()
        has_digital = hasattr(self.variant, "digital_content")
        return is_digital and has_digital


class Fulfillment(ModelWithMetadata):
    """Note that an Order can be fulfilled by multiple shipments.

    We can put multiple orders in the same shipment. This is how we see the stock
    that has left the warehouse.
    """

    fulfillment_order = models.PositiveIntegerField(editable=False)
    order = models.ForeignKey(
        Order,
        related_name="fulfillments",
        editable=False,
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=32,
        default=FulfillmentStatus.FULFILLED,
        choices=FulfillmentStatus.CHOICES,
    )
    shipment = models.ForeignKey(
        "shipping.Shipment",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="fulfillments",
    )
    tracking_url = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="Tracking URL or number from carrier",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    shipping_refund_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        null=True,
        blank=True,
    )
    total_refund_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        null=True,
        blank=True,
    )

    deposit_allocated_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    xero_quote_id = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        help_text="Xero Quote UUID for the proforma quote linked to this fulfillment.",
    )
    xero_quote_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Xero Quote number (e.g. Q-1234).",
    )
    xero_proforma_prepayment_id = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        help_text="Xero prepayment UUID for the proforma payment on this fulfillment.",
    )

    class Meta(ModelWithMetadata.Meta):
        ordering = ("pk",)
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            BTreeIndex(fields=["status"], name="fulfillment_status_idx"),
        ]

    def __str__(self):
        return f"Fulfillment #{self.composed_id}"

    def __iter__(self):
        return iter(self.lines.all())

    def clean(self):
        from django.core.exceptions import ValidationError

        from ..shipping import ShipmentType

        super().clean()

        if self.shipment_id and self.shipment:
            if self.shipment.shipment_type != ShipmentType.OUTBOUND:
                raise ValidationError(
                    {
                        "shipment": (
                            f"Cannot link fulfillment to {self.shipment.shipment_type} shipment. "
                            "Fulfillments can only be linked to outbound shipments."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        """Assign an auto incremented value as a fulfillment order."""
        if not self.pk:
            groups = self.order.fulfillments.all()
            existing_max = groups.aggregate(Max("fulfillment_order"))
            existing_max = existing_max.get("fulfillment_order__max")
            self.fulfillment_order = existing_max + 1 if existing_max is not None else 1

        if self.shipment_id:
            self.clean()

        return super().save(*args, **kwargs)

    @property
    def composed_id(self):
        return f"{self.order.number}-{self.fulfillment_order}"

    def can_edit(self):
        return self.status != FulfillmentStatus.CANCELED

    def get_total_quantity(self):
        return sum([line.quantity for line in self.lines.all()])

    @property
    def is_tracking_number_url(self):
        return bool(match(r"^[-\w]+://", self.tracking_url))

    @property
    def has_inventory_received(self):
        """Check if all required inventory has been received in the warehouse.

        Returns True if all allocations for this fulfillment's order lines
        have AllocationSources with quantities matching the allocation quantities,
        AND all linked purchase order shipments have arrived (arrived_at is set).

        Returns False if any owned warehouse allocations lack sources, have
        mismatched quantities, or if any shipments haven't arrived yet.
        """
        from django.db.models import Sum

        has_owned_allocations = False

        for line in self.lines.all():
            order_line = line.order_line
            allocations = order_line.allocations.filter(stock__warehouse__is_owned=True)

            for allocation in allocations:
                has_owned_allocations = True
                total_sourced = (
                    allocation.allocation_sources.aggregate(total=Sum("quantity"))[
                        "total"
                    ]
                    or 0
                )

                if total_sourced != allocation.quantity_allocated:
                    return False

                for allocation_source in allocation.allocation_sources.all():
                    poi = allocation_source.purchase_order_item

                    if not poi.shipment:
                        return False

                    if not poi.shipment.arrived_at:
                        return False

        return has_owned_allocations

    def has_po_sourced_allocations(self):
        """Check if this fulfillment has any allocations sourced from purchase orders.

        Returns True if any allocation for this fulfillment's order lines
        has AllocationSources linked to purchase orders.
        """
        for line in self.lines.all():
            order_line = line.order_line
            allocations = order_line.allocations.filter(stock__warehouse__is_owned=True)

            for allocation in allocations:
                if allocation.allocation_sources.exists():
                    return True

        return False

    @property
    def deposit_allocated(self):
        from ..core.prices import Money

        return Money(self.deposit_allocated_amount, self.order.currency)

    def can_auto_transition_to_fulfilled(self):
        """Check whether this fulfillment can auto-transition to fulfilled.

        We need to have a shipment booked, pick completed and the proforma needs
        to have been paid.
        """
        from . import PickStatus

        if self.status != FulfillmentStatus.WAITING_FOR_APPROVAL:
            return False

        try:
            pick_complete = self.pick.status == PickStatus.COMPLETED
        except Pick.DoesNotExist:
            return False

        if not pick_complete:
            return False

        if not self.shipment_id:
            return False

        from . import OrderOrigin

        order = self.order
        if order.origin != OrderOrigin.CHECKOUT:
            if (
                not self.xero_proforma_prepayment_id
                or not order.payments.filter(
                    psp_reference=self.xero_proforma_prepayment_id
                ).exists()
            ):
                return False

        return True


class FulfillmentLine(models.Model):
    """Represents line items in a fulfillment.

    For our use case quantity needs to equal order_line quantity.
    """

    order_line = models.ForeignKey(
        OrderLine,
        related_name="fulfillment_lines",
        on_delete=models.CASCADE,
    )
    fulfillment = models.ForeignKey(
        Fulfillment, related_name="lines", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    stock = models.ForeignKey(
        "warehouse.Stock",
        related_name="fulfillment_lines",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )


class Pick(models.Model):
    """Document for picking items from warehouse for order fulfillment.

    Tracks the physical picking process for outbound fulfillments. When warehouse staff
    pick items for an order, they work through a Pick document to record what was
    physically picked from the warehouse.

    Workflow:
    1. Auto-created when Fulfillment is created with WAITING_FOR_APPROVAL status
    2. Warehouse staff start pick (status=IN_PROGRESS)
    3. Staff scan/update items as they pick (updates PickItems)
    4. Complete Pick (status=COMPLETED) → enables FulfillmentApprove
    """

    fulfillment = models.OneToOneField(
        Fulfillment,
        on_delete=models.CASCADE,
        related_name="pick",
        help_text="Fulfillment being picked",
    )

    status = models.CharField(
        max_length=32,
        choices=PickStatus.CHOICES,
        default=PickStatus.NOT_STARTED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When picking was started",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When picking was completed",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="picks_created",
        help_text="User who created the pick",
    )

    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="picks_started",
        help_text="Warehouse staff who started picking",
    )

    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="picks_completed",
        help_text="Warehouse staff who completed picking",
    )

    notes = models.TextField(blank=True, help_text="Additional notes about this pick")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["fulfillment", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"Pick #{self.id} for Fulfillment #{self.fulfillment_id}"


class PickItem(models.Model):
    """Individual line item in a pick document.

    Tracks what needs to be picked vs what was actually picked for each OrderLine.
    """

    pick = models.ForeignKey(
        Pick,
        on_delete=models.CASCADE,
        related_name="items",
    )

    order_line = models.ForeignKey(
        OrderLine,
        on_delete=models.CASCADE,
        related_name="pick_items",
        help_text="Which order line this item picks for",
    )

    quantity_to_pick = models.PositiveIntegerField(
        help_text="Quantity that needs to be picked (from fulfillment line)"
    )

    quantity_picked = models.PositiveIntegerField(
        default=0,
        help_text="Quantity physically picked from warehouse",
    )

    picked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this item was marked as fully picked",
    )

    picked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pick_items_picked",
        help_text="Warehouse staff who picked this item",
    )

    notes = models.TextField(
        blank=True, help_text="Notes about picking this specific item"
    )

    class Meta:
        indexes = [
            models.Index(fields=["pick", "order_line"]),
        ]

    @property
    def is_fully_picked(self):
        return self.quantity_picked >= self.quantity_to_pick

    def __str__(self):
        return f"PickItem #{self.id}: {self.quantity_picked}/{self.quantity_to_pick} for OrderLine #{self.order_line_id}"


class OrderEvent(models.Model):
    """Model used to store events that happened during the order lifecycle.

    Args:
        parameters: Values needed to display the event on the storefront
        type: Type of an order

    """

    date = models.DateTimeField(default=now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=[
            (type_name.upper(), type_name) for type_name, _ in OrderEvents.CHOICES
        ],
    )
    order = models.ForeignKey(Order, related_name="events", on_delete=models.CASCADE)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    app = models.ForeignKey(App, related_name="+", on_delete=models.SET_NULL, null=True)
    related = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="related_events",
        db_index=False,
    )

    class Meta:
        ordering = ("date",)
        indexes = [
            BTreeIndex(fields=["related"], name="order_orderevent_related_id_idx"),
            models.Index(fields=["type"]),
            BTreeIndex(fields=["date"], name="order_orderevent_date_idx"),
        ]

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"


class OrderGrantedRefund(models.Model):
    """Model used to store granted refund for the order."""

    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False, db_index=True)

    amount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    amount = MoneyField(amount_field="amount_value", currency_field="currency")
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )
    reason = models.TextField(blank=True, default="")
    reason_reference = models.ForeignKey(
        "page.Page", related_name="+", on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    app = models.ForeignKey(
        App, related_name="+", on_delete=models.SET_NULL, null=True, blank=True
    )
    order = models.ForeignKey(
        Order, related_name="granted_refunds", on_delete=models.CASCADE
    )
    shipping_costs_included = models.BooleanField(default=False)

    transaction_item = models.ForeignKey(
        "payment.TransactionItem",
        related_name="granted_refund",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    status = models.CharField(
        choices=OrderGrantedRefundStatus.CHOICES,
        default=OrderGrantedRefundStatus.NONE,
        max_length=128,
    )

    class Meta:
        ordering = ("created_at", "id")


class OrderGrantedRefundLine(models.Model):
    """Model used to store granted refund line for the order."""

    order_line = models.ForeignKey(
        OrderLine, related_name="granted_refund_lines", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()

    granted_refund = models.ForeignKey(
        OrderGrantedRefund, related_name="lines", on_delete=models.CASCADE
    )

    reason = models.TextField(blank=True, null=True, default="")
