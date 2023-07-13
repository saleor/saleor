import logging
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

import graphene
import prices
from django.core.exceptions import ValidationError
from graphene import relay
from promise import Promise

from ...account.models import Address
from ...account.models import User as UserModel
from ...checkout.utils import get_external_shipping_id
from ...core.anonymize import obfuscate_address, obfuscate_email
from ...core.prices import quantize_price
from ...core.taxes import zero_money
from ...discount import DiscountType
from ...graphql.checkout.types import DeliveryMethod
from ...graphql.core.federation.entities import federated_entity
from ...graphql.core.federation.resolvers import resolve_federation_references
from ...graphql.order.resolvers import resolve_orders
from ...graphql.utils import get_user_or_app_from_context
from ...graphql.warehouse.dataloaders import StockByIdLoader, WarehouseByIdLoader
from ...order import OrderStatus, calculations, models
from ...order.models import FulfillmentStatus
from ...order.utils import (
    get_order_country,
    get_valid_collection_points_for_order,
    get_valid_shipping_methods_for_order,
)
from ...payment import ChargeStatus, TransactionKind
from ...payment.dataloaders import PaymentsByOrderIdLoader
from ...payment.model_helpers import get_last_payment, get_total_authorized
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import (
    AccountPermissions,
    AppPermission,
    OrderPermissions,
    PaymentPermissions,
    ProductPermissions,
)
from ...permission.utils import has_one_of_permissions
from ...product import ProductMediaTypes
from ...product.models import ALL_PRODUCTS_PERMISSIONS
from ...shipping.interface import ShippingMethodData
from ...shipping.models import ShippingMethodChannelListing
from ...shipping.utils import convert_to_shipping_method_data
from ...tax.utils import get_display_gross_prices
from ...thumbnail.utils import (
    get_image_or_proxy_url,
    get_thumbnail_format,
    get_thumbnail_size,
)
from ..account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ..account.types import User
from ..account.utils import (
    check_is_owner_or_has_one_of_perms,
    is_owner_or_has_one_of_perms,
)
from ..app.dataloaders import AppByIdLoader
from ..app.types import App
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByIdLoader, ChannelByOrderLineIdLoader
from ..channel.types import Channel
from ..checkout.utils import prevent_sync_event_circular_query
from ..core.connection import CountableConnection
from ..core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    ADDED_IN_35,
    ADDED_IN_38,
    ADDED_IN_39,
    ADDED_IN_310,
    ADDED_IN_311,
    ADDED_IN_313,
    ADDED_IN_315,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.enums import LanguageCodeEnum
from ..core.fields import PermissionsField
from ..core.mutations import validation_error_to_error_type
from ..core.scalars import PositiveDecimal
from ..core.tracing import traced_resolver
from ..core.types import (
    BaseObjectType,
    Image,
    ModelObjectType,
    Money,
    NonNullList,
    OrderError,
    TaxedMoney,
    ThumbnailField,
    Weight,
)
from ..core.utils import str_to_enum
from ..decorators import one_of_permissions_required
from ..discount.dataloaders import OrderDiscountsByOrderIDLoader, VoucherByIdLoader
from ..discount.enums import DiscountValueTypeEnum
from ..discount.types import Voucher
from ..giftcard.dataloaders import GiftCardsByOrderIdLoader
from ..giftcard.types import GiftCard
from ..invoice.dataloaders import InvoicesByOrderIdLoader
from ..invoice.types import Invoice
from ..meta.resolvers import check_private_metadata_privilege, resolve_metadata
from ..meta.types import MetadataItem, ObjectWithMetadata
from ..payment.dataloaders import TransactionByPaymentIdLoader
from ..payment.enums import OrderAction
from ..payment.types import Payment, PaymentChargeStatusEnum, TransactionItem
from ..plugins.dataloaders import (
    get_plugin_manager_promise,
    plugin_manager_promise_callback,
)
from ..product.dataloaders import (
    ImagesByProductIdLoader,
    MediaByProductVariantIdLoader,
    ProductByVariantIdLoader,
    ProductChannelListingByProductIdAndChannelSlugLoader,
    ProductVariantByIdLoader,
    ThumbnailByProductMediaIdSizeAndFormatLoader,
)
from ..product.types import DigitalContentUrl, ProductVariant
from ..shipping.dataloaders import (
    ShippingMethodByIdLoader,
    ShippingMethodChannelListingByChannelSlugLoader,
    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader,
)
from ..shipping.types import ShippingMethod
from ..tax.dataloaders import (
    TaxClassByIdLoader,
    TaxConfigurationByChannelId,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)
from ..tax.types import TaxClass
from ..warehouse.types import Allocation, Stock, Warehouse
from .dataloaders import (
    AllocationsByOrderLineIdLoader,
    FulfillmentLinesByFulfillmentIdLoader,
    FulfillmentLinesByIdLoader,
    FulfillmentsByOrderIdLoader,
    OrderByIdLoader,
    OrderByNumberLoader,
    OrderEventsByIdLoader,
    OrderEventsByOrderIdLoader,
    OrderGrantedRefundLinesByOrderGrantedRefundIdLoader,
    OrderGrantedRefundsByOrderIdLoader,
    OrderLineByIdLoader,
    OrderLinesByOrderIdLoader,
    TransactionItemsByOrderIDLoader,
)
from .enums import (
    FulfillmentStatusEnum,
    OrderAuthorizeStatusEnum,
    OrderChargeStatusEnum,
    OrderEventsEmailsEnum,
    OrderEventsEnum,
    OrderOriginEnum,
    OrderStatusEnum,
)
from .utils import validate_draft_order

logger = logging.getLogger(__name__)


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


def get_payment_status_for_order(order):
    status = ChargeStatus.NOT_CHARGED
    charged_money = order.total_charged

    if charged_money >= order.total.gross:
        status = ChargeStatus.FULLY_CHARGED
    elif charged_money and charged_money < order.total.gross:
        status = ChargeStatus.PARTIALLY_CHARGED
    return status


class OrderGrantedRefundLine(ModelObjectType[models.OrderGrantedRefundLine]):
    id = graphene.GlobalID(required=True)
    quantity = graphene.Int(description="Number of items to refund.", required=True)
    order_line = graphene.Field(
        "saleor.graphql.order.types.OrderLine",
        description="Line of the order associated with this granted refund.",
        required=True,
    )
    reason = graphene.String(description="Reason for refunding the line.")

    class Meta:
        description = "Represents granted refund line." + ADDED_IN_315 + PREVIEW_FEATURE
        model = models.OrderGrantedRefundLine

    @staticmethod
    def resolve_order_line(root: models.OrderGrantedRefundLine, info):
        return OrderLineByIdLoader(info.context).load(root.order_line_id)


class OrderGrantedRefund(ModelObjectType[models.OrderGrantedRefund]):
    id = graphene.GlobalID(required=True)
    created_at = graphene.DateTime(required=True, description="Time of creation.")
    updated_at = graphene.DateTime(required=True, description="Time of last update.")
    amount = graphene.Field(Money, required=True, description="Refund amount.")
    reason = graphene.String(description="Reason of the refund.")
    user = graphene.Field(
        User,
        description=(
            "User who performed the action. Requires of of the following "
            f"permissions: {AccountPermissions.MANAGE_USERS.name}, "
            f"{AccountPermissions.MANAGE_STAFF.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    app = graphene.Field(App, description=("App that performed the action."))
    shipping_costs_included = graphene.Boolean(
        required=True,
        description=(
            "If true, the refunded amount includes the shipping price."
            "If false, the refunded amount does not include the shipping price."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        ),
    )
    lines = NonNullList(
        OrderGrantedRefundLine,
        description="Lines assigned to the granted refund."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
    )

    class Meta:
        description = "The details of granted refund." + ADDED_IN_313 + PREVIEW_FEATURE
        model = models.OrderGrantedRefund

    @staticmethod
    def resolve_user(root: models.OrderGrantedRefund, info):
        def _resolve_user(event_user: UserModel):
            requester = get_user_or_app_from_context(info.context)
            if not requester:
                return None
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
    def resolve_app(root: models.OrderGrantedRefund, info):
        if root.app_id:
            return AppByIdLoader(info.context).load(root.app_id)
        return None

    @staticmethod
    def resolve_lines(root: models.OrderGrantedRefund, info):
        return OrderGrantedRefundLinesByOrderGrantedRefundIdLoader(info.context).load(
            root.id
        )


class OrderDiscount(BaseObjectType):
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

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


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

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderEventOrderLineObject(BaseObjectType):
    quantity = graphene.Int(description="The variant quantity.")
    order_line = graphene.Field(lambda: OrderLine, description="The order line.")
    item_name = graphene.String(description="The variant name.")
    discount = graphene.Field(
        OrderEventDiscountObject, description="The discount applied to the order line."
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderEvent(ModelObjectType[models.OrderEvent]):
    id = graphene.GlobalID(required=True)
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = OrderEventsEnum(description="Order event type.")
    user = graphene.Field(User, description="User who performed the action.")
    app = graphene.Field(
        App,
        description=(
            "App that performed the action. Requires of of the following permissions: "
            f"{AppPermission.MANAGE_APPS.name}, {OrderPermissions.MANAGE_ORDERS.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    message = graphene.String(description="Content of the event.")
    email = graphene.String(description="Email of the customer.")
    email_type = OrderEventsEmailsEnum(
        description="Type of an email sent to the customer."
    )
    amount = graphene.Float(description="Amount of money.")
    payment_id = graphene.String(
        description="The payment reference from the payment provider."
    )
    payment_gateway = graphene.String(description="The payment gateway of the payment.")
    quantity = graphene.Int(description="Number of items.")
    composed_id = graphene.String(description="Composed ID of the Fulfillment.")
    order_number = graphene.String(description="User-friendly number of an order.")
    invoice_number = graphene.String(
        description="Number of an invoice related to the order."
    )
    oversold_items = NonNullList(
        graphene.String, description="List of oversold lines names."
    )
    lines = NonNullList(OrderEventOrderLineObject, description="The concerned lines.")
    fulfilled_items = NonNullList(
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
    related = graphene.Field(
        lambda: OrderEvent,
        description="The order event which is related to this event."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
    )
    discount = graphene.Field(
        OrderEventDiscountObject, description="The discount applied to the order."
    )
    reference = graphene.String(description="The reference of payment's transaction.")

    class Meta:
        description = "History log of the order."
        model = models.OrderEvent
        interfaces = [relay.Node]

    @staticmethod
    def resolve_user(root: models.OrderEvent, info):
        user_or_app = get_user_or_app_from_context(info.context)
        if not user_or_app:
            return None
        requester = user_or_app

        def _resolve_user(event_user):
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
        check_is_owner_or_has_one_of_perms(
            requestor,
            root.user,
            AppPermission.MANAGE_APPS,
            OrderPermissions.MANAGE_ORDERS,
        )
        return AppByIdLoader(info.context).load(root.app_id) if root.app_id else None

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
    def resolve_order_number(root: models.OrderEvent, info):
        def _resolve_order_number(order: models.Order):
            return order.number

        return (
            OrderByIdLoader(info.context)
            .load(root.order_id)
            .then(_resolve_order_number)
        )

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
                line_pks.append(UUID(line_pk))

        def _resolve_lines(lines):
            results = []
            lines_dict = {str(line.pk): line for line in lines if line}
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
            return WarehouseByIdLoader(info.context).load(UUID(warehouse_pk))
        return None

    @staticmethod
    def resolve_transaction_reference(root: models.OrderEvent, _info):
        return root.parameters.get("transaction_reference")

    @staticmethod
    def resolve_shipping_costs_included(root: models.OrderEvent, _info):
        return root.parameters.get("shipping_costs_included")

    @staticmethod
    def resolve_related_order(root: models.OrderEvent, info):
        order_pk_or_number = root.parameters.get("related_order_pk")
        if not order_pk_or_number:
            return None

        try:
            # Orders that primary_key are not uuid are old int `id's`.
            # In migration `order_0128`, before migrating old `id's` to uuid,
            # old `id's` were saved to field `number`.
            order_pk = UUID(order_pk_or_number)
        except (AttributeError, ValueError):
            return OrderByNumberLoader(info.context).load(order_pk_or_number)

        return OrderByIdLoader(info.context).load(order_pk)

    @staticmethod
    def resolve_related(root: models.OrderEvent, info):
        if not root.related_id:
            return None
        return OrderEventsByIdLoader(info.context).load(root.related_id)

    @staticmethod
    def resolve_discount(root: models.OrderEvent, info):
        discount_obj = root.parameters.get("discount")
        if not discount_obj:
            return None
        return get_order_discount_event(discount_obj)

    @staticmethod
    def resolve_status(root: models.OrderEvent, _info):
        return root.parameters.get("status")

    @staticmethod
    def resolve_reference(root: models.OrderEvent, _info):
        return root.parameters.get("reference")


class OrderEventCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        node = OrderEvent


class FulfillmentLine(ModelObjectType[models.FulfillmentLine]):
    id = graphene.GlobalID(required=True)
    quantity = graphene.Int(required=True)
    order_line = graphene.Field(lambda: OrderLine)

    class Meta:
        description = "Represents line of the fulfillment."
        interfaces = [relay.Node]
        model = models.FulfillmentLine

    @staticmethod
    def resolve_order_line(root: models.FulfillmentLine, info):
        return OrderLineByIdLoader(info.context).load(root.order_line_id)


class Fulfillment(ModelObjectType[models.Fulfillment]):
    id = graphene.GlobalID(required=True)
    fulfillment_order = graphene.Int(required=True)
    status = FulfillmentStatusEnum(required=True)
    tracking_number = graphene.String(required=True)
    created = graphene.DateTime(required=True)
    lines = NonNullList(
        FulfillmentLine, description="List of lines for the fulfillment."
    )
    status_display = graphene.String(description="User-friendly fulfillment status.")
    warehouse = graphene.Field(
        Warehouse,
        required=False,
        description="Warehouse from fulfillment was fulfilled.",
    )

    class Meta:
        description = "Represents order fulfillment."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Fulfillment

    @staticmethod
    def resolve_created(root: models.Fulfillment, _info):
        return root.created_at

    @staticmethod
    def resolve_lines(root: models.Fulfillment, info):
        return FulfillmentLinesByFulfillmentIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_status_display(root: models.Fulfillment, _info):
        return root.get_status_display()

    @staticmethod
    def resolve_warehouse(root: models.Fulfillment, info):
        def _resolve_stock_warehouse(stock: Stock):
            return WarehouseByIdLoader(info.context).load(stock.warehouse_id)

        def _resolve_stock(fulfillment_lines: List[models.FulfillmentLine]):
            try:
                line = fulfillment_lines[0]
            except IndexError:
                return None

            if stock_id := line.stock_id:
                return (
                    StockByIdLoader(info.context)
                    .load(stock_id)
                    .then(_resolve_stock_warehouse)
                )

        return (
            FulfillmentLinesByFulfillmentIdLoader(info.context)
            .load(root.id)
            .then(_resolve_stock)
        )


class OrderLine(ModelObjectType[models.OrderLine]):
    id = graphene.GlobalID(required=True)
    product_name = graphene.String(required=True)
    variant_name = graphene.String(required=True)
    product_sku = graphene.String()
    product_variant_id = graphene.String()
    is_shipping_required = graphene.Boolean(required=True)
    quantity = graphene.Int(required=True)
    quantity_fulfilled = graphene.Int(required=True)
    unit_discount_reason = graphene.String()
    tax_rate = graphene.Float(required=True)
    digital_content_url = graphene.Field(DigitalContentUrl)
    thumbnail = ThumbnailField()
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
            "has been removed from stock at all. Requires one of the following "
            "permissions to include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
    )
    translated_product_name = graphene.String(
        required=True, description="Product name in the customer's language"
    )
    translated_variant_name = graphene.String(
        required=True, description="Variant name in the customer's language"
    )
    allocations = PermissionsField(
        NonNullList(Allocation),
        description="List of allocations across warehouses.",
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    quantity_to_fulfill = graphene.Int(
        required=True,
        description="A quantity of items remaining to be fulfilled." + ADDED_IN_31,
    )
    unit_discount_type = graphene.Field(
        DiscountValueTypeEnum,
        description="Type of the discount: fixed or percent",
    )
    tax_class = PermissionsField(
        TaxClass,
        description=(
            "Denormalized tax class of the product in this order line." + ADDED_IN_39
        ),
        required=False,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )
    tax_class_name = graphene.Field(
        graphene.String,
        description="Denormalized name of the tax class." + ADDED_IN_39,
        required=False,
    )
    tax_class_metadata = NonNullList(
        MetadataItem,
        required=True,
        description="Denormalized public metadata of the tax class." + ADDED_IN_39,
    )
    tax_class_private_metadata = NonNullList(
        MetadataItem,
        required=True,
        description=(
            "Denormalized private metadata of the tax class. Requires staff "
            "permissions to access." + ADDED_IN_39
        ),
    )

    class Meta:
        description = "Represents order line of particular order."
        model = models.OrderLine
        interfaces = [relay.Node, ObjectWithMetadata]
        metadata_since = ADDED_IN_35

    @staticmethod
    @traced_resolver
    def resolve_thumbnail(
        root: models.OrderLine, info, *, size: int = 256, format: Optional[str] = None
    ):
        if not root.variant_id:
            return None

        format = get_thumbnail_format(format)
        size = get_thumbnail_size(size)

        def _get_image_from_media(image):
            def _resolve_url(thumbnail):
                url = get_image_or_proxy_url(
                    thumbnail, image.id, "ProductMedia", size, format
                )
                return Image(alt=image.alt, url=url)

            return (
                ThumbnailByProductMediaIdSizeAndFormatLoader(info.context)
                .load((image.id, size, format))
                .then(_resolve_url)
            )

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
                ImagesByProductIdLoader(info.context)
                .load(product.id)
                .then(_get_first_product_image)
            )

        variants_product = ProductByVariantIdLoader(info.context).load(root.variant_id)
        variant_medias = MediaByProductVariantIdLoader(info.context).load(
            root.variant_id
        )
        return Promise.all([variants_product, variant_medias]).then(_resolve_thumbnail)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_unit_price(root: models.OrderLine, info):
        def _resolve_unit_price(data):
            order, lines, manager = data
            return calculations.order_line_unit(
                order, root, manager, lines
            ).price_with_discounts

        order = OrderByIdLoader(info.context).load(root.order_id)
        lines = OrderLinesByOrderIdLoader(info.context).load(root.order_id)
        manager = get_plugin_manager_promise(info.context)
        return Promise.all([order, lines, manager]).then(_resolve_unit_price)

    @staticmethod
    def resolve_quantity_to_fulfill(root: models.OrderLine, info):
        return root.quantity_unfulfilled

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_undiscounted_unit_price(root: models.OrderLine, info):
        def _resolve_undiscounted_unit_price(data):
            order, lines, manager = data
            return calculations.order_line_unit(
                order, root, manager, lines
            ).undiscounted_price

        order = OrderByIdLoader(info.context).load(root.order_id)
        lines = OrderLinesByOrderIdLoader(info.context).load(root.order_id)
        manager = get_plugin_manager_promise(info.context)
        return Promise.all([order, lines, manager]).then(
            _resolve_undiscounted_unit_price
        )

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
    @traced_resolver
    def resolve_tax_rate(root: models.OrderLine, info):
        def _resolve_tax_rate(data):
            order, lines, manager = data
            return calculations.order_line_tax_rate(
                order, root, manager, lines
            ) or Decimal(0)

        order = OrderByIdLoader(info.context).load(root.order_id)
        lines = OrderLinesByOrderIdLoader(info.context).load(root.order_id)
        manager = get_plugin_manager_promise(info.context)
        return Promise.all([order, lines, manager]).then(_resolve_tax_rate)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_total_price(root: models.OrderLine, info):
        def _resolve_total_price(data):
            order, lines, manager = data
            return calculations.order_line_total(
                order, root, manager, lines
            ).price_with_discounts

        order = OrderByIdLoader(info.context).load(root.order_id)
        lines = OrderLinesByOrderIdLoader(info.context).load(root.order_id)
        manager = get_plugin_manager_promise(info.context)
        return Promise.all([order, lines, manager]).then(_resolve_total_price)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_undiscounted_total_price(root: models.OrderLine, info):
        def _resolve_undiscounted_total_price(data):
            order, lines, manager = data
            return calculations.order_line_total(
                order, root, manager, lines
            ).undiscounted_price

        order = OrderByIdLoader(info.context).load(root.order_id)
        lines = OrderLinesByOrderIdLoader(info.context).load(root.order_id)
        manager = get_plugin_manager_promise(info.context)
        return Promise.all([order, lines, manager]).then(
            _resolve_undiscounted_total_price
        )

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
            has_required_permission = has_one_of_permissions(
                requester, ALL_PRODUCTS_PERMISSIONS
            )
            if has_required_permission:
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
    def resolve_allocations(root: models.OrderLine, info):
        return AllocationsByOrderLineIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_tax_class(root: models.OrderLine, info):
        return (
            TaxClassByIdLoader(info.context).load(root.tax_class_id)
            if root.tax_class_id
            else None
        )

    @staticmethod
    def resolve_tax_class_metadata(root: models.OrderLine, _info):
        return resolve_metadata(root.tax_class_metadata)

    @staticmethod
    def resolve_tax_class_private_metadata(root: models.OrderLine, info):
        check_private_metadata_privilege(root, info)
        return resolve_metadata(root.tax_class_private_metadata)


@federated_entity("id")
class Order(ModelObjectType[models.Order]):
    id = graphene.GlobalID(required=True)
    created = graphene.DateTime(required=True)
    updated_at = graphene.DateTime(required=True)
    status = OrderStatusEnum(required=True)
    user = graphene.Field(
        User,
        description=(
            "User who placed the order. This field is set only for orders placed by "
            "authenticated users. Can be fetched for orders created in Saleor 3.2 "
            "and later, for other orders requires one of the following permissions: "
            f"{AccountPermissions.MANAGE_USERS.name}, "
            f"{OrderPermissions.MANAGE_ORDERS.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    tracking_client_id = graphene.String(
        required=True,
        description="Google Analytics tracking client ID. " + DEPRECATED_IN_3X_FIELD,
    )
    billing_address = graphene.Field(
        "saleor.graphql.account.types.Address",
        description=(
            "Billing address. The full data can be access for orders created "
            "in Saleor 3.2 and later, for other orders requires one of the following "
            f"permissions: {OrderPermissions.MANAGE_ORDERS.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    shipping_address = graphene.Field(
        "saleor.graphql.account.types.Address",
        description=(
            "Shipping address. The full data can be access for orders created "
            "in Saleor 3.2 and later, for other orders requires one of the following "
            f"permissions: {OrderPermissions.MANAGE_ORDERS.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
    )
    shipping_method_name = graphene.String()
    collection_point_name = graphene.String()
    channel = graphene.Field(Channel, required=True)
    fulfillments = NonNullList(
        Fulfillment, required=True, description="List of shipments for the order."
    )
    lines = NonNullList(
        lambda: OrderLine, required=True, description="List of order lines."
    )
    actions = NonNullList(
        OrderAction,
        description=(
            "List of actions that can be performed in the current state of an order."
        ),
        required=True,
    )
    available_shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this order.",
        required=False,
        deprecation_reason="Use `shippingMethods`, this field will be removed in 4.0",
    )
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods related to this order.",
        required=True,
    )
    available_collection_points = NonNullList(
        Warehouse,
        description=(
            "Collection points that can be used for this order." + ADDED_IN_31
        ),
        required=True,
    )
    invoices = NonNullList(
        Invoice,
        description=(
            "List of order invoices. Can be fetched for orders created in Saleor 3.2 "
            "and later, for other orders requires one of the following permissions: "
            f"{OrderPermissions.MANAGE_ORDERS.name}, {AuthorizationFilters.OWNER.name}."
        ),
        required=True,
    )
    number = graphene.String(
        description="User-friendly number of an order.", required=True
    )
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
    authorize_status = OrderAuthorizeStatusEnum(
        description=("The authorize status of the order." + ADDED_IN_34),
        required=True,
    )
    charge_status = OrderChargeStatusEnum(
        description=("The charge status of the order." + ADDED_IN_34),
        required=True,
    )
    tax_exemption = graphene.Boolean(
        description=(
            "Returns True if order has to be exempt from taxes." + ADDED_IN_38
        ),
        required=True,
    )
    transactions = NonNullList(
        TransactionItem,
        description=(
            "List of transactions for the order. Requires one of the "
            "following permissions: MANAGE_ORDERS, HANDLE_PAYMENTS." + ADDED_IN_34
        ),
        required=True,
    )
    payments = NonNullList(
        Payment, description="List of payments for the order.", required=True
    )
    total = graphene.Field(
        TaxedMoney, description="Total amount of the order.", required=True
    )
    undiscounted_total = graphene.Field(
        TaxedMoney, description="Undiscounted total amount of the order.", required=True
    )
    shipping_method = graphene.Field(
        ShippingMethod,
        description="Shipping method for this order.",
        deprecation_reason=(f"{DEPRECATED_IN_3X_FIELD} Use `deliveryMethod` instead."),
    )
    shipping_price = graphene.Field(
        TaxedMoney, description="Total price of shipping.", required=True
    )
    shipping_tax_rate = graphene.Float(
        required=True, description="The shipping tax rate value."
    )
    shipping_tax_class = PermissionsField(
        TaxClass,
        description="Denormalized tax class assigned to the shipping method."
        + ADDED_IN_39,
        required=False,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )
    shipping_tax_class_name = graphene.Field(
        graphene.String,
        description=(
            "Denormalized name of the tax class assigned to the shipping method."
            + ADDED_IN_39
        ),
        required=False,
    )
    shipping_tax_class_metadata = NonNullList(
        MetadataItem,
        required=True,
        description=(
            "Denormalized public metadata of the shipping method's tax class."
            + ADDED_IN_39
        ),
    )
    shipping_tax_class_private_metadata = NonNullList(
        MetadataItem,
        required=True,
        description=(
            "Denormalized private metadata of the shipping method's tax class. "
            "Requires staff permissions to access." + ADDED_IN_39
        ),
    )
    token = graphene.String(
        required=True,
        deprecation_reason=(f"{DEPRECATED_IN_3X_FIELD} Use `id` instead."),
    )
    voucher = graphene.Field(Voucher)
    gift_cards = NonNullList(
        GiftCard, description="List of user gift cards.", required=True
    )
    customerNote = graphene.Boolean(required=True)
    customer_note = graphene.String(required=True)
    weight = graphene.Field(Weight, required=True)
    redirect_url = graphene.String()
    subtotal = graphene.Field(
        TaxedMoney,
        description="The sum of line prices not including shipping.",
        required=True,
    )
    status_display = graphene.String(
        description="User-friendly order status.", required=True
    )
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
        Money,
        description="Amount captured for the order. ",
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Use `totalCharged` instead.",
        required=True,
    )
    total_charged = graphene.Field(
        Money, description="Amount charged for the order." + ADDED_IN_313, required=True
    )

    total_canceled = graphene.Field(
        Money,
        description="Amount canceled for the order." + ADDED_IN_313,
        required=True,
    )

    events = PermissionsField(
        NonNullList(OrderEvent),
        description="List of events associated with the order.",
        permissions=[OrderPermissions.MANAGE_ORDERS],
        required=True,
    )
    total_balance = graphene.Field(
        Money,
        description="The difference between the paid and the order total amount.",
        required=True,
    )
    user_email = graphene.String(
        description=(
            "Email address of the customer. The full data can be access for orders "
            "created in Saleor 3.2 and later, for other orders requires one of "
            f"the following permissions: {OrderPermissions.MANAGE_ORDERS.name}, "
            f"{AuthorizationFilters.OWNER.name}."
        ),
        required=False,
    )
    is_shipping_required = graphene.Boolean(
        description="Returns True, if order requires shipping.", required=True
    )
    delivery_method = graphene.Field(
        DeliveryMethod,
        description=("The delivery method selected for this order." + ADDED_IN_31),
    )
    language_code = graphene.String(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `languageCodeEnum` field to fetch the language code. "
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
            f"{DEPRECATED_IN_3X_FIELD} Use the `discounts` field instead."
        ),
    )
    discount_name = graphene.String(
        description="Discount name.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `discounts` field instead."
        ),
    )
    translated_discount_name = graphene.String(
        description="Translated discount name.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `discounts` field instead. "
        ),
    )
    discounts = NonNullList(
        "saleor.graphql.discount.types.OrderDiscount",
        description="List of all discounts assigned to the order.",
        required=True,
    )
    errors = NonNullList(
        OrderError,
        description="List of errors that occurred during order validation.",
        default_value=[],
        required=True,
    )
    display_gross_prices = graphene.Boolean(
        description=(
            "Determines whether checkout prices should include taxes when displayed "
            "in a storefront." + ADDED_IN_39
        ),
        required=True,
    )
    external_reference = graphene.String(
        description=f"External ID of this order. {ADDED_IN_310}", required=False
    )
    checkout_id = graphene.ID(
        description=(
            f"ID of the checkout that the order was created from. {ADDED_IN_311}"
        ),
        required=False,
    )

    granted_refunds = PermissionsField(
        NonNullList(OrderGrantedRefund),
        required=True,
        description="List of granted refunds." + ADDED_IN_313 + PREVIEW_FEATURE,
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    total_granted_refund = PermissionsField(
        Money,
        required=True,
        description="Total amount of granted refund." + ADDED_IN_313 + PREVIEW_FEATURE,
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    total_refunded = graphene.Field(
        Money,
        required=True,
        description="Total refund amount for the order."
        + ADDED_IN_313
        + PREVIEW_FEATURE,
    )
    total_refund_pending = PermissionsField(
        Money,
        required=True,
        description=(
            "Total amount of ongoing refund requests for the order's transactions."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        ),
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    total_authorize_pending = PermissionsField(
        Money,
        required=True,
        description=(
            "Total amount of ongoing authorize requests for the order's transactions."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        ),
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    total_charge_pending = PermissionsField(
        Money,
        required=True,
        description=(
            "Total amount of ongoing charge requests for the order's transactions."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        ),
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )
    total_cancel_pending = PermissionsField(
        Money,
        required=True,
        description=(
            "Total amount of ongoing cancel requests for the order's transactions."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        ),
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )

    total_remaining_grant = PermissionsField(
        Money,
        required=True,
        description=(
            "The difference amount between granted refund and the "
            "amounts that are pending and refunded." + ADDED_IN_313 + PREVIEW_FEATURE
        ),
        permissions=[OrderPermissions.MANAGE_ORDERS],
    )

    class Meta:
        description = "Represents an order in the shop."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Order

    @staticmethod
    def resolve_created(root: models.Order, _info):
        return root.created_at

    @staticmethod
    def resolve_channel(root: models.Order, info):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    def resolve_token(root: models.Order, info):
        return root.id

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
                if discount.type == DiscountType.VOUCHER:
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
                if discount.type == DiscountType.VOUCHER:
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
                if discount.type == DiscountType.VOUCHER:
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
            if root.use_old_id is False or is_owner_or_has_one_of_perms(
                requester, user, OrderPermissions.MANAGE_ORDERS
            ):
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
            if root.use_old_id is False or is_owner_or_has_one_of_perms(
                requester, user, OrderPermissions.MANAGE_ORDERS
            ):
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
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_shipping_price(root: models.Order, info):
        def _resolve_shipping_price(data):
            lines, manager = data
            return calculations.order_shipping(root, manager, lines)

        lines = OrderLinesByOrderIdLoader(info.context).load(root.id)
        manager = get_plugin_manager_promise(info.context)
        return Promise.all([lines, manager]).then(_resolve_shipping_price)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_shipping_tax_rate(root: models.Order, info):
        def _resolve_shipping_tax_rate(data):
            lines, manager = data
            return calculations.order_shipping_tax_rate(
                root, manager, lines
            ) or Decimal(0)

        lines = OrderLinesByOrderIdLoader(info.context).load(root.id)
        manager = get_plugin_manager_promise(info.context)
        return Promise.all([lines, manager]).then(_resolve_shipping_tax_rate)

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
        def _resolve_subtotal(data):
            order_lines, manager = data
            return calculations.order_subtotal(root, manager, order_lines)

        order_lines = OrderLinesByOrderIdLoader(info.context).load(root.id)
        manager = get_plugin_manager_promise(info.context)

        return Promise.all([order_lines, manager]).then(_resolve_subtotal)

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    @plugin_manager_promise_callback
    def resolve_total(root: models.Order, info, manager):
        def _resolve_total(lines):
            return calculations.order_total(root, manager, lines)

        return (
            OrderLinesByOrderIdLoader(info.context).load(root.id).then(_resolve_total)
        )

    @staticmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    def resolve_undiscounted_total(root: models.Order, info):
        def _resolve_undiscounted_total(lines_and_manager):
            lines, manager = lines_and_manager
            return calculations.order_undiscounted_total(root, manager, lines)

        lines = OrderLinesByOrderIdLoader(info.context).load(root.id)
        manager = get_plugin_manager_promise(info.context)
        return Promise.all([lines, manager]).then(_resolve_undiscounted_total)

    @staticmethod
    def resolve_total_authorized(root: models.Order, info):
        def _resolve_total_get_total_authorized(data):
            transactions, payments = data
            if transactions:
                authorized_money = prices.Money(Decimal(0), root.currency)
                for transaction in transactions:
                    authorized_money += transaction.amount_authorized
                return quantize_price(authorized_money, root.currency)
            return get_total_authorized(payments, root.currency)

        transactions = TransactionItemsByOrderIDLoader(info.context).load(root.id)
        payments = PaymentsByOrderIdLoader(info.context).load(root.id)
        return Promise.all([transactions, payments]).then(
            _resolve_total_get_total_authorized
        )

    @staticmethod
    def resolve_total_canceled(root: models.Order, info):
        def _resolve_total_canceled(transactions):
            canceled_money = prices.Money(Decimal(0), root.currency)
            if transactions:
                for transaction in transactions:
                    canceled_money += transaction.amount_canceled
            return quantize_price(canceled_money, root.currency)

        return (
            TransactionItemsByOrderIDLoader(info.context)
            .load(root.id)
            .then(_resolve_total_canceled)
        )

    @staticmethod
    def resolve_total_captured(root: models.Order, info):
        return root.total_charged

    @staticmethod
    def resolve_total_charged(root: models.Order, info):
        return root.total_charged

    @staticmethod
    def resolve_total_balance(root: models.Order, info):
        def _resolve_total_balance(data):
            granted_refunds, transactions, payments = data
            if any([p.is_active for p in payments]):
                return root.total_balance
            else:
                total_granted_refund = sum(
                    [granted_refund.amount for granted_refund in granted_refunds],
                    zero_money(root.currency),
                )
                total_charged = prices.Money(Decimal(0), root.currency)

                for transaction in transactions:
                    total_charged += transaction.amount_charged
                    total_charged += transaction.amount_charge_pending
                order_granted_refunds_difference = (
                    root.total.gross - total_granted_refund
                )
                return total_charged - order_granted_refunds_difference

        granted_refunds = OrderGrantedRefundsByOrderIdLoader(info.context).load(root.id)
        transactions = TransactionItemsByOrderIDLoader(info.context).load(root.id)
        payments = PaymentsByOrderIdLoader(info.context).load(root.id)
        return Promise.all([granted_refunds, transactions, payments]).then(
            _resolve_total_balance
        )

    @staticmethod
    def resolve_fulfillments(root: models.Order, info):
        def _resolve_fulfillments(fulfillments):
            user = info.context.user
            if user and user.is_staff:
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
    def resolve_events(root: models.Order, _info):
        return OrderEventsByOrderIdLoader(_info.context).load(root.id)

    @staticmethod
    def resolve_is_paid(root: models.Order, info):
        def _resolve_is_paid(transactions):
            if transactions:
                charged_money = prices.Money(Decimal(0), root.currency)
                for transaction in transactions:
                    charged_money += transaction.amount_charged
                return charged_money >= root.total.gross
            return root.is_fully_paid()

        return (
            TransactionItemsByOrderIDLoader(info.context)
            .load(root.id)
            .then(_resolve_is_paid)
        )

    @staticmethod
    def resolve_number(root: models.Order, _info):
        return str(root.number)

    @staticmethod
    @traced_resolver
    def resolve_payment_status(root: models.Order, info):
        def _resolve_payment_status(data):
            transactions, payments, fulfillments = data

            total_fulfillment_refund = sum(
                [
                    fulfillment.total_refund_amount
                    for fulfillment in fulfillments
                    if fulfillment.total_refund_amount
                ]
            )
            if (
                total_fulfillment_refund != 0
                and total_fulfillment_refund == root.total.gross.amount
            ):
                return ChargeStatus.FULLY_REFUNDED

            if transactions:
                return get_payment_status_for_order(root)
            last_payment = get_last_payment(payments)
            if not last_payment:
                if root.total.gross.amount == 0:
                    return ChargeStatus.FULLY_CHARGED
                return ChargeStatus.NOT_CHARGED
            return last_payment.charge_status

        transactions = TransactionItemsByOrderIDLoader(info.context).load(root.id)
        payments = PaymentsByOrderIdLoader(info.context).load(root.id)
        fulfillments = FulfillmentsByOrderIdLoader(info.context).load(root.id)
        return Promise.all([transactions, payments, fulfillments]).then(
            _resolve_payment_status
        )

    @staticmethod
    def resolve_payment_status_display(root: models.Order, info):
        def _resolve_payment_status(data):
            transactions, payments = data
            if transactions:
                status = get_payment_status_for_order(root)
                return dict(ChargeStatus.CHOICES).get(status)
            last_payment = get_last_payment(payments)
            if not last_payment:
                if root.total.gross.amount == 0:
                    return dict(ChargeStatus.CHOICES).get(ChargeStatus.FULLY_CHARGED)
                return dict(ChargeStatus.CHOICES).get(ChargeStatus.NOT_CHARGED)
            return last_payment.get_charge_status_display()

        transactions = TransactionItemsByOrderIDLoader(info.context).load(root.id)
        payments = PaymentsByOrderIdLoader(info.context).load(root.id)
        return Promise.all([transactions, payments]).then(_resolve_payment_status)

    @staticmethod
    def resolve_payments(root: models.Order, info):
        return PaymentsByOrderIdLoader(info.context).load(root.id)

    @staticmethod
    @one_of_permissions_required(
        [OrderPermissions.MANAGE_ORDERS, PaymentPermissions.HANDLE_PAYMENTS]
    )
    def resolve_transactions(root: models.Order, info):
        return TransactionItemsByOrderIDLoader(info.context).load(root.id)

    @staticmethod
    def resolve_status_display(root: models.Order, _info):
        return root.get_status_display()

    @staticmethod
    @traced_resolver
    def resolve_can_finalize(root: models.Order, info):
        if root.status == OrderStatus.DRAFT:

            def _validate_draft_order(manager):
                country = get_order_country(root)
                try:
                    validate_draft_order(root, country, manager)
                except ValidationError:
                    return False
                return True

            return get_plugin_manager_promise(info.context).then(_validate_draft_order)
        return True

    @staticmethod
    def resolve_user_email(root: models.Order, info):
        def _resolve_user_email(user):
            requester = get_user_or_app_from_context(info.context)
            if root.use_old_id is False or is_owner_or_has_one_of_perms(
                requester, user, OrderPermissions.MANAGE_ORDERS
            ):
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
            check_is_owner_or_has_one_of_perms(
                requester,
                user,
                AccountPermissions.MANAGE_USERS,
                OrderPermissions.MANAGE_ORDERS,
            )
            return user

        if not root.user_id:
            return None

        return UserByUserIdLoader(info.context).load(root.user_id).then(_resolve_user)

    @staticmethod
    def resolve_shipping_method(root: models.Order, info):
        external_app_shipping_id = get_external_shipping_id(root)

        if external_app_shipping_id:
            tax_config = TaxConfigurationByChannelId(info.context).load(root.channel_id)

            def with_tax_config(tax_config):
                prices_entered_with_tax = tax_config.prices_entered_with_tax
                price = (
                    root.shipping_price_gross
                    if prices_entered_with_tax
                    else root.shipping_price_net
                )
                return ShippingMethodData(
                    id=external_app_shipping_id,
                    name=root.shipping_method_name,
                    price=price,
                )

            return tax_config.then(with_tax_config)

        if not root.shipping_method_id:
            return None

        def wrap_shipping_method_with_channel_context(data):
            shipping_method, channel = data
            listing = (
                ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(
                    info.context
                ).load((shipping_method.id, channel.slug))
            )

            def calculate_price(
                listing: Optional[ShippingMethodChannelListing],
            ) -> Optional[ShippingMethodData]:
                if not listing:
                    return None
                return convert_to_shipping_method_data(shipping_method, listing)

            return listing.then(calculate_price)

        shipping_method = ShippingMethodByIdLoader(info.context).load(
            int(root.shipping_method_id)
        )
        channel = ChannelByIdLoader(info.context).load(root.channel_id)

        return Promise.all([shipping_method, channel]).then(
            wrap_shipping_method_with_channel_context
        )

    @classmethod
    def resolve_delivery_method(cls, root: models.Order, info):
        if root.shipping_method_id or get_external_shipping_id(root):
            return cls.resolve_shipping_method(root, info)
        if root.collection_point_id:
            collection_point = WarehouseByIdLoader(info.context).load(
                root.collection_point_id
            )
            return collection_point
        return None

    @classmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    # TODO: We should optimize it in/after PR#5819
    def resolve_shipping_methods(cls, root: models.Order, info):
        def with_channel(data):
            channel, manager = data

            def with_listings(channel_listings):
                return get_valid_shipping_methods_for_order(
                    root, channel_listings, manager
                )

            return (
                ShippingMethodChannelListingByChannelSlugLoader(info.context)
                .load(channel.slug)
                .then(with_listings)
            )

        channel = ChannelByIdLoader(info.context).load(root.channel_id)
        manager = get_plugin_manager_promise(info.context)

        return Promise.all([channel, manager]).then(with_channel)

    @classmethod
    @traced_resolver
    @prevent_sync_event_circular_query
    # TODO: We should optimize it in/after PR#5819
    def resolve_available_shipping_methods(cls, root: models.Order, info):
        return cls.resolve_shipping_methods(root, info).then(
            lambda methods: [method for method in methods if method.active]
        )

    @classmethod
    @traced_resolver
    def resolve_available_collection_points(cls, root: models.Order, info):
        def get_available_collection_points(lines):
            return get_valid_collection_points_for_order(lines, root.channel_id)

        return cls.resolve_lines(root, info).then(get_available_collection_points)

    @staticmethod
    def resolve_invoices(root: models.Order, info):
        requester = get_user_or_app_from_context(info.context)
        if root.use_old_id is True:
            check_is_owner_or_has_one_of_perms(
                requester, root.user, OrderPermissions.MANAGE_ORDERS
            )
        return InvoicesByOrderIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_is_shipping_required(root: models.Order, info):
        return (
            OrderLinesByOrderIdLoader(info.context)
            .load(root.id)
            .then(lambda lines: any(line.is_shipping_required for line in lines))
        )

    @staticmethod
    def resolve_gift_cards(root: models.Order, info):
        return GiftCardsByOrderIdLoader(info.context).load(root.id)

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
    def resolve_language_code_enum(root: models.Order, _info):
        return LanguageCodeEnum[str_to_enum(root.language_code)]

    @staticmethod
    def resolve_original(root: models.Order, _info):
        if not root.original_id:
            return None
        return graphene.Node.to_global_id("Order", root.original_id)

    @staticmethod
    @traced_resolver
    def resolve_errors(root: models.Order, info):
        if root.status == OrderStatus.DRAFT:

            def _validate_order(manager):
                country = get_order_country(root)
                try:
                    validate_draft_order(root, country, manager)
                except ValidationError as e:
                    return validation_error_to_error_type(e, OrderError)
                return []

            return get_plugin_manager_promise(info.context).then(_validate_order)

        return []

    @staticmethod
    def resolve_granted_refunds(root: models.Order, info):
        return OrderGrantedRefundsByOrderIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_total_granted_refund(root: models.Order, info):
        def calculate_total_granted_refund(granted_refunds):
            return sum(
                [granted_refund.amount for granted_refund in granted_refunds],
                zero_money(root.currency),
            )

        return (
            OrderGrantedRefundsByOrderIdLoader(info.context)
            .load(root.id)
            .then(calculate_total_granted_refund)
        )

    @staticmethod
    def resolve_total_refunded(root: models.Order, info):
        def _resolve_total_refunded_for_transactions(transactions):
            return sum(
                [transaction.amount_refunded for transaction in transactions],
                zero_money(root.currency),
            )

        def _resolve_total_refunded_for_payment(transactions):
            # Calculate payment total refund requires iterating
            # over payment's transactions
            total_refund_amount = Decimal(0)
            for transaction in transactions:
                if (
                    transaction.kind == TransactionKind.REFUND
                    and transaction.is_success
                ):
                    total_refund_amount += transaction.amount
            return prices.Money(total_refund_amount, root.currency)

        def _resolve_total_refund(data):
            payments, transactions = data
            last_payment = get_last_payment(payments)
            if last_payment and last_payment.is_active:
                return (
                    TransactionByPaymentIdLoader(info.context)
                    .load(last_payment.id)
                    .then(_resolve_total_refunded_for_payment)
                )
            return _resolve_total_refunded_for_transactions(transactions)

        payments = PaymentsByOrderIdLoader(info.context).load(root.id)
        transactions = TransactionItemsByOrderIDLoader(info.context).load(root.id)
        return Promise.all([payments, transactions]).then(_resolve_total_refund)

    @staticmethod
    def resolve_total_refund_pending(root: models.Order, info):
        def _resolve_total_refund_pending(transactions):
            return sum(
                [transaction.amount_refund_pending for transaction in transactions],
                zero_money(root.currency),
            )

        return (
            TransactionItemsByOrderIDLoader(info.context)
            .load(root.id)
            .then(_resolve_total_refund_pending)
        )

    @staticmethod
    def resolve_total_authorize_pending(root: models.Order, info):
        def _resolve_total_authorize_pending(transactions):
            return sum(
                [transaction.amount_authorize_pending for transaction in transactions],
                zero_money(root.currency),
            )

        return (
            TransactionItemsByOrderIDLoader(info.context)
            .load(root.id)
            .then(_resolve_total_authorize_pending)
        )

    @staticmethod
    def resolve_total_charge_pending(root: models.Order, info):
        def _resolve_total_charge_pending(transactions):
            return sum(
                [transaction.amount_charge_pending for transaction in transactions],
                zero_money(root.currency),
            )

        return (
            TransactionItemsByOrderIDLoader(info.context)
            .load(root.id)
            .then(_resolve_total_charge_pending)
        )

    @staticmethod
    def resolve_total_cancel_pending(root: models.Order, info):
        def _resolve_total_cancel_pending(transactions):
            return sum(
                [transaction.amount_cancel_pending for transaction in transactions],
                zero_money(root.currency),
            )

        return (
            TransactionItemsByOrderIDLoader(info.context)
            .load(root.id)
            .then(_resolve_total_cancel_pending)
        )

    @staticmethod
    def resolve_total_remaining_grant(root: models.Order, info):
        def _resolve_total_remaining_grant_for_transactions(
            transactions, total_granted_refund
        ):
            total_pending_refund = sum(
                [transaction.amount_refund_pending for transaction in transactions],
                zero_money(root.currency),
            )
            total_refund = sum(
                [transaction.amount_refunded for transaction in transactions],
                zero_money(root.currency),
            )
            return total_granted_refund - (total_pending_refund + total_refund)

        def _resolve_total_remaining_grant(data):
            transactions, payments, granted_refunds = data
            total_granted_refund = sum(
                [granted_refund.amount for granted_refund in granted_refunds],
                zero_money(root.currency),
            )

            def _resolve_total_remaining_grant_for_payment(payment_transactions):
                total_refund_amount = Decimal(0)
                for transaction in payment_transactions:
                    if transaction.kind == TransactionKind.REFUND:
                        total_refund_amount += transaction.amount
                return prices.Money(
                    total_granted_refund.amount - total_refund_amount, root.currency
                )

            last_payment = get_last_payment(payments)
            if last_payment and last_payment.is_active:
                return (
                    TransactionByPaymentIdLoader(info.context)
                    .load(last_payment.id)
                    .then(_resolve_total_remaining_grant_for_payment)
                )
            return _resolve_total_remaining_grant_for_transactions(
                transactions, total_granted_refund
            )

        granted_refunds = OrderGrantedRefundsByOrderIdLoader(info.context).load(root.id)
        transactions = TransactionItemsByOrderIDLoader(info.context).load(root.id)
        payments = PaymentsByOrderIdLoader(info.context).load(root.id)
        return Promise.all([transactions, payments, granted_refunds]).then(
            _resolve_total_remaining_grant
        )

    def resolve_display_gross_prices(root: models.Order, info):
        tax_config = TaxConfigurationByChannelId(info.context).load(root.channel_id)
        country_code = get_order_country(root)

        def load_tax_country_exceptions(tax_config):
            tax_configs_per_country = (
                TaxConfigurationPerCountryByTaxConfigurationIDLoader(info.context).load(
                    tax_config.id
                )
            )

            def calculate_display_gross_prices(tax_configs_per_country):
                tax_config_country = next(
                    (
                        tc
                        for tc in tax_configs_per_country
                        if tc.country.code == country_code
                    ),
                    None,
                )
                return get_display_gross_prices(tax_config, tax_config_country)

            return tax_configs_per_country.then(calculate_display_gross_prices)

        return tax_config.then(load_tax_country_exceptions)

    @classmethod
    def resolve_shipping_tax_class(cls, root: models.Order, info):
        if root.shipping_method_id:
            return cls.resolve_shipping_method(root, info).then(
                lambda shipping_method_data: shipping_method_data.tax_class
                if shipping_method_data
                else None
            )
        return None

    @staticmethod
    def resolve_shipping_tax_class_metadata(root: models.Order, _info):
        return resolve_metadata(root.shipping_tax_class_metadata)

    @staticmethod
    def resolve_shipping_tax_class_private_metadata(root: models.Order, info):
        check_private_metadata_privilege(root, info)
        return resolve_metadata(root.shipping_tax_class_private_metadata)

    @staticmethod
    def resolve_checkout_id(root: models.Order, _info):
        if root.checkout_token:
            return graphene.Node.to_global_id("Checkout", root.checkout_token)
        return None

    @staticmethod
    def __resolve_references(roots: List["Order"], info):
        requestor = get_user_or_app_from_context(info.context)
        requestor_has_access_to_all = has_one_of_permissions(
            requestor, [OrderPermissions.MANAGE_ORDERS]
        )

        if requestor:
            qs = resolve_orders(
                info,
                requestor_has_access_to_all=requestor_has_access_to_all,
                requesting_user=info.context.user,
            )
        else:
            qs = models.Order.objects.none()

        return resolve_federation_references(Order, roots, qs)


class OrderCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        node = Order
