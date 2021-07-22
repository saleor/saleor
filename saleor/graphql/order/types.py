from decimal import Decimal
from operator import attrgetter
from typing import Optional

import graphene
import prices
from django.core.exceptions import ValidationError
from graphene import relay
from promise import Promise

from ...account.models import Address
from ...account.utils import requestor_is_staff_member_or_app
from ...core.anonymize import obfuscate_address, obfuscate_email
from ...core.exceptions import PermissionDenied
from ...core.permissions import (
    AccountPermissions,
    AppPermission,
    OrderPermissions,
    ProductPermissions,
)
from ...core.taxes import display_gross_prices
from ...core.tracing import traced_resolver
from ...discount import OrderDiscountType
from ...graphql.utils import get_user_or_app_from_context
from ...graphql.warehouse.dataloaders import WarehouseByIdLoader
from ...order import OrderStatus, models
from ...order.models import FulfillmentStatus
from ...order.utils import get_order_country, get_valid_shipping_methods_for_order
from ...payment import ChargeStatus
from ...payment.dataloaders import PaymentsByOrderIdLoader
from ...payment.model_helpers import (
    get_last_payment,
    get_subtotal,
    get_total_authorized,
)
from ...product import ProductMediaTypes
from ...product.product_images import get_product_image_thumbnail
from ..account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ..account.types import User
from ..account.utils import requestor_has_access
from ..app.dataloaders import AppByIdLoader
from ..app.types import App
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByIdLoader, ChannelByOrderLineIdLoader
from ..core.connection import CountableDjangoObjectType
from ..core.enums import LanguageCodeEnum
from ..core.mutations import validation_error_to_error_type
from ..core.scalars import PositiveDecimal
from ..core.types.common import Image, OrderError
from ..core.types.money import Money, TaxedMoney
from ..core.utils import str_to_enum
from ..decorators import one_of_permissions_required, permission_required
from ..discount.dataloaders import OrderDiscountsByOrderIDLoader, VoucherByIdLoader
from ..discount.enums import DiscountValueTypeEnum
from ..giftcard.types import GiftCard
from ..invoice.types import Invoice
from ..meta.types import ObjectWithMetadata
from ..payment.types import OrderAction, Payment, PaymentChargeStatusEnum
from ..product.dataloaders import (
    MediaByProductVariantIdLoader,
    ProductByVariantIdLoader,
    ProductChannelListingByProductIdAndChannelSlugLoader,
    ProductImageByProductIdLoader,
    ProductVariantByIdLoader,
)
from ..product.types import ProductVariant
from ..shipping.dataloaders import ShippingMethodByIdLoader
from ..shipping.types import ShippingMethod
from ..warehouse.types import Allocation, Warehouse
from .dataloaders import (
    AllocationsByOrderLineIdLoader,
    FulfillmentLinesByIdLoader,
    FulfillmentsByOrderIdLoader,
    OrderByIdLoader,
    OrderEventsByOrderIdLoader,
    OrderLineByIdLoader,
    OrderLinesByOrderIdLoader,
)
from .enums import OrderEventsEmailsEnum, OrderEventsEnum, OrderOriginEnum
from .utils import validate_draft_order


def get_order_discount_event(discount_obj: dict):
    currency = discount_obj["currency"]

    amount = prices.Money(Decimal(discount_obj["amount_value"]), currency)

    old_amount = None
    old_amount_value = discount_obj.get("old_amount_value")
    if old_amount_value:
        old_amount = prices.Money(Decimal(old_amount_value), currency)

    return OrderEventDiscountObject(
        value=discount_obj.get("value"),
        amount=amount,
        value_type=discount_obj.get("value_type"),
        reason=discount_obj.get("reason"),
        old_value_type=discount_obj.get("old_value_type"),
        old_value=discount_obj.get("old_value"),
        old_amount=old_amount,
    )


class OrderDiscount(graphene.ObjectType):
    value_type = graphene.Field(
        DiscountValueTypeEnum,
        required=True,
        description="Type of the discount: fixed or percent.",
    )
    value = PositiveDecimal(
        required=True,
        description="Value of the discount. Can store fixed value or percent value.",
    )
    reason = graphene.String(
        required=False, description="Explanation for the applied discount."
    )
    amount = graphene.Field(Money, description="Returns amount of discount.")


class OrderEventDiscountObject(OrderDiscount):
    old_value_type = graphene.Field(
        DiscountValueTypeEnum,
        required=False,
        description="Type of the discount: fixed or percent.",
    )
    old_value = PositiveDecimal(
        required=False,
        description="Value of the discount. Can store fixed value or percent value.",
    )
    old_amount = graphene.Field(
        Money, required=False, description="Returns amount of discount."
    )


class OrderEventOrderLineObject(graphene.ObjectType):
    quantity = graphene.Int(description="The variant quantity.")
    order_line = graphene.Field(lambda: OrderLine, description="The order line.")
    item_name = graphene.String(description="The variant name.")
    discount = graphene.Field(
        OrderEventDiscountObject, description="The discount applied to the order line."
    )


class OrderEvent(CountableDjangoObjectType):
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = OrderEventsEnum(description="Order event type.")
    user = graphene.Field(User, description="User who performed the action.")
    app = graphene.Field(App, description="App that performed the action.")
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
    invoice_number = graphene.String(
        description="Number of an invoice related to the order."
    )
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
    transaction_reference = graphene.String(
        description="The transaction reference of captured payment."
    )
    shipping_costs_included = graphene.Boolean(
        description="Define if shipping costs were included to the refund."
    )
    related_order = graphene.Field(
        lambda: Order, description="The order which is related to this order."
    )
    discount = graphene.Field(
        OrderEventDiscountObject, description="The discount applied to the order."
    )

    class Meta:
        description = "History log of the order."
        model = models.OrderEvent
        interfaces = [relay.Node]
        only_fields = ["id"]

    @staticmethod
    def resolve_user(root: models.OrderEvent, info):
        def _resolve_user(event_user):
            requester = get_user_or_app_from_context(info.context)
            if (
                requester == event_user
                or requester.has_perm(AccountPermissions.MANAGE_USERS)
                or requester.has_perm(AccountPermissions.MANAGE_STAFF)
            ):
                return event_user
            return None

        if not root.user_id:
            return None

        return UserByUserIdLoader(info.context).load(root.user_id).then(_resolve_user)

    @staticmethod
    def resolve_app(root: models.OrderEvent, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(requestor, root.user, AppPermission.MANAGE_APPS):
            return (
                AppByIdLoader(info.context).load(root.app_id) if root.app_id else None
            )
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
    def resolve_invoice_number(root: models.OrderEvent, _info):
        return root.parameters.get("invoice_number")

    @staticmethod
    @traced_resolver
    def resolve_lines(root: models.OrderEvent, info):
        raw_lines = root.parameters.get("lines", None)

        if not raw_lines:
            return None

        line_pks = []
        for entry in raw_lines:
            line_pk = entry.get("line_pk", None)
            if line_pk:
                line_pks.append(line_pk)

        def _resolve_lines(lines):
            results = []
            lines_dict = {line.pk: line for line in lines if line}
            for raw_line in raw_lines:
                line_pk = raw_line.get("line_pk")
                line_object = lines_dict.get(line_pk)
                discount = raw_line.get("discount")
                if discount:
                    discount = get_order_discount_event(discount)
                results.append(
                    OrderEventOrderLineObject(
                        quantity=raw_line["quantity"],
                        order_line=line_object,
                        item_name=raw_line["item"],
                        discount=discount,
                    )
                )

            return results

        return (
            OrderLineByIdLoader(info.context).load_many(line_pks).then(_resolve_lines)
        )

    @staticmethod
    def resolve_fulfilled_items(root: models.OrderEvent, info):
        fulfillment_lines_ids = root.parameters.get("fulfilled_items", [])

        if not fulfillment_lines_ids:
            return None

        return FulfillmentLinesByIdLoader(info.context).load_many(fulfillment_lines_ids)

    @staticmethod
    def resolve_warehouse(root: models.OrderEvent, info):
        if warehouse_pk := root.parameters.get("warehouse"):
            return WarehouseByIdLoader(info.context).load(warehouse_pk)
        return None

    @staticmethod
    def resolve_transaction_reference(root: models.OrderEvent, _info):
        return root.parameters.get("transaction_reference")

    @staticmethod
    def resolve_shipping_costs_included(root: models.OrderEvent, _info):
        return root.parameters.get("shipping_costs_included")

    @staticmethod
    def resolve_related_order(root: models.OrderEvent, info):
        order_pk = root.parameters.get("related_order_pk")
        if not order_pk:
            return None
        return OrderByIdLoader(info.context).load(order_pk)

    @staticmethod
    def resolve_discount(root: models.OrderEvent, info):
        discount_obj = root.parameters.get("discount")
        if not discount_obj:
            return None
        return get_order_discount_event(discount_obj)


class FulfillmentLine(CountableDjangoObjectType):
    order_line = graphene.Field(lambda: OrderLine)

    class Meta:
        description = "Represents line of the fulfillment."
        interfaces = [relay.Node]
        model = models.FulfillmentLine
        only_fields = ["id", "quantity"]

    @staticmethod
    def resolve_order_line(root: models.FulfillmentLine, info):
        return OrderLineByIdLoader(info.context).load(root.order_line_id)


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


class OrderLine(CountableDjangoObjectType):
    thumbnail = graphene.Field(
        Image,
        description="The main thumbnail for the ordered product.",
        size=graphene.Argument(graphene.Int, description="Size of thumbnail."),
    )
    unit_price = graphene.Field(
        TaxedMoney,
        description="Price of the single item in the order line.",
        required=True,
    )
    undiscounted_unit_price = graphene.Field(
        TaxedMoney,
        description=(
            "Price of the single item in the order line without applied an order line "
            "discount."
        ),
        required=True,
    )
    unit_discount = graphene.Field(
        Money,
        description="The discount applied to the single order line.",
        required=True,
    )
    unit_discount_value = graphene.Field(
        PositiveDecimal,
        description="Value of the discount. Can store fixed value or percent value",
        required=True,
    )
    total_price = graphene.Field(
        TaxedMoney, description="Price of the order line.", required=True
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
    allocations = graphene.List(
        graphene.NonNull(Allocation),
        description="List of allocations across warehouses.",
    )
    unit_discount_type = graphene.Field(
        DiscountValueTypeEnum,
        description="Type of the discount: fixed or percent",
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
            "unit_discount_reason",
        ]

    @staticmethod
    @traced_resolver
    def resolve_thumbnail(root: models.OrderLine, info, *, size=255):
        if not root.variant_id:
            return None

        def _get_image_from_media(image):
            url = get_product_image_thumbnail(image, size, method="thumbnail")
            alt = image.alt
            return Image(alt=alt, url=info.context.build_absolute_uri(url))

        def _get_first_variant_image(all_medias):
            if image := next(
                (
                    media
                    for media in all_medias
                    if media.type == ProductMediaTypes.IMAGE
                ),
                None,
            ):
                return image

        def _get_first_product_image(images):
            return _get_image_from_media(images[0]) if images else None

        def _resolve_thumbnail(result):
            product, variant_medias = result

            if image := _get_first_variant_image(variant_medias):
                return _get_image_from_media(image)

            # we failed to get image from variant, lets use first from product
            return (
                ProductImageByProductIdLoader(info.context)
                .load(product.id)
                .then(_get_first_product_image)
            )

        variants_product = ProductByVariantIdLoader(info.context).load(root.variant_id)
        variant_medias = MediaByProductVariantIdLoader(info.context).load(
            root.variant_id
        )
        return Promise.all([variants_product, variant_medias]).then(_resolve_thumbnail)

    @staticmethod
    def resolve_unit_price(root: models.OrderLine, _info):
        return root.unit_price

    @staticmethod
    def resolve_undiscounted_unit_price(root: models.OrderLine, _info):
        return root.undiscounted_unit_price

    @staticmethod
    def resolve_unit_discount_type(root: models.OrderLine, _info):
        return root.unit_discount_type

    @staticmethod
    def resolve_unit_discount_value(root: models.OrderLine, _info):
        return root.unit_discount_value

    @staticmethod
    def resolve_unit_discount(root: models.OrderLine, _info):
        return root.unit_discount

    @staticmethod
    def resolve_total_price(root: models.OrderLine, _info):
        return root.total_price

    @staticmethod
    def resolve_translated_product_name(root: models.OrderLine, _info):
        return root.translated_product_name

    @staticmethod
    def resolve_translated_variant_name(root: models.OrderLine, _info):
        return root.translated_variant_name

    @staticmethod
    @traced_resolver
    def resolve_variant(root: models.OrderLine, info):
        context = info.context
        if not root.variant_id:
            return None

        def requestor_has_access_to_variant(data):
            variant, channel = data

            requester = get_user_or_app_from_context(context)
            is_staff = requestor_is_staff_member_or_app(requester)
            if is_staff:
                return ChannelContext(node=variant, channel_slug=channel.slug)

            def product_is_available(product_channel_listing):
                if product_channel_listing and product_channel_listing.is_visible:
                    return ChannelContext(node=variant, channel_slug=channel.slug)
                return None

            return (
                ProductChannelListingByProductIdAndChannelSlugLoader(context)
                .load((variant.product_id, channel.slug))
                .then(product_is_available)
            )

        variant = ProductVariantByIdLoader(context).load(root.variant_id)
        channel = ChannelByOrderLineIdLoader(context).load(root.id)

        return Promise.all([variant, channel]).then(requestor_has_access_to_variant)

    @staticmethod
    @one_of_permissions_required(
        [ProductPermissions.MANAGE_PRODUCTS, OrderPermissions.MANAGE_ORDERS]
    )
    def resolve_allocations(root: models.OrderLine, info):
        return AllocationsByOrderLineIdLoader(info.context).load(root.id)


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
    invoices = graphene.List(
        Invoice, required=False, description="List of order invoices."
    )
    number = graphene.String(description="User-friendly number of an order.")
    original = graphene.ID(
        description="The ID of the order that was the base for this order."
    )
    origin = OrderOriginEnum(description="The order origin.", required=True)
    is_paid = graphene.Boolean(
        description="Informs if an order is fully paid.", required=True
    )
    payment_status = PaymentChargeStatusEnum(
        description="Internal payment status.", required=True
    )
    payment_status_display = graphene.String(
        description="User-friendly payment status.", required=True
    )
    payments = graphene.List(Payment, description="List of payments for the order.")
    total = graphene.Field(
        TaxedMoney, description="Total amount of the order.", required=True
    )
    undiscounted_total = graphene.Field(
        TaxedMoney, description="Undiscounted total amount of the order.", required=True
    )
    shipping_price = graphene.Field(
        TaxedMoney, description="Total price of shipping.", required=True
    )
    subtotal = graphene.Field(
        TaxedMoney,
        description="The sum of line prices not including shipping.",
        required=True,
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
        Money, description="Amount authorized for the order.", required=True
    )
    total_captured = graphene.Field(
        Money, description="Amount captured by payment.", required=True
    )
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
    language_code = graphene.String(
        deprecation_reason=(
            "Use the `languageCodeEnum` field to fetch the language code. "
            "This field will be removed in Saleor 4.0."
        ),
        required=True,
    )
    language_code_enum = graphene.Field(
        LanguageCodeEnum, description="Order language code.", required=True
    )
    discount = graphene.Field(
        Money,
        description="Returns applied discount.",
        deprecation_reason=(
            "Use discounts field. This field will be removed in Saleor 4.0."
        ),
    )
    discount_name = graphene.String(
        description="Discount name.",
        deprecation_reason=(
            "Use discounts field. This field will be removed in Saleor 4.0."
        ),
    )

    translated_discount_name = graphene.String(
        description="Translated discount name.",
        deprecation_reason=(
            "Use discounts field. This field will be removed in Saleor 4.0."
        ),
    )

    discounts = graphene.List(
        graphene.NonNull("saleor.graphql.discount.types.OrderDiscount"),
        description="List of all discounts assigned to the order.",
        required=False,
    )
    errors = graphene.List(
        graphene.NonNull(OrderError),
        description="List of errors that occurred during order validation.",
        default_value=[],
        required=True,
    )

    class Meta:
        description = "Represents an order in the shop."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Order
        only_fields = [
            "billing_address",
            "created",
            "customer_note",
            "channel",
            "discount",
            "discount_name",
            "display_gross_prices",
            "gift_cards",
            "id",
            "shipping_address",
            "shipping_method",
            "shipping_method_name",
            "shipping_price",
            "shipping_tax_rate",
            "status",
            "token",
            "tracking_client_id",
            "translated_discount_name",
            "user",
            "voucher",
            "weight",
            "redirect_url",
        ]

    @staticmethod
    def resolve_discounts(root: models.Order, info):
        return OrderDiscountsByOrderIDLoader(info.context).load(root.id)

    @staticmethod
    @traced_resolver
    def resolve_discount(root: models.Order, info):
        def return_voucher_discount(discounts) -> Optional[Money]:
            if not discounts:
                return None
            for discount in discounts:
                if discount.type == OrderDiscountType.VOUCHER:
                    return Money(amount=discount.value, currency=discount.currency)
            return None

        return (
            OrderDiscountsByOrderIDLoader(info.context)
            .load(root.id)
            .then(return_voucher_discount)
        )

    @staticmethod
    @traced_resolver
    def resolve_discount_name(root: models.Order, info):
        def return_voucher_name(discounts) -> Optional[Money]:
            if not discounts:
                return None
            for discount in discounts:
                if discount.type == OrderDiscountType.VOUCHER:
                    return discount.name
            return None

        return (
            OrderDiscountsByOrderIDLoader(info.context)
            .load(root.id)
            .then(return_voucher_name)
        )

    @staticmethod
    @traced_resolver
    def resolve_translated_discount_name(root: models.Order, info):
        def return_voucher_translated_name(discounts) -> Optional[Money]:
            if not discounts:
                return None
            for discount in discounts:
                if discount.type == OrderDiscountType.VOUCHER:
                    return discount.translated_name
            return None

        return (
            OrderDiscountsByOrderIDLoader(info.context)
            .load(root.id)
            .then(return_voucher_translated_name)
        )

    @staticmethod
    @traced_resolver
    def resolve_billing_address(root: models.Order, info):
        def _resolve_billing_address(data):
            if isinstance(data, Address):
                user = None
                address = data
            else:
                user, address = data

            requester = get_user_or_app_from_context(info.context)
            if requestor_has_access(requester, user, OrderPermissions.MANAGE_ORDERS):
                return address
            return obfuscate_address(address)

        if not root.billing_address_id:
            return

        if root.user_id:
            user = UserByUserIdLoader(info.context).load(root.user_id)
            address = AddressByIdLoader(info.context).load(root.billing_address_id)
            return Promise.all([user, address]).then(_resolve_billing_address)
        return (
            AddressByIdLoader(info.context)
            .load(root.billing_address_id)
            .then(_resolve_billing_address)
        )

    @staticmethod
    @traced_resolver
    def resolve_shipping_address(root: models.Order, info):
        def _resolve_shipping_address(data):
            if isinstance(data, Address):
                user = None
                address = data
            else:
                user, address = data
            requester = get_user_or_app_from_context(info.context)
            if requestor_has_access(requester, user, OrderPermissions.MANAGE_ORDERS):
                return address
            return obfuscate_address(address)

        if not root.shipping_address_id:
            return

        if root.user_id:
            user = UserByUserIdLoader(info.context).load(root.user_id)
            address = AddressByIdLoader(info.context).load(root.shipping_address_id)
            return Promise.all([user, address]).then(_resolve_shipping_address)
        return (
            AddressByIdLoader(info.context)
            .load(root.shipping_address_id)
            .then(_resolve_shipping_address)
        )

    @staticmethod
    def resolve_shipping_price(root: models.Order, _info):
        return root.shipping_price

    @staticmethod
    def resolve_actions(root: models.Order, info):
        def _resolve_actions(payments):
            actions = []
            payment = get_last_payment(payments)
            if root.can_capture(payment):
                actions.append(OrderAction.CAPTURE)
            if root.can_mark_as_paid(payments):
                actions.append(OrderAction.MARK_AS_PAID)
            if root.can_refund(payment):
                actions.append(OrderAction.REFUND)
            if root.can_void(payment):
                actions.append(OrderAction.VOID)
            return actions

        return (
            PaymentsByOrderIdLoader(info.context).load(root.id).then(_resolve_actions)
        )

    @staticmethod
    @traced_resolver
    def resolve_subtotal(root: models.Order, info):
        def _resolve_subtotal(order_lines):
            return get_subtotal(order_lines, root.currency)

        return (
            OrderLinesByOrderIdLoader(info.context)
            .load(root.id)
            .then(_resolve_subtotal)
        )

    @staticmethod
    def resolve_total(root: models.Order, _info):
        return root.total

    @staticmethod
    def resolve_undiscounted_total(root: models.Order, _info):
        return root.undiscounted_total

    @staticmethod
    def resolve_total_authorized(root: models.Order, info):
        def _resolve_total_get_total_authorized(payments):
            return get_total_authorized(payments, root.currency)

        return (
            PaymentsByOrderIdLoader(info.context)
            .load(root.id)
            .then(_resolve_total_get_total_authorized)
        )

    @staticmethod
    def resolve_total_captured(root: models.Order, info):
        return root.total_paid

    @staticmethod
    def resolve_total_balance(root: models.Order, _info):
        return root.total_balance

    @staticmethod
    def resolve_fulfillments(root: models.Order, info):
        def _resolve_fulfillments(fulfillments):
            user = info.context.user
            if user.is_staff:
                return fulfillments
            return filter(
                lambda fulfillment: fulfillment.status != FulfillmentStatus.CANCELED,
                fulfillments,
            )

        return (
            FulfillmentsByOrderIdLoader(info.context)
            .load(root.id)
            .then(_resolve_fulfillments)
        )

    @staticmethod
    def resolve_lines(root: models.Order, info):
        return OrderLinesByOrderIdLoader(info.context).load(root.id)

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_events(root: models.Order, _info):
        return OrderEventsByOrderIdLoader(_info.context).load(root.id)

    @staticmethod
    def resolve_is_paid(root: models.Order, _info):
        return root.is_fully_paid()

    @staticmethod
    def resolve_number(root: models.Order, _info):
        return str(root.pk)

    @staticmethod
    @traced_resolver
    def resolve_payment_status(root: models.Order, info):
        def _resolve_payment_status(payments):
            if last_payment := max(payments, default=None, key=attrgetter("pk")):
                return last_payment.charge_status
            return ChargeStatus.NOT_CHARGED

        return (
            PaymentsByOrderIdLoader(info.context)
            .load(root.id)
            .then(_resolve_payment_status)
        )

    @staticmethod
    def resolve_payment_status_display(root: models.Order, info):
        def _resolve_payment_status(payments):
            if last_payment := max(payments, default=None, key=attrgetter("pk")):
                return last_payment.get_charge_status_display()
            return dict(ChargeStatus.CHOICES).get(ChargeStatus.NOT_CHARGED)

        return (
            PaymentsByOrderIdLoader(info.context)
            .load(root.id)
            .then(_resolve_payment_status)
        )

    @staticmethod
    def resolve_payments(root: models.Order, _info):
        return root.payments.all()

    @staticmethod
    def resolve_status_display(root: models.Order, _info):
        return root.get_status_display()

    @staticmethod
    @traced_resolver
    def resolve_can_finalize(root: models.Order, _info):
        if root.status == OrderStatus.DRAFT:
            country = get_order_country(root)
            try:
                validate_draft_order(root, country)
            except ValidationError:
                return False
        return True

    @staticmethod
    def resolve_user_email(root: models.Order, info):
        def _resolve_user_email(user):
            requester = get_user_or_app_from_context(info.context)
            if requestor_has_access(requester, user, OrderPermissions.MANAGE_ORDERS):
                return user.email if user else root.user_email
            return obfuscate_email(user.email if user else root.user_email)

        if not root.user_id:
            return _resolve_user_email(None)

        return (
            UserByUserIdLoader(info.context)
            .load(root.user_id)
            .then(_resolve_user_email)
        )

    @staticmethod
    def resolve_user(root: models.Order, info):
        def _resolve_user(user):
            requester = get_user_or_app_from_context(info.context)
            if requestor_has_access(requester, user, AccountPermissions.MANAGE_USERS):
                return user
            raise PermissionDenied()

        if not root.user_id:
            return None

        return UserByUserIdLoader(info.context).load(root.user_id).then(_resolve_user)

    @staticmethod
    def resolve_shipping_method(root: models.Order, info):
        if not root.shipping_method_id:
            return None

        def wrap_shipping_method_with_channel_context(data):
            shipping_method, channel = data
            return ChannelContext(node=shipping_method, channel_slug=channel.slug)

        shipping_method = ShippingMethodByIdLoader(info.context).load(
            root.shipping_method_id
        )
        channel = ChannelByIdLoader(info.context).load(root.channel_id)

        return Promise.all([shipping_method, channel]).then(
            wrap_shipping_method_with_channel_context
        )

    @staticmethod
    @traced_resolver
    # TODO: We should optimize it in/after PR#5819
    def resolve_available_shipping_methods(root: models.Order, info):
        available = get_valid_shipping_methods_for_order(root)
        if available is None:
            return []
        available_shipping_methods = []
        manager = info.context.plugins
        display_gross = display_gross_prices()
        channel_slug = root.channel.slug
        for shipping_method in available:
            # Ignore typing check because it is checked in
            # get_valid_shipping_methods_for_order
            shipping_channel_listing = shipping_method.channel_listings.filter(
                channel=root.channel
            ).first()
            if shipping_channel_listing:
                taxed_price = manager.apply_taxes_to_shipping(
                    shipping_channel_listing.price,
                    root.shipping_address,  # type: ignore
                    channel_slug,
                )
                if display_gross:
                    shipping_method.price = taxed_price.gross
                else:
                    shipping_method.price = taxed_price.net
                available_shipping_methods.append(shipping_method)
        instances = [
            ChannelContext(node=shipping, channel_slug=channel_slug)
            for shipping in available_shipping_methods
        ]

        return instances

    @staticmethod
    def resolve_invoices(root: models.Order, info):
        requester = get_user_or_app_from_context(info.context)
        if requestor_has_access(requester, root.user, OrderPermissions.MANAGE_ORDERS):
            return root.invoices.all()
        raise PermissionDenied()

    @staticmethod
    def resolve_is_shipping_required(root: models.Order, _info):
        return root.is_shipping_required()

    @staticmethod
    def resolve_gift_cards(root: models.Order, _info):
        return root.gift_cards.all()

    @staticmethod
    def resolve_voucher(root: models.Order, info):
        if not root.voucher_id:
            return None

        def wrap_voucher_with_channel_context(data):
            voucher, channel = data
            return ChannelContext(node=voucher, channel_slug=channel.slug)

        voucher = VoucherByIdLoader(info.context).load(root.voucher_id)
        channel = ChannelByIdLoader(info.context).load(root.channel_id)

        return Promise.all([voucher, channel]).then(wrap_voucher_with_channel_context)

    @staticmethod
    def resolve_language_code_enum(root, _info, **_kwargs):
        return LanguageCodeEnum[str_to_enum(root.language_code)]

    @staticmethod
    def resolve_original(root, info, **_kwargs):
        if not root.original_id:
            return None
        return graphene.Node.to_global_id("Order", root.original_id)

    @traced_resolver
    def resolve_errors(root, _info, **_kwargs):
        if root.status == OrderStatus.DRAFT:
            country = get_order_country(root)
            try:
                validate_draft_order(root, country)
            except ValidationError as e:
                return validation_error_to_error_type(e, OrderError)
        return []
