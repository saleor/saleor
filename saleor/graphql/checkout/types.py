import graphene
from promise import Promise

from ...checkout import calculations, models
from ...checkout.utils import get_valid_shipping_methods_for_checkout
from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions, CheckoutPermissions
from ...core.taxes import display_gross_prices, zero_taxed_money
from ..account.dataloaders import AddressByIdLoader
from ..core.connection import CountableDjangoObjectType
from ..core.scalars import UUID
from ..core.types.money import TaxedMoney
from ..decorators import permission_required
from ..discount.dataloaders import DiscountsByDateTimeLoader
from ..giftcard.types import GiftCard
from ..meta.deprecated.resolvers import resolve_meta, resolve_private_meta
from ..meta.types import ObjectWithMetadata
from ..product.dataloaders import (
    CollectionsByVariantIdLoader,
    ProductByVariantIdLoader,
    ProductTypeByProductIdLoader,
    ProductTypeByVariantIdLoader,
    ProductVariantByIdLoader,
)
from ..shipping.types import ShippingMethod
from .dataloaders import (
    CheckoutByTokenLoader,
    CheckoutLinesByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
)


class GatewayConfigLine(graphene.ObjectType):
    field = graphene.String(required=True, description="Gateway config key.")
    value = graphene.String(description="Gateway config value for key.")

    class Meta:
        description = "Payment gateway client configuration key and value pair."


class PaymentGateway(graphene.ObjectType):
    name = graphene.String(required=True, description="Payment gateway name.")
    id = graphene.ID(required=True, description="Payment gateway ID.")
    config = graphene.List(
        graphene.NonNull(GatewayConfigLine),
        required=True,
        description="Payment gateway client configuration.",
    )
    currencies = graphene.List(
        graphene.String,
        required=True,
        description="Payment gateway supported currencies.",
    )

    class Meta:
        description = (
            "Available payment gateway backend with configuration "
            "necessary to setup client."
        )


class CheckoutLine(CountableDjangoObjectType):
    total_price = graphene.Field(
        TaxedMoney,
        description="The sum of the checkout line price, taxes and discounts.",
    )
    requires_shipping = graphene.Boolean(
        description="Indicates whether the item need to be delivered."
    )

    class Meta:
        only_fields = ["id", "quantity", "variant"]
        description = "Represents an item in the checkout."
        interfaces = [graphene.relay.Node]
        model = models.CheckoutLine
        filter_fields = ["id"]

    @staticmethod
    def resolve_variant(root: models.CheckoutLine, info):
        return ProductVariantByIdLoader(info.context).load(root.variant_id)

    @staticmethod
    def resolve_total_price(root: models.CheckoutLine, info):
        def calculate_line_total_price(data):
            address, variant, product, collections, discounts = data
            return info.context.plugins.calculate_checkout_line_total(
                checkout_line=root,
                variant=variant,
                product=product,
                collections=collections,
                address=address,
                discounts=discounts,
            )

        def with_checkout(checkout):
            address_id = checkout.shipping_address_id or checkout.billing_address_id
            address = (
                AddressByIdLoader(info.context).load(address_id) if address_id else None
            )
            variant = ProductVariantByIdLoader(info.context).load(root.variant_id)
            product = ProductByVariantIdLoader(info.context).load(root.variant_id)
            collections = CollectionsByVariantIdLoader(info.context).load(
                root.variant_id
            )
            discounts = DiscountsByDateTimeLoader(info.context).load(
                info.context.request_time
            )
            return Promise.all(
                [address, variant, product, collections, discounts]
            ).then(calculate_line_total_price)

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


class Checkout(CountableDjangoObjectType):
    available_shipping_methods = graphene.List(
        ShippingMethod,
        required=True,
        description="Shipping methods that can be used with this order.",
    )
    available_payment_gateways = graphene.List(
        graphene.NonNull(PaymentGateway),
        description="List of available payment gateways.",
        required=True,
    )
    email = graphene.String(description="Email of a customer.", required=True)
    gift_cards = graphene.List(
        GiftCard, description="List of gift cards associated with this checkout."
    )
    is_shipping_required = graphene.Boolean(
        description="Returns True, if checkout requires shipping.", required=True
    )
    lines = graphene.List(
        CheckoutLine,
        description=(
            "A list of checkout lines, each containing information about "
            "an item in the checkout."
        ),
    )
    shipping_price = graphene.Field(
        TaxedMoney,
        description="The price of the shipping, with all the taxes included.",
    )
    subtotal_price = graphene.Field(
        TaxedMoney,
        description="The price of the checkout before shipping, with taxes included.",
    )
    token = graphene.Field(UUID, description=("The checkout's token."), required=True)
    total_price = graphene.Field(
        TaxedMoney,
        description=(
            "The sum of the the checkout line prices, with all the taxes,"
            "shipping costs, and discounts included."
        ),
    )

    class Meta:
        only_fields = [
            "billing_address",
            "created",
            "discount_name",
            "gift_cards",
            "is_shipping_required",
            "last_change",
            "note",
            "quantity",
            "shipping_address",
            "shipping_method",
            "translated_discount_name",
            "user",
            "voucher_code",
            "discount",
        ]
        description = "Checkout object."
        model = models.Checkout
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        filter_fields = ["token"]

    @staticmethod
    def resolve_user(root: models.Checkout, info):
        user = info.context.user
        if user == root.user or user.has_perm(AccountPermissions.MANAGE_USERS):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_email(root: models.Checkout, _info):
        return root.get_customer_email()

    @staticmethod
    def resolve_total_price(root: models.Checkout, info):
        def calculate_total_price(data):
            address, lines, discounts = data
            taxed_total = (
                calculations.checkout_total(
                    manager=info.context.plugins,
                    checkout=root,
                    lines=lines,
                    address=address,
                    discounts=discounts,
                )
                - root.get_total_gift_cards_balance()
            )
            return max(taxed_total, zero_taxed_money())

        address_id = root.shipping_address_id or root.billing_address_id
        address = (
            AddressByIdLoader(info.context).load(address_id) if address_id else None
        )
        lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, discounts]).then(calculate_total_price)

    @staticmethod
    def resolve_subtotal_price(root: models.Checkout, info):
        def calculate_subtotal_price(data):
            address, lines, discounts = data
            return calculations.checkout_subtotal(
                manager=info.context.plugins,
                checkout=root,
                lines=lines,
                address=address,
                discounts=discounts,
            )

        address_id = root.shipping_address_id or root.billing_address_id
        address = (
            AddressByIdLoader(info.context).load(address_id) if address_id else None
        )
        lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, discounts]).then(calculate_subtotal_price)

    @staticmethod
    def resolve_shipping_price(root: models.Checkout, info):
        def calculate_shipping_price(data):
            address, lines, discounts = data
            return calculations.checkout_shipping_price(
                manager=info.context.plugins,
                checkout=root,
                lines=lines,
                address=address,
                discounts=discounts,
            )

        address = (
            AddressByIdLoader(info.context).load(root.shipping_address_id)
            if root.shipping_address_id
            else None
        )
        lines = CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, discounts]).then(calculate_shipping_price)

    @staticmethod
    def resolve_lines(root: models.Checkout, info):
        return CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)

    @staticmethod
    def resolve_available_shipping_methods(root: models.Checkout, info):
        def calculate_available_shipping_methods(data):
            address, lines, discounts = data
            available = get_valid_shipping_methods_for_checkout(root, lines, discounts)
            if available is None:
                return []

            display_gross = display_gross_prices()
            for shipping_method in available:
                # ignore mypy checking because it is checked in
                # get_valid_shipping_methods_for_checkout
                taxed_price = info.context.plugins.apply_taxes_to_shipping(
                    shipping_method.price, address
                )
                if display_gross:
                    shipping_method.price = taxed_price.gross
                else:
                    shipping_method.price = taxed_price.net
            return available

        address = (
            AddressByIdLoader(info.context).load(root.shipping_address_id)
            if root.shipping_address_id
            else None
        )
        lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, discounts]).then(
            calculate_available_shipping_methods
        )

    @staticmethod
    def resolve_available_payment_gateways(root: models.Checkout, info):
        return info.context.plugins.checkout_available_payment_gateways(checkout=root)

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
    @permission_required(CheckoutPermissions.MANAGE_CHECKOUTS)
    def resolve_private_meta(root: models.Checkout, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.Checkout, _info):
        return resolve_meta(root, _info)
