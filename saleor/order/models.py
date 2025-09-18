import copy
from decimal import Decimal
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
from django.forms.models import model_to_dict
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
from ..shipping.models import ShippingMethod
from . import (
    FulfillmentStatus,
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderGrantedRefundStatus,
    OrderOrigin,
    OrderStatus,
)

if TYPE_CHECKING:
    from ..account.models import User


class OrderQueryset(models.QuerySet["Order"]):
    """订单模型的自定义查询集。"""

    def get_by_checkout_token(self, token):
        """通过结帐令牌返回非草稿订单。"""
        return self.non_draft().filter(checkout_token=token).first()

    def confirmed(self):
        """返回已确认的订单（非草稿或未确认）。"""
        return self.exclude(status__in=[OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])

    def non_draft(self):
        """返回非草稿订单。"""
        return self.exclude(status=OrderStatus.DRAFT)

    def drafts(self):
        """返回草稿订单。"""
        return self.filter(status=OrderStatus.DRAFT)

    def ready_to_fulfill(self):
        """返回可履行的订单。

        可履行的订单是已完全付款但未履行（或部分履行）的订单。
        """
        statuses = {OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED}
        payments = Payment.objects.filter(is_active=True).values("id")
        return self.filter(
            Exists(payments.filter(order_id=OuterRef("id"))),
            status__in=statuses,
            total_gross_amount__lte=F("total_charged_amount"),
        )

    def ready_to_capture(self):
        """返回有待收款的订单。

        有待收款的订单是指那些非草稿或已取消，并且具有预授权付款的订单。
        预授权付款不能已经被部分或全部收款。
        """
        payments = Payment.objects.filter(
            is_active=True, charge_status=ChargeStatus.NOT_CHARGED
        ).values("id")
        qs = self.filter(Exists(payments.filter(order_id=OuterRef("id"))))
        return qs.exclude(
            status={OrderStatus.DRAFT, OrderStatus.CANCELED, OrderStatus.EXPIRED}
        )

    def ready_to_confirm(self):
        """返回未确认的订单。"""
        return self.filter(status=OrderStatus.UNCONFIRMED)


OrderManager = models.Manager.from_queryset(OrderQueryset)


def get_order_number():
    """从数据库序列中获取下一个订单号。"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('order_order_number_seq')")
        result = cursor.fetchone()
        return result[0]


class Order(ModelWithMetadata, ModelWithExternalReference):
    """订单模型。

    代表客户的订单。

    Attributes:
        status (str): 订单的状态。
        user (User): 与此订单关联的用户。
        billing_address (Address): 账单地址。
        shipping_address (Address): 送货地址。
        total (TaxedMoney): 订单的总金额。
        ... (许多其他字段)
    """

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
        blank=True, null=True, default=dict, encoder=CustomJsonEncoder
    )
    shipping_tax_class_metadata = JSONField(
        blank=True, null=True, default=dict, encoder=CustomJsonEncoder
    )

    # Token of a checkout instance that this order was created from
    checkout_token = models.CharField(max_length=36, blank=True)

    lines_count = models.PositiveIntegerField(blank=True, null=True)

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
        ]

    @property
    def comparison_fields(self):
        return [
            "discount",
            "voucher",
            "voucher_code",
            "customer_note",
            "redirect_url",
            "external_reference",
            "user",
            "user_email",
            "channel",
            "metadata",
            "private_metadata",
            "draft_save_billing_address",
            "draft_save_shipping_address",
            "language_code",
        ]

    def serialize_for_comparison(self):
        return copy.deepcopy(model_to_dict(self, fields=self.comparison_fields))

    def is_fully_paid(self):
        """检查订单是否已完全付款。"""
        return self.total_charged >= self.total.gross

    def is_partly_paid(self):
        """检查订单是否已部分付款。"""
        return self.total_charged_amount > 0

    def get_customer_email(self):
        """获取客户的电子邮件地址。"""
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
        """获取订单的最后一次付款。

        跳过部分付款。
        """
        # Skipping a partial payment is a temporary workaround for storing a basic data
        # about partial payment from Adyen plugin. This is something that will removed
        # in 3.1 by introducing a partial payments feature.
        payments: list[Payment] = [
            payment for payment in self.payments.all() if not payment.partial
        ]
        return max(payments, default=None, key=attrgetter("pk"))

    def is_pre_authorized(self):
        """检查订单是否有成功的预授权付款。"""
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
        """检查订单是否有成功的收款。"""
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
        """获取订单的小计。"""
        return get_subtotal(self.lines.all(), self.currency)

    def is_shipping_required(
        self, database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME
    ):
        """检查订单是否需要配送。"""
        return any(
            line.is_shipping_required
            for line in self.lines.using(database_connection_name).all()
        )

    def get_total_quantity(self):
        """获取订单中所有商品的总数量。"""
        return sum([line.quantity for line in self.lines.all()])

    def is_draft(self):
        """检查订单是否为草稿。"""
        return self.status == OrderStatus.DRAFT

    def is_unconfirmed(self):
        """检查订单是否未确认。"""
        return self.status == OrderStatus.UNCONFIRMED

    def is_expired(self):
        """检查订单是否已过期。"""
        return self.status == OrderStatus.EXPIRED

    def is_open(self):
        """检查订单是否为开放状态（未履行或部分履行）。"""
        statuses = {OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED}
        return self.status in statuses

    def can_cancel(self):
        """检查订单是否可以取消。"""
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
        """检查订单是否可以收款。"""
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
        """检查订单是否可以作废付款。"""
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        return payment.can_void()

    def can_refund(self, payment=None):
        """检查订单是否可以退款。"""
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        return payment.can_refund()

    def can_mark_as_paid(self, payments=None):
        """检查订单是否可以标记为已付款。"""
        if not payments:
            payments = self.payments.all()
        return len(payments) == 0

    @property
    def total_balance(self):
        return self.total_charged - self.total.gross


class OrderLineQueryset(models.QuerySet["OrderLine"]):
    """订单行模型的自定义查询集。"""

    def digital(self):
        """返回包含电子产品的订单行。"""
        for line in self.all():
            if line.is_digital:
                yield line

    def physical(self):
        """返回包含实体产品的订单行。"""
        for line in self.all():
            if not line.is_digital:
                yield line


OrderLineManager = models.Manager.from_queryset(OrderLineQueryset)


class OrderLine(ModelWithMetadata):
    """订单行模型。

    代表订单中的一个项目。

    Attributes:
        order (Order): 此订单行所属的订单。
        variant (ProductVariant): 关联的产品变体。
        quantity (int): 订购的数量。
        unit_price (TaxedMoney): 商品的单价。
        total_price (TaxedMoney): 此行的总价。
        ... (许多其他字段)
    """

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
        blank=True, null=True, default=dict, encoder=CustomJsonEncoder
    )
    tax_class_metadata = JSONField(
        blank=True, null=True, default=dict, encoder=CustomJsonEncoder
    )

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

    def __str__(self):
        return (
            f"{self.product_name} ({self.variant_name})"
            if self.variant_name
            else self.product_name
        )

    @property
    def quantity_unfulfilled(self):
        """返回未履行的数量。"""
        return self.quantity - self.quantity_fulfilled

    @property
    def is_digital(self) -> bool:
        """检查变体是否为电子产品并包含电子内容。"""
        if not self.variant:
            return False
        is_digital = self.variant.is_digital()
        has_digital = hasattr(self.variant, "digital_content")
        return is_digital and has_digital


class Fulfillment(ModelWithMetadata):
    """履行模型。

    代表订单的一部分或全部商品的配送。

    Attributes:
        fulfillment_order (int): 履行的顺序号。
        order (Order): 此履行所属的订单。
        status (str): 履行的状态。
        tracking_number (str): 运单号。
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
    tracking_number = models.CharField(max_length=255, default="", blank=True)
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

    class Meta(ModelWithMetadata.Meta):
        ordering = ("pk",)

    def __str__(self):
        return f"Fulfillment #{self.composed_id}"

    def __iter__(self):
        return iter(self.lines.all())

    def save(self, *args, **kwargs):
        """分配一个自动递增的值作为履行顺序。"""
        if not self.pk:
            groups = self.order.fulfillments.all()
            existing_max = groups.aggregate(Max("fulfillment_order"))
            existing_max = existing_max.get("fulfillment_order__max")
            self.fulfillment_order = existing_max + 1 if existing_max is not None else 1
        return super().save(*args, **kwargs)

    @property
    def composed_id(self):
        """返回组合的 ID（订单号-履行顺序）。"""
        return f"{self.order.number}-{self.fulfillment_order}"

    def can_edit(self):
        """检查履行是否可以编辑。"""
        return self.status != FulfillmentStatus.CANCELED

    def get_total_quantity(self):
        """获取此履行中所有商品的总数量。"""
        return sum([line.quantity for line in self.lines.all()])

    @property
    def is_tracking_number_url(self):
        """检查运单号是否为 URL。"""
        return bool(match(r"^[-\w]+://", self.tracking_number))


class FulfillmentLine(models.Model):
    """履行行模型。

    代表履行中的一个项目。
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


class OrderEvent(models.Model):
    """用于存储订单生命周期中发生的事件的模型。

    Args:
        parameters: 在店面显示事件所需的值
        type: 订单的类型

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
        ]

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"


class OrderGrantedRefund(models.Model):
    """用于存储订单已批准退款的模型。"""

    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False, db_index=True)

    amount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )
    amount = MoneyField(amount_field="amount_value", currency_field="currency")
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )
    reason = models.TextField(blank=True, default="")
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
    """用于存储订单已批准退款行的模型。"""

    order_line = models.ForeignKey(
        OrderLine, related_name="granted_refund_lines", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()

    granted_refund = models.ForeignKey(
        OrderGrantedRefund, related_name="lines", on_delete=models.CASCADE
    )

    reason = models.TextField(blank=True, null=True, default="")
