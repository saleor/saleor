from decimal import Decimal
from typing import List, Union

import graphene
from promise import Promise

from ....checkout import base_calculations
from ....checkout.models import Checkout, CheckoutLine
from ....core.prices import quantize_price
from ....core.taxes import include_taxes_in_prices, zero_money
from ....discount import VoucherType
from ....order.models import Order, OrderLine
from ....shipping.models import ShippingMethodChannelListing
from ...account.dataloaders import AddressByIdLoader
from ...channel.dataloaders import ChannelByIdLoader
from ...channel.types import Channel
from ...checkout import types as checkout_types
from ...checkout.dataloaders import (
    CheckoutByTokenLoader,
    CheckoutInfoByCheckoutTokenLoader,
    CheckoutLinesByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
)
from ...discount.dataloaders import (
    DiscountsByDateTimeLoader,
    OrderDiscountsByOrderIDLoader,
)
from ...order import types as order_types
from ...order.dataloaders import OrderLinesByOrderIdLoader
from ...product.dataloaders.products import (
    ProductByVariantIdLoader,
    ProductVariantByIdLoader,
)
from ...shipping.dataloaders import ShippingMethodChannelListingByShippingMethodIdLoader
from .common import NonNullList
from .money import Money


class TaxSourceObject(graphene.Union):
    class Meta:
        types = (checkout_types.Checkout, order_types.Order)

    @classmethod
    def resolve_type(cls, instance, info):
        if isinstance(instance, Checkout):
            return checkout_types.Checkout
        if isinstance(instance, Order):
            return order_types.Order
        return super(TaxSourceObject, cls).resolve_type(instance, info)


class TaxSourceLine(graphene.Union):
    class Meta:
        types = (checkout_types.CheckoutLine, order_types.OrderLine)

    @classmethod
    def resolve_type(cls, instance, info):
        if isinstance(instance, CheckoutLine):
            return checkout_types.CheckoutLine
        if isinstance(instance, OrderLine):
            return order_types.OrderLine
        return super(TaxSourceObject, cls).resolve_type(instance, info)


class TaxableObjectLine(graphene.ObjectType):
    source_line = graphene.Field(
        TaxSourceLine,
        required=True,
        description="The source line related to this tax line.",
    )
    quantity = graphene.Int(required=True, description="Number of items.")
    charge_taxes = graphene.Boolean(
        required=True,
        description="Determines if taxes are being charged for the product.",
    )
    product_name = graphene.String(description="The product name.", required=True)
    variant_name = graphene.String(description="The variant name.", required=True)
    product_sku = graphene.String(description="The product sku.")

    unit_price = graphene.Field(
        Money, description="Price of the single item in the order line.", required=True
    )
    total_price = graphene.Field(
        Money, description="Price of the order line.", required=True
    )

    @staticmethod
    def resolve_variant_name(root: Union[CheckoutLine, OrderLine], info):
        if isinstance(root, CheckoutLine):

            def get_name(variant):
                return variant.name

            if not root.variant_id:
                return ""
            return (
                ProductVariantByIdLoader(info.context)
                .load(root.variant_id)
                .then(get_name)
            )
        return root.variant_name

    @staticmethod
    def resolve_product_name(root: Union[CheckoutLine, OrderLine], info):
        if isinstance(root, CheckoutLine):

            def get_name(product):
                return product.name

            if not root.variant_id:
                return ""
            return (
                ProductByVariantIdLoader(info.context)
                .load(root.variant_id)
                .then(get_name)
            )
        return root.product_name

    @staticmethod
    def resolve_product_sku(root: Union[CheckoutLine, OrderLine], info):
        if isinstance(root, CheckoutLine):
            if not root.variant_id:
                return None

            def get_sku(variant):
                return variant.sku

            return (
                ProductVariantByIdLoader(info.context)
                .load(root.variant_id)
                .then(get_sku)
            )
        return root.product_sku

    @staticmethod
    def resolve_source_line(root: Union[CheckoutLine, OrderLine], info):
        return root

    @staticmethod
    def resolve_charge_taxes(root: Union[CheckoutLine, OrderLine], info):

        if not root.variant_id:
            # By default charge taxes are set to True
            return True

        def get_charge_taxes(product):
            return product.charge_taxes

        return (
            ProductByVariantIdLoader(info.context)
            .load(root.variant_id)
            .then(get_charge_taxes)
        )

    @staticmethod
    def resolve_unit_price(root: Union[CheckoutLine, OrderLine], info):
        if isinstance(root, CheckoutLine):

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
                            return base_calculations.calculate_base_line_unit_price(
                                line_info=line_info,
                                channel=checkout_info.channel,
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
        return root.base_unit_price

    @staticmethod
    def resolve_total_price(root: Union[CheckoutLine, OrderLine], info):
        if isinstance(root, CheckoutLine):

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
                            return base_calculations.calculate_base_line_total_price(
                                line_info=line_info,
                                channel=checkout_info.channel,
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
        return root.base_unit_price * root.quantity


class TaxableObjectDiscount(graphene.ObjectType):
    name = graphene.String(description="The name of the discount.")
    amount = graphene.Field(
        Money, description="The amount of the discount.", required=True
    )

    class Meta:
        description = "Taxable object discount."


class TaxableObject(graphene.ObjectType):
    source_object = graphene.Field(
        TaxSourceObject,
        required=True,
        description="The source object related to this tax object.",
    )
    prices_entered_with_tax = graphene.Boolean(
        required=True, description="Determines if prices contain entered tax.."
    )
    currency = graphene.String(required=True, description="The currency of the object.")
    shipping_price = graphene.Field(
        Money, required=True, description="The price of shipping method."
    )
    address = graphene.Field(
        "saleor.graphql.account.types.Address",
        description="The address data.",
    )
    discounts = NonNullList(
        TaxableObjectDiscount, description="List of discounts.", required=True
    )
    lines = NonNullList(
        TaxableObjectLine,
        description="List of lines assigned to the object.",
        required=True,
    )
    channel = graphene.Field(Channel, required=True)

    class Meta:
        description = "Taxable object."

    @staticmethod
    def resolve_channel(root: Union[Checkout, Order], info):
        return ChannelByIdLoader(info.context).load(root.channel_id)

    @staticmethod
    def resolve_address(root: Union[Checkout, Order], info):
        address_id = root.shipping_address_id or root.billing_address_id
        if not address_id:
            return None
        return AddressByIdLoader(info.context).load(address_id)

    @staticmethod
    def resolve_source_object(root: Union[Checkout, Order], info):
        return root

    @staticmethod
    def resolve_prices_entered_with_tax(root: Union[Checkout, Order], info):
        return include_taxes_in_prices()

    @staticmethod
    def resolve_currency(root: Union[Checkout, Order], info):
        return root.currency

    @staticmethod
    def resolve_shipping_price(root: Union[Checkout, Order], info):
        if isinstance(root, Checkout):

            def calculate_shipping_price(data):
                checkout_info, lines = data
                is_shipping_voucher = (
                    checkout_info.voucher.type == VoucherType.SHIPPING
                    if checkout_info.voucher
                    else False
                )
                price = base_calculations.base_checkout_delivery_price(
                    checkout_info, lines
                )
                if is_shipping_voucher:
                    price.amount = max(
                        price.amount - checkout_info.checkout.discount_amount,
                        Decimal("0.0"),
                    )

                return quantize_price(
                    price,
                    checkout_info.checkout.currency,
                )

            checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(
                root.token
            )
            lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(
                root.token
            )
            return Promise.all(
                [
                    checkout_info,
                    lines,
                ]
            ).then(calculate_shipping_price)

        def calculate_base_shipping_method(
            channel_listins: List[ShippingMethodChannelListing],
        ):
            for listing in channel_listins:
                if listing.channel_id == root.channel_id:
                    return listing.price
            return zero_money(root.currency)

        if not root.shipping_method:
            return zero_money(root.currency)

        return (
            ShippingMethodChannelListingByShippingMethodIdLoader(info.context)
            .load(root.shipping_method_id)
            .then(calculate_base_shipping_method)
        )

    @staticmethod
    def resolve_discounts(root: Union[Checkout, Order], info):
        if isinstance(root, Checkout):

            def calculate_checkout_discounts(checkout_info):
                is_shipping_voucher = (
                    checkout_info.voucher.type == VoucherType.SHIPPING
                    if checkout_info.voucher
                    else False
                )
                checkout = checkout_info.checkout
                discount_name = checkout.discount_name
                return (
                    [{"name": discount_name, "amount": checkout.discount}]
                    if checkout.discount and not is_shipping_voucher
                    else []
                )

            return (
                CheckoutInfoByCheckoutTokenLoader(info.context)
                .load(root.token)
                .then(calculate_checkout_discounts)
            )

        def map_discounts(discounts):
            return [
                {"name": discount.name, "amount": discount.amount}
                for discount in discounts
            ]

        return (
            OrderDiscountsByOrderIDLoader(info.context)
            .load(root.id)
            .then(map_discounts)
        )

    @staticmethod
    def resolve_lines(root: Union[Checkout, Order], info):
        if isinstance(root, Checkout):
            return CheckoutLinesByCheckoutTokenLoader(info.context).load(root.token)
        return OrderLinesByOrderIdLoader(info.context).load(root.id)
