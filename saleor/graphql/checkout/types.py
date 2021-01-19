import graphene
from promise import Promise

from ...checkout import calculations, models
from ...checkout.utils import get_valid_shipping_methods_for_checkout
from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions
from ...core.taxes import zero_taxed_money
from ..account.dataloaders import AddressByIdLoader
from ..account.utils import requestor_has_access
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByCheckoutLineIDLoader, ChannelByIdLoader
from ..core.connection import CountableDjangoObjectType
from ..core.scalars import UUID
from ..core.types.money import TaxedMoney
from ..discount.dataloaders import DiscountsByDateTimeLoader
from ..giftcard.types import GiftCard
from ..meta.types import ObjectWithMetadata
from ..product.dataloaders import (
    CollectionsByVariantIdLoader,
    ProductByVariantIdLoader,
    ProductTypeByProductIdLoader,
    ProductTypeByVariantIdLoader,
    ProductVariantByIdLoader,
    VariantChannelListingByVariantIdAndChannelSlugLoader,
)
from ..shipping.dataloaders import (
    ShippingMethodByIdLoader,
    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader,
)
from ..shipping.types import ShippingMethod
from ..utils import get_user_or_app_from_context
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
        variant = ProductVariantByIdLoader(info.context).load(root.variant_id)
        channel = ChannelByCheckoutLineIDLoader(info.context).load(root.id)

        return Promise.all([variant, channel]).then(
            lambda data: ChannelContext(node=data[0], channel_slug=data[1].slug)
        )

    @staticmethod
    def resolve_total_price(root, info):
        def with_checkout(checkout):
            def with_channel(channel):
                address_id = checkout.shipping_address_id or checkout.billing_address_id
                address = (
                    AddressByIdLoader(info.context).load(address_id)
                    if address_id
                    else None
                )
                variant = ProductVariantByIdLoader(info.context).load(root.variant_id)
                channel_listing = VariantChannelListingByVariantIdAndChannelSlugLoader(
                    info.context
                ).load((root.variant_id, channel.slug))
                product = ProductByVariantIdLoader(info.context).load(root.variant_id)
                collections = CollectionsByVariantIdLoader(info.context).load(
                    root.variant_id
                )
                discounts = DiscountsByDateTimeLoader(info.context).load(
                    info.context.request_time
                )
                return Promise.all(
                    [
                        checkout,
                        address,
                        variant,
                        channel_listing,
                        product,
                        collections,
                        channel,
                        discounts,
                    ]
                ).then(calculate_line_total_price)

            return (
                ChannelByCheckoutLineIDLoader(info.context)
                .load(root.id)
                .then(with_channel)
            )

        def calculate_line_total_price(data):
            (
                checkout,
                address,
                variant,
                channel_listing,
                product,
                collections,
                channel,
                discounts,
            ) = data
            return info.context.plugins.calculate_checkout_line_total(
                checkout=checkout,
                checkout_line=root,
                variant=variant,
                product=product,
                collections=collections,
                address=address,
                channel=channel,
                channel_listing=channel_listing,
                discounts=discounts,
            )

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
    shipping_method = graphene.Field(
        ShippingMethod,
        description="The shipping method related with checkout.",
    )
    subtotal_price = graphene.Field(
        TaxedMoney,
        description="The price of the checkout before shipping, with taxes included.",
    )
    token = graphene.Field(UUID, description="The checkout's token.", required=True)
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
            "channel",
            "note",
            "quantity",
            "shipping_address",
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
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(requestor, root.user, AccountPermissions.MANAGE_USERS):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_email(root: models.Checkout, _info):
        return root.get_customer_email()

    @staticmethod
    def resolve_shipping_method(root: models.Checkout, info):
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
    # TODO: We should optimize it in/after PR#5819
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
            return max(taxed_total, zero_taxed_money(root.currency))

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
    # TODO: We should optimize it in/after PR#5819
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
    # TODO: We should optimize it in/after PR#5819
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
        lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, discounts]).then(calculate_shipping_price)

    @staticmethod
    def resolve_lines(root: models.Checkout, info):
        return CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)

    @staticmethod
    # TODO: We should optimize it in/after PR#5819
    def resolve_available_shipping_methods(root: models.Checkout, info):
        def calculate_available_shipping_methods(data):
            address, lines, discounts, channel = data
            channel_slug = channel.slug
            display_gross = info.context.site.settings.display_gross_prices
            manager = info.context.plugins
            subtotal = manager.calculate_checkout_subtotal(
                root, lines, address, discounts
            )
            if not address:
                return []
            available = get_valid_shipping_methods_for_checkout(
                root,
                lines,
                discounts,
                subtotal=subtotal,
                country_code=address.country.code,
            )
            if available is None:
                return []
            available_ids = available.values_list("id", flat=True)

            def map_shipping_method_with_channel(shippings):
                def apply_price_to_shipping_method(channel_listings):
                    channel_listing_map = {
                        channel_listing.shipping_method_id: channel_listing
                        for channel_listing in channel_listings
                    }
                    available_with_channel_context = []
                    for shipping in shippings:
                        shipping_channel_listing = channel_listing_map[shipping.id]
                        taxed_price = info.context.plugins.apply_taxes_to_shipping(
                            shipping_channel_listing.price, address
                        )
                        if display_gross:
                            shipping.price = taxed_price.gross
                        else:
                            shipping.price = taxed_price.net
                        available_with_channel_context.append(
                            ChannelContext(node=shipping, channel_slug=channel_slug)
                        )
                    return available_with_channel_context

                map_shipping_method_and_channel = (
                    (shipping_method_id, channel_slug)
                    for shipping_method_id in available_ids
                )
                return (
                    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(
                        info.context
                    )
                    .load_many(map_shipping_method_and_channel)
                    .then(apply_price_to_shipping_method)
                )

            return (
                ShippingMethodByIdLoader(info.context)
                .load_many(available_ids)
                .then(map_shipping_method_with_channel)
            )

        channel = ChannelByIdLoader(info.context).load(root.channel_id)
        address = (
            AddressByIdLoader(info.context).load(root.shipping_address_id)
            if root.shipping_address_id
            else None
        )
        lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return Promise.all([address, lines, discounts, channel]).then(
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
