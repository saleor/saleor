import graphene
from promise import Promise

from ...checkout import calculations, models
from ...checkout.utils import get_valid_shipping_methods_for_checkout
from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions
from ...core.taxes import display_gross_prices, zero_taxed_money
from ...plugins.manager import get_plugins_manager
from ..account.utils import requestor_has_access
from ..channel import ChannelContext
from ..channel.dataloaders import ChannelByCheckoutLineIDLoader, ChannelByIdLoader
from ..core.connection import CountableDjangoObjectType
from ..core.scalars import UUID
from ..core.types.money import TaxedMoney
from ..discount.dataloaders import DiscountsByDateTimeLoader
from ..giftcard.types import GiftCard
from ..meta.types import ObjectWithMetadata
from ..product.resolvers import resolve_variant
from ..shipping.dataloaders import ShippingMethodByIdLoader
from ..shipping.types import ShippingMethod
from ..utils import get_user_or_app_from_context
from .dataloaders import CheckoutLinesByCheckoutTokenLoader


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
        dataloader = ChannelByCheckoutLineIDLoader(info.context)
        return resolve_variant(info, root, dataloader)

    @staticmethod
    def resolve_total_price(root, info):
        context = info.context
        channel = ChannelByCheckoutLineIDLoader(context).load(root.id)

        def calculate_total_price_with_discounts(discounts):
            def calculate_total_price_with_channel(channel):
                return info.context.plugins.calculate_checkout_line_total(
                    checkout_line=root, discounts=discounts, channel=channel,
                )

            return channel.then(calculate_total_price_with_channel)

        return (
            DiscountsByDateTimeLoader(context)
            .load(context.request_time)
            .then(calculate_total_price_with_discounts)
        )

    @staticmethod
    def resolve_requires_shipping(root: models.CheckoutLine, *_args):
        return root.is_shipping_required()


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
        ShippingMethod, description="The shipping method related with checkout.",
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
    def resolve_user(root: models.Checkout, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(requestor, root.user, AccountPermissions.MANAGE_USERS):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_email(root: models.Checkout, info):
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
            lines, discounts = data
            taxed_total = (
                calculations.checkout_total(
                    checkout=root, lines=lines, discounts=discounts
                )
                - root.get_total_gift_cards_balance()
            )
            return max(taxed_total, zero_taxed_money(root.currency))

        lines = CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )

        return Promise.all([lines, discounts]).then(calculate_total_price)

    @staticmethod
    # TODO: We should optimize it in/after PR#5819
    def resolve_subtotal_price(root: models.Checkout, info):
        def calculate_subtotal_price(data):
            lines, discounts = data
            return calculations.checkout_subtotal(
                checkout=root, lines=lines, discounts=discounts
            )

        lines = CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )

        return Promise.all([lines, discounts]).then(calculate_subtotal_price)

    @staticmethod
    # TODO: We should optimize it in/after PR#5819
    def resolve_shipping_price(root: models.Checkout, info):
        def calculate_shipping_price(data):
            lines, discounts = data
            return calculations.checkout_shipping_price(
                checkout=root, lines=lines, discounts=discounts
            )

        lines = CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )

        return Promise.all([lines, discounts]).then(calculate_shipping_price)

    @staticmethod
    # TODO: We should optimize it in/after PR#5819
    def resolve_lines(root: models.Checkout, *_args):
        return root.lines.prefetch_related("variant")

    @staticmethod
    # TODO: We should optimize it in/after PR#5819
    def resolve_available_shipping_methods(root: models.Checkout, info):
        def calculate_available_shipping_methods(data):
            lines, discounts = data
            available = get_valid_shipping_methods_for_checkout(root, lines, discounts)
            if available is None:
                return []
            manager = get_plugins_manager()
            display_gross = display_gross_prices()
            for shipping_method in available:
                # ignore mypy checking because it is checked in
                # get_valid_shipping_methods_for_checkout
                shipping_channel_listing = shipping_method.channel_listings.get(
                    channel=root.channel
                )
                taxed_price = manager.apply_taxes_to_shipping(  # type: ignore
                    shipping_channel_listing.price, root.shipping_address
                )
                if display_gross:
                    shipping_method.price = taxed_price.gross
                else:
                    shipping_method.price = taxed_price.net
            return available

        lines = CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)
        discounts = DiscountsByDateTimeLoader(info.context).load(
            info.context.request_time
        )
        return (
            Promise.all([lines, discounts])
            .then(calculate_available_shipping_methods)
            .then(
                lambda available: [
                    ChannelContext(node=shipping, channel_slug=root.channel.slug)
                    for shipping in available
                ]
            )
        )

    @staticmethod
    def resolve_available_payment_gateways(root: models.Checkout, _info):
        return get_plugins_manager().checkout_available_payment_gateways(checkout=root)

    @staticmethod
    def resolve_gift_cards(root: models.Checkout, _info):
        return root.gift_cards.all()

    @staticmethod
    def resolve_is_shipping_required(root: models.Checkout, _info):
        return root.is_shipping_required()
