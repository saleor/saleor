import graphene
from django.core.exceptions import ValidationError
from graphene import relay
from graphql_jwt.exceptions import PermissionDenied

from ...core.permissions import AccountPermissions, OrderPermissions
from ...core.taxes import display_gross_prices
from ...order import OrderStatus, models
from ...order.models import FulfillmentStatus
from ...order.utils import get_order_country, get_valid_shipping_methods_for_order
from ...plugins.manager import get_plugins_manager
from ...product.templatetags.product_images import get_product_image_thumbnail
from ...warehouse import models as warehouse_models
from ..account.types import User
from ..core.connection import CountableDjangoObjectType
from ..core.types.common import Image
from ..core.types.money import Money, TaxedMoney
from ..decorators import permission_required
from ..giftcard.types import GiftCard
from ..meta.deprecated.resolvers import resolve_meta, resolve_private_meta
from ..meta.types import ObjectWithMetadata
from ..payment.types import OrderAction, Payment, PaymentChargeStatusEnum
from ..product.types import ProductVariant
from ..shipping.types import ShippingMethod
from ..warehouse.types import Warehouse
from .enums import OrderEventsEmailsEnum, OrderEventsEnum
from .utils import validate_draft_order


class OrderEventOrderLineObject(graphene.ObjectType):
    quantity = graphene.Int(description="The variant quantity.")
    order_line = graphene.Field(lambda: OrderLine, description="The order line.")
    item_name = graphene.String(description="The variant name.")


class OrderEvent(CountableDjangoObjectType):
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = OrderEventsEnum(description="Order event type.")
    user = graphene.Field(User, description="User who performed the action.")
    message = graphene.String(description="Content of the event.")
    email = graphene.String(description="Email of the customer.")
    email_type = OrderEventsEmailsEnum(
        description="Type of an email sent to the customer."
    )
    amount = graphene.Float(description="Amount of money.")
    payment_id = graphene.String(description="The payment ID from the payment gateway.")
    payment_gateway = graphene.String(description="The payment gateway of the payment.")
    quantity = graphene.Int(description="Number of items.")
    composed_id = graphene.String(description="Composed ID of the Fulfillment.")
    order_number = graphene.String(description="User-friendly number of an order.")
    oversold_items = graphene.List(
        graphene.String, description="List of oversold lines names."
    )
    lines = graphene.List(OrderEventOrderLineObject, description="The concerned lines.")
    fulfilled_items = graphene.List(
        lambda: FulfillmentLine, description="The lines fulfilled."
    )
    warehouse = graphene.Field(
        Warehouse, description="The warehouse were items were restocked."
    )

    class Meta:
        description = "History log of the order."
        model = models.OrderEvent
        interfaces = [relay.Node]
        only_fields = ["id"]

    @staticmethod
    def resolve_user(root: models.OrderEvent, info):
        user = info.context.user
        if (
            user == root.user
            or user.has_perm(AccountPermissions.MANAGE_USERS)
            or user.has_perm(AccountPermissions.MANAGE_STAFF)
        ):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_email(root: models.OrderEvent, _info):
        return root.parameters.get("email", None)

    @staticmethod
    def resolve_email_type(root: models.OrderEvent, _info):
        return root.parameters.get("email_type", None)

    @staticmethod
    def resolve_amount(root: models.OrderEvent, _info):
        amount = root.parameters.get("amount", None)
        return float(amount) if amount else None

    @staticmethod
    def resolve_payment_id(root: models.OrderEvent, _info):
        return root.parameters.get("payment_id", None)

    @staticmethod
    def resolve_payment_gateway(root: models.OrderEvent, _info):
        return root.parameters.get("payment_gateway", None)

    @staticmethod
    def resolve_quantity(root: models.OrderEvent, _info):
        quantity = root.parameters.get("quantity", None)
        return int(quantity) if quantity else None

    @staticmethod
    def resolve_message(root: models.OrderEvent, _info):
        return root.parameters.get("message", None)

    @staticmethod
    def resolve_composed_id(root: models.OrderEvent, _info):
        return root.parameters.get("composed_id", None)

    @staticmethod
    def resolve_oversold_items(root: models.OrderEvent, _info):
        return root.parameters.get("oversold_items", None)

    @staticmethod
    def resolve_order_number(root: models.OrderEvent, _info):
        return root.order_id

    @staticmethod
    def resolve_lines(root: models.OrderEvent, _info):
        raw_lines = root.parameters.get("lines", None)

        if not raw_lines:
            return None

        line_pks = []
        for entry in raw_lines:
            line_pks.append(entry.get("line_pk", None))

        lines = models.OrderLine.objects.filter(pk__in=line_pks).all()
        results = []
        for raw_line, line_pk in zip(raw_lines, line_pks):
            line_object = None
            for line in lines:
                if line.pk == line_pk:
                    line_object = line
                    break
            results.append(
                OrderEventOrderLineObject(
                    quantity=raw_line["quantity"],
                    order_line=line_object,
                    item_name=raw_line["item"],
                )
            )

        return results

    @staticmethod
    def resolve_fulfilled_items(root: models.OrderEvent, _info):
        lines = root.parameters.get("fulfilled_items", None)
        return models.FulfillmentLine.objects.filter(pk__in=lines)

    @staticmethod
    def resolve_warehouse(root: models.OrderEvent, _info):
        warehouse = root.parameters.get("warehouse")
        return warehouse_models.Warehouse.objects.filter(pk=warehouse).first()


class FulfillmentLine(CountableDjangoObjectType):
    order_line = graphene.Field(lambda: OrderLine)

    class Meta:
        description = "Represents line of the fulfillment."
        interfaces = [relay.Node]
        model = models.FulfillmentLine
        only_fields = ["id", "quantity"]

    @staticmethod
    def resolve_order_line(root: models.FulfillmentLine, _info):
        return root.order_line


class Fulfillment(CountableDjangoObjectType):
    lines = graphene.List(
        FulfillmentLine, description="List of lines for the fulfillment."
    )
    status_display = graphene.String(description="User-friendly fulfillment status.")
    warehouse = graphene.Field(
        Warehouse,
        required=False,
        description=("Warehouse from fulfillment was fulfilled."),
    )

    class Meta:
        description = "Represents order fulfillment."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Fulfillment
        only_fields = [
            "fulfillment_order",
            "id",
            "created",
            "status",
            "tracking_number",
        ]

    @staticmethod
    def resolve_lines(root: models.Fulfillment, _info):
        return root.lines.all()

    @staticmethod
    def resolve_status_display(root: models.Fulfillment, _info):
        return root.get_status_display()

    @staticmethod
    def resolve_warehouse(root: models.Fulfillment, _info):
        line = root.lines.first()
        return line.stock.warehouse if line and line.stock else None

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_private_meta(root: models.Fulfillment, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.Fulfillment, _info):
        return resolve_meta(root, _info)


class OrderLine(CountableDjangoObjectType):
    thumbnail = graphene.Field(
        Image,
        description="The main thumbnail for the ordered product.",
        size=graphene.Argument(graphene.Int, description="Size of thumbnail."),
    )
    unit_price = graphene.Field(
        TaxedMoney, description="Price of the single item in the order line."
    )
    variant = graphene.Field(
        ProductVariant,
        required=False,
        description=(
            "A purchased product variant. Note: this field may be null if the variant "
            "has been removed from stock at all."
        ),
    )
    translated_product_name = graphene.String(
        required=True, description="Product name in the customer's language"
    )
    translated_variant_name = graphene.String(
        required=True, description="Variant name in the customer's language"
    )

    class Meta:
        description = "Represents order line of particular order."
        model = models.OrderLine
        interfaces = [relay.Node]
        only_fields = [
            "digital_content_url",
            "id",
            "is_shipping_required",
            "product_name",
            "variant_name",
            "product_sku",
            "quantity",
            "quantity_fulfilled",
            "tax_rate",
        ]

    @staticmethod
    def resolve_thumbnail(root: models.OrderLine, info, *, size=255):
        if not root.variant:
            return None
        image = root.variant.get_first_image()
        if image:
            url = get_product_image_thumbnail(image, size, method="thumbnail")
            alt = image.alt
            return Image(alt=alt, url=info.context.build_absolute_uri(url))
        return None

    @staticmethod
    def resolve_unit_price(root: models.OrderLine, _info):
        return root.unit_price

    @staticmethod
    def resolve_translated_product_name(root: models.OrderLine, _info):
        return root.translated_product_name

    @staticmethod
    def resolve_translated_variant_name(root: models.OrderLine, _info):
        return root.translated_variant_name


class Order(CountableDjangoObjectType):
    fulfillments = graphene.List(
        Fulfillment, required=True, description="List of shipments for the order."
    )
    lines = graphene.List(
        lambda: OrderLine, required=True, description="List of order lines."
    )
    actions = graphene.List(
        OrderAction,
        description=(
            "List of actions that can be performed in the current state of an order."
        ),
        required=True,
    )
    available_shipping_methods = graphene.List(
        ShippingMethod,
        required=False,
        description="Shipping methods that can be used with this order.",
    )
    number = graphene.String(description="User-friendly number of an order.")
    is_paid = graphene.Boolean(description="Informs if an order is fully paid.")
    payment_status = PaymentChargeStatusEnum(description="Internal payment status.")
    payment_status_display = graphene.String(
        description="User-friendly payment status."
    )
    payments = graphene.List(Payment, description="List of payments for the order.")
    total = graphene.Field(TaxedMoney, description="Total amount of the order.")
    shipping_price = graphene.Field(TaxedMoney, description="Total price of shipping.")
    subtotal = graphene.Field(
        TaxedMoney, description="The sum of line prices not including shipping."
    )
    gift_cards = graphene.List(GiftCard, description="List of user gift cards.")
    status_display = graphene.String(description="User-friendly order status.")
    can_finalize = graphene.Boolean(
        description=(
            "Informs whether a draft order can be finalized"
            "(turned into a regular order)."
        ),
        required=True,
    )
    total_authorized = graphene.Field(
        Money, description="Amount authorized for the order."
    )
    total_captured = graphene.Field(Money, description="Amount captured by payment.")
    events = graphene.List(
        OrderEvent, description="List of events associated with the order."
    )
    total_balance = graphene.Field(
        Money,
        description="The difference between the paid and the order total amount.",
        required=True,
    )
    user_email = graphene.String(
        required=False, description="Email address of the customer."
    )
    is_shipping_required = graphene.Boolean(
        description="Returns True, if order requires shipping.", required=True
    )

    class Meta:
        description = "Represents an order in the shop."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Order
        only_fields = [
            "billing_address",
            "created",
            "customer_note",
            "discount",
            "discount_name",
            "display_gross_prices",
            "gift_cards",
            "id",
            "language_code",
            "shipping_address",
            "shipping_method",
            "shipping_method_name",
            "shipping_price",
            "status",
            "token",
            "tracking_client_id",
            "translated_discount_name",
            "user",
            "voucher",
            "weight",
        ]

    @staticmethod
    def resolve_shipping_price(root: models.Order, _info):
        return root.shipping_price

    @staticmethod
    def resolve_actions(root: models.Order, _info):
        actions = []
        payment = root.get_last_payment()
        if root.can_capture(payment):
            actions.append(OrderAction.CAPTURE)
        if root.can_mark_as_paid():
            actions.append(OrderAction.MARK_AS_PAID)
        if root.can_refund(payment):
            actions.append(OrderAction.REFUND)
        if root.can_void(payment):
            actions.append(OrderAction.VOID)
        return actions

    @staticmethod
    def resolve_subtotal(root: models.Order, _info):
        return root.get_subtotal()

    @staticmethod
    def resolve_total(root: models.Order, _info):
        return root.total

    @staticmethod
    def resolve_total_authorized(root: models.Order, _info):
        # FIXME adjust to multiple payments in the future
        return root.total_authorized

    @staticmethod
    def resolve_total_captured(root: models.Order, _info):
        # FIXME adjust to multiple payments in the future
        return root.total_captured

    @staticmethod
    def resolve_total_balance(root: models.Order, _info):
        return root.total_balance

    @staticmethod
    def resolve_fulfillments(root: models.Order, info):
        user = info.context.user
        if user.is_staff:
            qs = root.fulfillments.all()
        else:
            qs = root.fulfillments.exclude(status=FulfillmentStatus.CANCELED)
        return qs.order_by("pk")

    @staticmethod
    def resolve_lines(root: models.Order, _info):
        return root.lines.all().order_by("pk")

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_events(root: models.Order, _info):
        return root.events.all().order_by("pk")

    @staticmethod
    def resolve_is_paid(root: models.Order, _info):
        return root.is_fully_paid()

    @staticmethod
    def resolve_number(root: models.Order, _info):
        return str(root.pk)

    @staticmethod
    def resolve_payment_status(root: models.Order, _info):
        return root.get_payment_status()

    @staticmethod
    def resolve_payment_status_display(root: models.Order, _info):
        return root.get_payment_status_display()

    @staticmethod
    def resolve_payments(root: models.Order, _info):
        return root.payments.all()

    @staticmethod
    def resolve_status_display(root: models.Order, _info):
        return root.get_status_display()

    @staticmethod
    def resolve_can_finalize(root: models.Order, _info):
        if root.status == OrderStatus.DRAFT:
            country = get_order_country(root)
            try:
                validate_draft_order(root, country)
            except ValidationError:
                return False
        return True

    @staticmethod
    def resolve_user_email(root: models.Order, _info):
        return root.get_customer_email()

    @staticmethod
    def resolve_user(root: models.Order, info):
        user = info.context.user
        if user == root.user or user.has_perm(AccountPermissions.MANAGE_USERS):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_available_shipping_methods(root: models.Order, _info):
        available = get_valid_shipping_methods_for_order(root)
        if available is None:
            return []

        manager = get_plugins_manager()
        display_gross = display_gross_prices()
        for shipping_method in available:
            # Ignore typing check because it is checked in
            # get_valid_shipping_methods_for_order
            taxed_price = manager.apply_taxes_to_shipping(
                shipping_method.price, root.shipping_address  # type: ignore
            )
            if display_gross:
                shipping_method.price = taxed_price.gross
            else:
                shipping_method.price = taxed_price.net
        return available

    @staticmethod
    def resolve_is_shipping_required(root: models.Order, _info):
        return root.is_shipping_required()

    @staticmethod
    def resolve_gift_cards(root: models.Order, _info):
        return root.gift_cards.all()

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_private_meta(root: models.Order, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.Order, _info):
        return resolve_meta(root, _info)
