import graphene
import graphene_django_optimizer as gql_optimizer
from django.conf import settings

from ...checkout import models
from ...core.taxes import ZERO_TAXED_MONEY
from ...core.taxes.interface import (
    calculate_checkout_line_total,
    calculate_checkout_shipping,
    calculate_checkout_subtotal,
    calculate_checkout_total,
)
from ..core.connection import CountableDjangoObjectType
from ..core.types.money import TaxedMoney
from ..giftcard.types import GiftCard
from ..order.utils import applicable_shipping_methods
from ..payment.enums import PaymentGatewayEnum
from ..shipping.types import ShippingMethod


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
    def resolve_total_price(self, info):
        return calculate_checkout_line_total(
            checkout_line=self, discounts=info.context.discounts
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
        PaymentGatewayEnum,
        description="List of available payment gateways.",
        required=True,
    )
    email = graphene.String(description="Email of a customer", required=True)
    gift_cards = gql_optimizer.field(
        graphene.List(
            GiftCard, description="List of gift cards associated with this checkout"
        ),
        model_field="gift_cards",
    )
    is_shipping_required = graphene.Boolean(
        description="Returns True, if checkout requires shipping.", required=True
    )
    lines = gql_optimizer.field(
        graphene.List(
            CheckoutLine,
            description=(
                "A list of checkout lines, each containing information about "
                "an item in the checkout."
            ),
        ),
        model_field="lines",
    )
    shipping_price = graphene.Field(
        TaxedMoney,
        description="The price of the shipping, with all the taxes included.",
    )
    subtotal_price = graphene.Field(
        TaxedMoney,
        description="The price of the checkout before shipping, with taxes included.",
    )
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
            "discount_amount",
            "discount_name",
            "gift_cards",
            "is_shipping_required",
            "last_change",
            "note",
            "quantity",
            "shipping_address",
            "shipping_method",
            "token",
            "translated_discount_name",
            "user",
            "voucher_code",
        ]
        description = "Checkout object"
        model = models.Checkout
        interfaces = [graphene.relay.Node]
        filter_fields = ["token"]

    @staticmethod
    def resolve_total_price(root: models.Checkout, info):
        taxed_total = (
            calculate_checkout_total(checkout=root, discounts=info.context.discounts)
            - root.get_total_gift_cards_balance()
        )
        return max(taxed_total, ZERO_TAXED_MONEY)

    @staticmethod
    def resolve_subtotal_price(root: models.Checkout, info):
        return calculate_checkout_subtotal(
            checkout=root, discounts=info.context.discounts
        )

    @staticmethod
    def resolve_shipping_price(root: models.Checkout, info):
        return calculate_checkout_shipping(
            checkout=root, discounts=info.context.discounts
        )

    @staticmethod
    def resolve_lines(root: models.Checkout, *_args):
        return root.lines.prefetch_related("variant")

    @staticmethod
    def resolve_available_shipping_methods(root: models.Checkout, info):
        price = calculate_checkout_subtotal(
            checkout=root, discounts=info.context.discounts
        )
        return applicable_shipping_methods(root, price.gross.amount)

    @staticmethod
    def resolve_available_payment_gateways(_: models.Checkout, _info):
        return settings.CHECKOUT_PAYMENT_GATEWAYS.keys()

    @staticmethod
    def resolve_gift_cards(root: models.Checkout, _info):
        return root.gift_cards.all()

    @staticmethod
    def resolve_is_shipping_required(root: models.Checkout, _info):
        return root.is_shipping_required()
