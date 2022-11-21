from functools import partial
from typing import Union

import graphene
from promise import Promise

from ....checkout import base_calculations
from ....checkout.models import Checkout, CheckoutLine
from ....core.prices import quantize_price
from ....discount import VoucherType
from ....order.models import Order, OrderLine
from ....order.utils import get_order_country
from ....tax.utils import get_charge_taxes
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
from ...order.dataloaders import OrderByIdLoader, OrderLinesByOrderIdLoader
from ...product.dataloaders.products import (
    ProductByVariantIdLoader,
    ProductVariantByIdLoader,
)
from ...tax.dataloaders import (
    TaxConfigurationByChannelId,
    TaxConfigurationPerCountryByTaxConfigurationIDLoader,
)
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
        def load_tax_configuration(channel, country_code):
            tax_config = TaxConfigurationByChannelId(info.context).load(channel.pk)

            def load_tax_country_exceptions(tax_config):
                tax_configs_per_country = (
                    TaxConfigurationPerCountryByTaxConfigurationIDLoader(
                        info.context
                    ).load(tax_config.id)
                )

                def calculate_charge_taxes(tax_configs_per_country):
                    tax_config_country = next(
                        (
                            tc
                            for tc in tax_configs_per_country
                            if tc.country.code == country_code
                        ),
                        None,
                    )
                    return get_charge_taxes(tax_config, tax_config_country)

                return tax_configs_per_country.then(calculate_charge_taxes)

            return tax_config.then(load_tax_country_exceptions)

        if isinstance(root, CheckoutLine):
            checkout = CheckoutByTokenLoader(info.context).load(root.checkout_id)

            def load_channel(checkout):
                country_code = checkout.get_country()
                load_tax_config_with_country = partial(
                    load_tax_configuration, country_code=country_code
                )
                return (
                    ChannelByIdLoader(info.context)
                    .load(checkout.channel_id)
                    .then(load_tax_config_with_country)
                )

            return checkout.then(load_channel)
        else:
            order = OrderByIdLoader(info.context).load(root.order_id)

            def load_channel(order):  # type: ignore
                country_code = get_order_country(order)
                load_tax_config_with_country = partial(
                    load_tax_configuration, country_code=country_code
                )
                return (
                    ChannelByIdLoader(info.context)
                    .load(order.channel_id)
                    .then(load_tax_config_with_country)
                )

            return order.then(load_channel)

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
        tax_config = TaxConfigurationByChannelId(info.context).load(root.channel_id)
        return tax_config.then(lambda tc: tc.prices_entered_with_tax)

    @staticmethod
    def resolve_currency(root: Union[Checkout, Order], info):
        return root.currency

    @staticmethod
    def resolve_shipping_price(root: Union[Checkout, Order], info):
        if isinstance(root, Checkout):

            def calculate_shipping_price(data):
                checkout_info, lines = data
                price = base_calculations.base_checkout_delivery_price(
                    checkout_info, lines
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

        return root.base_shipping_price

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
