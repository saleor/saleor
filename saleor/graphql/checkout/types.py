import graphene
from promise import Promise

from ...checkout import calculations, models
from ...checkout.base_calculations import (
    calculate_undiscounted_base_line_total_price,
    calculate_undiscounted_base_line_unit_price,
)
from ...checkout.utils import get_valid_collection_points_for_checkout
from ...core.permissions import (
    AccountPermissions,
    CheckoutPermissions,
    PaymentPermissions,
)
from ...core.taxes import zero_taxed_money
from ...core.tracing import traced_resolver
from ...shipping.interface import ShippingMethodData
from ...warehouse import models as warehouse_models
from ...warehouse.reservations import is_reservation_enabled
from ..account.dataloaders import AddressByIdLoader
from ..account.utils import check_is_owner_or_has_one_of_perms
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByCheckoutLineIDLoader
from ..channel.types import Channel
from ..core.connection import CountableConnection
from ..core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ..core.enums import LanguageCodeEnum
from ..core.scalars import UUID
from ..core.types import ModelObjectType, Money, NonNullList, TaxedMoney
from ..core.utils import str_to_enum
from ..decorators import one_of_permissions_required
from ..discount.dataloaders import DiscountsByDateTimeLoader
from ..giftcard.types import GiftCard
from ..meta.types import ObjectWithMetadata
from ..payment.types import TransactionItem
from ..product.dataloaders import (
    ProductTypeByProductIdLoader,
    ProductTypeByVariantIdLoader,
    ProductVariantByIdLoader,
)
from ..shipping.types import ShippingMethod
from ..utils import get_user_or_app_from_context
from ..warehouse.dataloaders import StocksReservationsByCheckoutTokenLoader
from ..warehouse.types import Warehouse
from .dataloaders import (
    CheckoutByTokenLoader,
    CheckoutInfoByCheckoutTokenLoader,
    CheckoutLinesByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
    TransactionItemsByCheckoutIDLoader,
)


class GatewayConfigLine(graphene.ObjectType):
    field = graphene.String(required=True, description="Gateway config key.")
    value = graphene.String(description="Gateway config value for key.")

    class Meta:
        description = "Payment gateway client configuration key and value pair."


class PaymentGateway(graphene.ObjectType):
    name = graphene.String(required=True, description="Payment gateway name.")
    id = graphene.ID(required=True, description="Payment gateway ID.")
    config = NonNullList(
        GatewayConfigLine,
        required=True,
        description="Payment gateway client configuration.",
    )
    currencies = NonNullList(
        graphene.String,
        required=True,
        description="Payment gateway supported currencies.",
    )

    class Meta:
        description = (
            "Available payment gateway backend with configuration "
            "necessary to setup client."
        )


class CheckoutLine(ModelObjectType):
    id = graphene.GlobalID(required=True)
    variant = graphene.Field(
        "saleor.graphql.product.types.ProductVariant", required=True
    )
    quantity = graphene.Int(required=True)
    unit_price = graphene.Field(
        TaxedMoney,
        description="The unit price of the checkout line, with taxes and discounts.",
        required=True,
    )
    undiscounted_unit_price = graphene.Field(
        Money,
        description="The unit price of the checkout line, without discounts.",
        required=True,
    )
    total_price = graphene.Field(
        TaxedMoney,
        description="The sum of the checkout line price, taxes and discounts.",
        required=True,
    )
    undiscounted_total_price = graphene.Field(
        Money,
        description="The sum of the checkout line price, without discounts.",
        required=True,
    )
    requires_shipping = graphene.Boolean(
        description="Indicates whether the item need to be delivered.",
        required=True,
    )

    class Meta:
        description = "Represents an item in the checkout."
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        model = models.CheckoutLine

    @staticmethod
    def resolve_variant(root: models.CheckoutLine, info):
        variant = ProductVariantByIdLoader(info.context).load(root.variant_id)
        channel = ChannelByCheckoutLineIDLoader(info.context).load(root.id)

        return Promise.all([variant, channel]).then(
            lambda data: ChannelContext(node=data[0], channel_slug=data[1].slug)
        )

    @staticmethod
    def resolve_unit_price(root, info):
        def with_checkout(checkout):
            discounts = DiscountsByDateTimeLoader(info.context).load(
                info.context.request_time
            )
            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )
            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )

            def calculate_line_unit_price(data):
                (
                    discounts,
                    checkout_info,
                    lines,
                ) = data
                for line_info in lines:
                    if line_info.line.pk == root.pk:
                        return calculations.checkout_line_unit_price(
                            manager=info.context.plugins,
                            checkout_info=checkout_info,
                            lines=lines,
                            checkout_line_info=line_info,
                            discounts=discounts,
                        )
                return None

            return Promise.all(
                [
                    discounts,
                    checkout_info,
                    lines,
                ]
            ).then(calculate_line_unit_price)

        return (
            CheckoutByTokenLoader(info.context)
            .load(root.checkout_id)
            .then(with_checkout)
        )

    @staticmethod
    def resolve_undiscounted_unit_price(root, info):
        def with_checkout(checkout):
            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )
            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )

            def calculate_undiscounted_unit_price(data):
                (
                    checkout_info,
                    lines,
                ) = data
                for line_info in lines:
                    if line_info.line.pk == root.pk:
                        return calculate_undiscounted_base_line_unit_price(
                            line_info, checkout_info.channel
                        )

                return None

            return Promise.all(
                [
                    checkout_info,
                    lines,
                ]
            ).then(calculate_undiscounted_unit_price)

        return (
            CheckoutByTokenLoader(info.context)
            .load(root.checkout_id)
            .then(with_checkout)
        )

    @staticmethod
    @traced_resolver
    def resolve_total_price(root, info):
        def with_checkout(checkout):
            discounts = DiscountsByDateTimeLoader(info.context).load(
                info.context.request_time
            )
            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )
            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )

            def calculate_line_total_price(data):
                (
                    discounts,
                    checkout_info,
                    lines,
                ) = data
                for line_info in lines:
                    if line_info.line.pk == root.pk:
                        return calculations.checkout_line_total(
                            manager=info.context.plugins,
                            checkout_info=checkout_info,
                            lines=lines,
                            checkout_line_info=line_info,
                            discounts=discounts,
                        )
                return None

            return Promise.all(
                [
                    discounts,
                    checkout_info,
                    lines,
                ]
            ).then(calculate_line_total_price)

        return (
            CheckoutByTokenLoader(info.context)
            .load(root.checkout_id)
            .then(with_checkout)
        )

    @staticmethod
    def resolve_undiscounted_total_price(root, info):
        def with_checkout(checkout):
            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )
            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                checkout.token
            )

            def calculate_undiscounted_total_price(data):
                (
                    checkout_info,
                    lines,
                ) = data
                for line_info in lines:
                    if line_info.line.pk == root.pk:
                        return calculate_undiscounted_base_line_total_price(
                            line_info, checkout_info.channel
                        )
                return None

            return Promise.all(
                [
                    checkout_info,
                    lines,
                ]
            ).then(calculate_undiscounted_total_price)

        return (
            CheckoutByTokenLoader(info.context)
            .load(root.checkout_id)
            .then(with_checkout)
        )

    @staticmethod
    def resolve_requires_shipping(root: models.CheckoutLine, info):
        def is_shipping_required(product_type):
            return product_type.is_shipping_required

        return (
            ProductTypeByVariantIdLoader(info.context)
            .load(root.variant_id)
            .then(is_shipping_required)
        )


class CheckoutLineCountableConnection(CountableConnection):
    class Meta:
        node = CheckoutLine


class DeliveryMethod(graphene.Union):
    class Meta:
        description = (
            "Represents a delivery method chosen for the checkout. "
            '`Warehouse` type is used when checkout is marked as "click and collect" '
            "and `ShippingMethod` otherwise." + ADDED_IN_31 + PREVIEW_FEATURE
        )
        types = (Warehouse, ShippingMethod)

    @classmethod
    def resolve_type(cls, instance, info):
        if isinstance(instance, ShippingMethodData):
            return ShippingMethod
        if isinstance(instance, warehouse_models.Warehouse):
            return Warehouse

        return super(DeliveryMethod, cls).resolve_type(instance, info)


class Checkout(ModelObjectType):
    id = graphene.ID(required=True)
    created = graphene.DateTime(required=True)
    last_change = graphene.DateTime(required=True)
    user = graphene.Field("saleor.graphql.account.types.User")
    channel = graphene.Field(Channel, required=True)
    billing_address = graphene.Field("saleor.graphql.account.types.Address")
    shipping_address = graphene.Field("saleor.graphql.account.types.Address")
    note = graphene.String(required=True)
    discount = graphene.Field(Money)
    discount_name = graphene.String()
    translated_discount_name = graphene.String()
    voucher_code = graphene.String()
    available_shipping_methods = NonNullList(
        ShippingMethod,
        required=True,
        description="Shipping methods that can be used with this checkout.",
        deprecation_reason=(f"{DEPRECATED_IN_3X_FIELD} Use `shippingMethods` instead."),
    )
    shipping_methods = NonNullList(
        ShippingMethod,
        required=True,
        description="Shipping methods that can be used with this checkout.",
    )
    available_collection_points = NonNullList(
        Warehouse,
        required=True,
        description=(
            "Collection points that can be used for this order."
            + ADDED_IN_31
            + PREVIEW_FEATURE
        ),
    )
    available_payment_gateways = NonNullList(
        PaymentGateway,
        description="List of available payment gateways.",
        required=True,
    )
    email = graphene.String(description="Email of a customer.", required=False)
    gift_cards = NonNullList(
        GiftCard,
        description="List of gift cards associated with this checkout.",
        required=True,
    )
    is_shipping_required = graphene.Boolean(
        description="Returns True, if checkout requires shipping.", required=True
    )
    quantity = graphene.Int(description="The number of items purchased.", required=True)
    stock_reservation_expires = graphene.DateTime(
        description=(
            "Date when oldest stock reservation for this checkout "
            "expires or null if no stock is reserved." + ADDED_IN_31
        ),
    )
    lines = NonNullList(
        CheckoutLine,
        description=(
            "A list of checkout lines, each containing information about "
            "an item in the checkout."
        ),
        required=True,
    )
    shipping_price = graphene.Field(
        TaxedMoney,
        description="The price of the shipping, with all the taxes included.",
        required=True,
    )
    shipping_method = graphene.Field(
        ShippingMethod,
        description="The shipping method related with checkout.",
        deprecation_reason=(f"{DEPRECATED_IN_3X_FIELD} Use `deliveryMethod` instead."),
    )

    delivery_method = graphene.Field(
        DeliveryMethod,
        description=(
            "The delivery method selected for this checkout."
            + ADDED_IN_31
            + PREVIEW_FEATURE
        ),
    )

    subtotal_price = graphene.Field(
        TaxedMoney,
        description="The price of the checkout before shipping, with taxes included.",
        required=True,
    )
    token = graphene.Field(UUID, description="The checkout's token.", required=True)
    total_price = graphene.Field(
        TaxedMoney,
        description=(
            "The sum of the the checkout line prices, with all the taxes,"
            "shipping costs, and discounts included."
        ),
        required=True,
    )
    language_code = graphene.Field(
        LanguageCodeEnum, description="Checkout language code.", required=True
    )

    transactions = NonNullList(
        TransactionItem,
        description=(
            "List of transactions for the checkout. Requires one of the "
            "following permissions: MANAGE_CHECKOUTS, HANDLE_PAYMENTS."
            + ADDED_IN_34
            + PREVIEW_FEATURE
        ),
    )

    class Meta:
        description = "Checkout object."
        model = models.Checkout
        interfaces = [graphene.relay.Node, ObjectWithMetadata]

    @staticmethod
    def resolve_created(root: models.Checkout, _info):
        return root.created_at

    @staticmethod
    def resolve_id(root: models.Checkout, _):
        return graphene.Node.to_global_id("Checkout", root.pk)

    @staticmethod
    def resolve_shipping_address(root: models.Checkout, info):
        if not root.shipping_address_id:
            return
        return AddressByIdLoader(info.context).load(root.shipping_address_id)

    @staticmethod
    def resolve_billing_address(root: models.Checkout, info):
        if not root.billing_address_id:
            return
        return AddressByIdLoader(info.context).load(root.billing_address_id)

    @staticmethod
    def resolve_user(root: models.Checkout, info):
        if not root.user_id:
            return None
        requestor = get_user_or_app_from_context(info.context)
        check_is_owner_or_has_one_of_perms(
            requestor, root.user, AccountPermissions.MANAGE_USERS
        )
        return root.user

    @staticmethod
    def resolve_email(root: models.Checkout, _info):
        return root.get_customer_email()

    @classmethod
    def resolve_shipping_method(cls, root: models.Checkout, info):
        def with_checkout_info(checkout_info):
            delivery_method = checkout_info.delivery_method_info.delivery_method
            if not delivery_method or not isinstance(
                delivery_method, ShippingMethodData
            ):
                return
            return delivery_method

        return (
            CheckoutInfoByCheckoutTokenLoader(info.context)
            .load(root.token)
            .then(with_checkout_info)
        )

    @classmethod
    @traced_resolver
    def resolve_shipping_methods(cls, root: models.Checkout, info):
        return (
            CheckoutInfoByCheckoutTokenLoader(info.context)
            .load(root.token)
            .then(lambda checkout_info: checkout_info.all_shipping_methods)
        )

    @staticmethod
    def resolve_delivery_method(root: models.Checkout, info):
        return (
            CheckoutInfoByCheckoutTokenLoader(info.context)
            .load(root.token)
            .then(
                lambda checkout_info: checkout_info.delivery_method_info.delivery_method
            )
        )

    @staticmethod
    def resolve_quantity(root: models.Checkout, info):
        checkout_info = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
            root.token
        )

        def calculate_quantity(lines):
            return sum([line_info.line.quantity for line_info in lines])

        return checkout_info.then(calculate_quantity)

    @staticmethod
    @traced_resolver
    # TODO: We should optimize it in/after PR#5819
    def resolve_total_price(root: models.Checkout, info):
        def calculate_total_price(data):
            address, lines, checkout_info, discounts = data
            taxed_total = calculations.calculate_checkout_total_with_gift_cards(
                manager=info.context.plugins,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                discounts=discounts,
            )
            return max(taxed_total, zero_taxed_money(root.currency))

        address_id = root.shipping_address_id or root.billing_address_id
        address = (
            AddressByIdLoader(info.context).load(address_id) if address_id else None
        )
        lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
        checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, checkout_info, discounts]).then(
            calculate_total_price
        )

    @staticmethod
    @traced_resolver
    # TODO: We should optimize it in/after PR#5819
    def resolve_subtotal_price(root: models.Checkout, info):
        def calculate_subtotal_price(data):
            address, lines, checkout_info, discounts = data
            return calculations.checkout_subtotal(
                manager=info.context.plugins,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                discounts=discounts,
            )

        address_id = root.shipping_address_id or root.billing_address_id
        address = (
            AddressByIdLoader(info.context).load(address_id) if address_id else None
        )
        lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
        checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, checkout_info, discounts]).then(
            calculate_subtotal_price
        )

    @staticmethod
    @traced_resolver
    # TODO: We should optimize it in/after PR#5819
    def resolve_shipping_price(root: models.Checkout, info):
        def calculate_shipping_price(data):
            address, lines, checkout_info, discounts = data
            return calculations.checkout_shipping_price(
                manager=info.context.plugins,
                checkout_info=checkout_info,
                lines=lines,
                address=address,
                discounts=discounts,
            )

        address = (
            AddressByIdLoader(info.context).load(root.shipping_address_id)
            if root.shipping_address_id
            else None
        )
        lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
        checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, checkout_info, discounts]).then(
            calculate_shipping_price
        )

    @staticmethod
    def resolve_lines(root: models.Checkout, info):
        return CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)

    @staticmethod
    @traced_resolver
    def resolve_available_shipping_methods(root: models.Checkout, info):
        return (
            CheckoutInfoByCheckoutTokenLoader(info.context)
            .load(root.token)
            .then(lambda checkout_info: checkout_info.valid_shipping_methods)
        )

    @staticmethod
    @traced_resolver
    def resolve_available_collection_points(root: models.Checkout, info):
        def get_available_collection_points(lines):
            return get_valid_collection_points_for_checkout(lines, root.channel_id)

        return (
            CheckoutLinesInfoByCheckoutTokenLoader(info.context)
            .load(root.token)
            .then(get_available_collection_points)
        )

    @staticmethod
    def resolve_available_payment_gateways(root: models.Checkout, info):
        return info.context.plugins.list_payment_gateways(
            currency=root.currency, checkout=root, channel_slug=root.channel.slug
        )

    @staticmethod
    def resolve_gift_cards(root: models.Checkout, _info):
        return root.gift_cards.all()

    @staticmethod
    def resolve_is_shipping_required(root: models.Checkout, info):
        def is_shipping_required(lines):
            product_ids = [line_info.product.id for line_info in lines]

            def with_product_types(product_types):
                return any([pt.is_shipping_required for pt in product_types])

            return (
                ProductTypeByProductIdLoader(info.context)
                .load_many(product_ids)
                .then(with_product_types)
            )

        return (
            CheckoutLinesInfoByCheckoutTokenLoader(info.context)
            .load(root.token)
            .then(is_shipping_required)
        )

    @staticmethod
    def resolve_language_code(root, _info):
        return LanguageCodeEnum[str_to_enum(root.language_code)]

    @staticmethod
    @traced_resolver
    def resolve_stock_reservation_expires(root: models.Checkout, info):
        if not is_reservation_enabled(info.context.site.settings):
            return None

        def get_oldest_stock_reservation_expiration_date(reservations):
            if not reservations:
                return None

            return min(reservation.reserved_until for reservation in reservations)

        return (
            StocksReservationsByCheckoutTokenLoader(info.context)
            .load(root.token)
            .then(get_oldest_stock_reservation_expiration_date)
        )

    @staticmethod
    @one_of_permissions_required(
        [CheckoutPermissions.MANAGE_CHECKOUTS, PaymentPermissions.HANDLE_PAYMENTS]
    )
    def resolve_transactions(root: models.Checkout, info):
        return TransactionItemsByCheckoutIDLoader(info.context).load(root.pk)


class CheckoutCountableConnection(CountableConnection):
    class Meta:
        node = Checkout
