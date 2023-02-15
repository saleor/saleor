from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Tuple, Any

import graphene

from ...account.i18n import I18nMixin
from ...core.utils import from_global_id_or_none
from ....account.models import User
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus
from ....order.models import Order, OrderLine
from ....permission.enums import OrderPermissions
from ...account.types import AddressInput
from ...core import ResolveInfo
from ...core.enums import ErrorPolicyEnum, LanguageCodeEnum
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal, WeightScalar
from ...core.types import NonNullList
from ...core.types.common import OrderBulkCreateError
from ...meta.mutations import MetadataInput
from ..mutations.order_discount_common import OrderDiscountCommonInput
from ..types import Order as OrderType
from ....product.models import ProductVariant
from ....shipping.models import ShippingMethod
from ....tax.models import TaxClass
from ....warehouse.models import Warehouse


@dataclass
class OrderBulkErrorDataclass:
    order: str
    field: str
    message: str


@dataclass
class TaxedMoneyDataclass:
    # add slots to dataclasses
    gross: Decimal
    net: Decimal
    currency: str


@dataclass
class NoteInputDataclass:
    message: str
    date: Optional[datetime]
    user_id: Optional[str]
    app_id: Optional[str]


@dataclass
class UserInputDataclass:
    id: Optional[str]
    email: Optional[str]
    external_reference: Optional[str]


@dataclass
class DeliveryMethodInputDataclass:
    warehouse_id: Optional[str]
    warehouse_name: Optional[str]
    shipping_method_id: Optional[str]
    shipping_method_name: Optional[str]
    shipping_price = Optional[TaxedMoneyDataclass]
    shipping_tax_rate: Decimal
    shipping_tax_class_id: Optional[str]
    shipping_tax_class_name: Optional[str]
    shipping_tax_class_metadata: Optional[List[Dict[str, str]]]
    shipping_tax_class_private_metadata: Optional[List[Dict[str, str]]]


@dataclass
class OrderLineInputDataclass:
    variant_id: Optional[str]
    variant_sku: Optional[str]
    variant_external_reference: Optional[str]
    variant_name: Optional[str]
    product_name: Optional[str]
    translated_variant_name: Optional[str]
    translated_product_name: Optional[str]
    created_at: datetime
    is_shipping_required: bool
    is_gift_card: bool
    quantity: int
    quantity_fulfilled: int
    total_price: TaxedMoneyDataclass
    undiscounted_total_price: TaxedMoneyDataclass
    tax_rate: Decimal
    tax_class_id: Optional[str]
    tax_class_name: Optional[str]
    tax_class_metadata = Optional[List[Dict[str, str]]]
    tax_class_private_metadata = Optional[List[Dict[str, str]]]


@dataclass
class AddressInputDataclass:
    first_name: Optional[str]
    last_name: Optional[str]
    company_name: Optional[str]
    street_address_1: Optional[str]
    street_address_2: Optional[str]
    city: Optional[str]
    city_area: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    country_area: Optional[str]
    phone: Optional[str]


@dataclass
class OrderInputDataclass:
    number: Optional[str]
    external_reference: Optional[str]
    channel: str
    created_at: datetime
    status: OrderStatus
    user: UserInputDataclass
    tracking_client_id: Optional[str]
    billing_address = AddressInputDataclass
    shipping_address = Optional[AddressInputDataclass]
    delivery_method: DeliveryMethodInputDataclass
    metadata = Optional[List[Dict[str, str]]]
    private_metadata = Optional[List[Dict[str, str]]]
    customer_note: Optional[str]
    notes = Optional[List[NoteInputDataclass]]
    language_code: Optional[str]
    display_gross_prices: bool
    redirect_url: Optional[str]
    lines = List[OrderLineInputDataclass]
    promo_codes: Optional[str]
    # TODO weight = WeightScalar(description="Weight of the order.")
    # TODO discounts = NonNullList(OrderDiscountCommonInput, description="List of discounts.")
    # TODO invoices = [OrderBulkCreateInvoiceInput!]
    # TODO transactions: [TransactionCreateInput!]!
    # TODO fulfillments: [OrderBulkCreateFulfillmentInput!]


class TaxedMoneyInput(graphene.InputObjectType):
    gross = PositiveDecimal(required=True, description="Gross value of an item.")
    net = PositiveDecimal(required=True, description="Net value of an item.")
    currency = graphene.String(required=True, description="Currency code.")


class OrderBulkCreateUserInput(graphene.InputObjectType):
    id = graphene.ID(description="Customer ID associated with the order.")
    email = graphene.String(description="Customer email associated with the order.")
    external_reference = graphene.String(
        description="Customer external ID associated with the order."
    )


class OrderBulkCreateDeliveryMethodInput(graphene.InputObjectType):
    warehouse_id = graphene.ID(description="The ID of the warehouse.")
    warehouse_name = graphene.String(description="The name of the warehouse.")
    shipping_method_id = graphene.ID(description="The ID of the shipping method.")
    shipping_method_name = graphene.String(
        description="The name of the shipping method."
    )
    shipping_price = graphene.Field(
        TaxedMoneyInput, description="The price of the shipping."
    )
    shipping_tax_rate = graphene.Float(
        required=True, description="Tax rate of the shipping."
    )
    shipping_tax_class_id = graphene.ID(description="The ID of the tax class.")
    shipping_tax_class_name = graphene.String(description="The name of the tax class.")
    shipping_tax_class_metadata = NonNullList(
        MetadataInput, description="Metadata of the tax class."
    )
    shipping_tax_class_private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the tax class."
    )


class OrderBulkCreateNoteInput(graphene.InputObjectType):
    message = graphene.String(required=True, description="Note message.")
    date = graphene.DateTime(description="The date associated with the message.")
    user_id = graphene.ID(description="The user ID associated with the message.")
    app_id = graphene.ID(description="The app ID associated with the message.")


class OrderBulkCreateOrderLineInput(graphene.InputObjectType):
    variant_id = graphene.ID(description="The ID of the product variant.")
    variant_sku = graphene.String(description="The sku of the product variant.")
    variant_external_reference = graphene.String(
        description="The external ID of the product variant."
    )
    variant_name = graphene.String(description="The name of the product variant.")
    product_name = graphene.String(description="The name of the product.")
    translated_variant_name = graphene.String(
        description="Translation of the product variant name."
    )
    translated_product_name = graphene.String(
        description="Translation of the product name."
    )
    created_at = graphene.DateTime(
        required=True, description="The date, when the order line was created."
    )
    is_shipping_required = graphene.Boolean(
        required=True,
        description="Determines whether shipping of the order line items is required.",
    )
    is_gift_card = graphene.Boolean(required=True, description="Gift card flag.")
    quantity = graphene.Int(
        required=True, description="Number of items in the order line"
    )
    quantity_fulfilled = graphene.Int(
        required=True,
        description="Number of items in the order line, "
        "which have been already fulfilled.",
    )
    total_price = graphene.Field(
        TaxedMoneyInput, required=True, description="Price of the order line."
    )
    undiscounted_total_price = graphene.Field(
        TaxedMoneyInput,
        required=True,
        description="Price of the order line excluding applied discount.",
    )
    tax_rate = graphene.Float(required=True, description="Tax rate of the order line.")
    tax_class_id = graphene.ID(description="The ID of the tax class.")
    tax_class_name = graphene.String(description="The name of the tax class.")
    tax_class_metadata = NonNullList(
        MetadataInput, description="Metadata of the tax class."
    )
    tax_class_private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the tax class."
    )


class OrderBulkCreateInput(graphene.InputObjectType):
    number = graphene.String(description="Unique identifier of the order.")
    external_reference = graphene.String(description="External ID of the order.")
    channel = graphene.String(
        required=True, description="Slug of the channel associated with the order."
    )
    created_at = graphene.DateTime(
        required=True,
        description="The date, when the order was inserted to Saleor database.",
    )
    status = graphene.String(description="Status of the order.")
    user = graphene.Field(
        OrderBulkCreateUserInput,
        required=True,
        description="Customer accociated with the order.",
    )
    tracking_client_id = graphene.String(description="Tracking ID of the customer.")
    billing_address = graphene.Field(
        AddressInput, required=True, description="Billing address of the customer."
    )
    shipping_address = graphene.Field(
        AddressInput, description="Shipping address of the customer."
    )
    metadata = NonNullList(MetadataInput, description="Metadata of the order.")
    private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the order."
    )
    customer_note = graphene.String(description="Note about customer.")
    notes = NonNullList(
        OrderBulkCreateNoteInput,
        description="Notes related to the order.",
    )
    language_code = graphene.Argument(
        LanguageCodeEnum, required=True, description="Order language code."
    )
    display_gross_prices = graphene.Boolean(
        requierd=True,
        description="Determines whether checkout prices should include taxes, "
        "when displayed in a storefront.",
    )
    weight = WeightScalar(description="Weight of the order.")
    redirect_url = graphene.String(
        description="URL of a view, where users should be redirected "
        "to see the order details.",
    )
    lines = NonNullList(
        OrderBulkCreateOrderLineInput, required=True, description="List of order lines."
    )
    delivery_method = graphene.Field(
        OrderBulkCreateDeliveryMethodInput,
        required=True,
        description="The delivery method selected for this order.",
    )
    promo_codes = NonNullList(graphene.String, description="List of promo codes.")
    discounts = NonNullList(OrderDiscountCommonInput, description="List of discounts.")
    # TODO invoices = [OrderBulkCreateInvoiceInput!]
    # TODO transactions: [TransactionCreateInput!]!
    # TODO fulfillments: [OrderBulkCreateFulfillmentInput!]


class OrderBulkCreateResult(graphene.ObjectType):
    order = graphene.Field(OrderType, required=True, description="Order data.")
    errors = NonNullList(
        OrderBulkCreateError,
        description="List of errors occurred on create attempt.",
    )


class OrderBulkCreate(BaseMutation, I18nMixin):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were created.",
    )
    results = NonNullList(
        OrderBulkCreateResult,
        required=True,
        default_value=[],
        description="List of the created orders.",
    )

    class Arguments:
        orders = NonNullList(
            OrderBulkCreateInput,
            required=True,
            description="Input list of orders to create.",
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.value,
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
            ),
        )

    class Meta:
        description = "Creates multiple orders."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderBulkCreateError
        error_type_field = "bulk_order_errors"

    @classmethod
    def get_instance(cls, input: Dict[str, Any], model, key_map: Dict[str, str]):
        """Resolve instance based on data, model and `key_map` argument provided.

        `input`: data from input
        `key_map`: mapping between keys from data and keys from database
        `model`: database model associated with searched instance
        """
        # TODO replace model with query set if additional filters needed
        if sum((input.get(key) is not None for key in key_map.keys())) > 1:
            # TODO error
            i = 1
            return

        for data_key, db_key in key_map.items():
            if input.get(data_key) and isinstance(input.get(data_key), str):
                if db_key == "id":
                    id = from_global_id_or_none(input.get(data_key), model.__name__)
                    if not id:
                        # TODO error
                        break
                    else:
                        input[data_key] = id

                return model.objects.filter(**{db_key: input.get(data_key)}).first()

        # TODO error if data.get(data_key) didn't return any not None
        # TODO error if there is no instance
        return

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /, **data):
        assert True
        # validate input
        # prepare order instances
        # consider error policy
        # save orders
        # post save actions
        order_input = data["orders"][0]
        user = cls.get_instance(
            input=order_input["user"],
            model=User,
            key_map={
                "id": "id",
                "email": "email",
                "external_reference": "external_reference"
            },
        )
        # TODO check if zones etc needed
        warehouse = cls.get_instance(
            input=order_input["delivery_method"],
            model=Warehouse,
            key_map={
                "warehouse_id": "id",
                "warehouse_name": "name",
            },
        )
        # TODO check if zones etc needed
        shipping_method = cls.get_instance(
            input=order_input["delivery_method"],
            model=ShippingMethod,
            key_map={
                "shipping_method_id": "id",
                "shipping_method_name": "name",
            },
        )
        # TODO handle tax class metadata
        # TODO check if zones etc needed
        shipping_tax_class = cls.get_instance(
            input=order_input["delivery_method"],
            model=TaxClass,
            key_map={
                "shipping_tax_class_id": "id",
                "shipping_tax_class_name": "name",
            },
        )
        order_line_input = order_input["lines"][0]
        variant: ProductVariant = cls.get_instance(
            input=order_line_input,
            model=ProductVariant,
            key_map={
                "variant_id": "id",
                "variant_name": "name",
                "variant_external_reference": "external_reference",
                "variant_sku": "name",
            },
        )
        # TODO handle tax class metadata
        line_tax_class = cls.get_instance(
            input=order_line_input,
            model=TaxClass,
            key_map={
                "tax_class_id": "id",
                "tax_class_name": "name",
            },
        )

        billing_address_input = order_input["billing_address"]
        try:
            billing_address = cls.validate_address(billing_address_input)
        except Exception as e:
            # TODO error
            print(e)
            pass

        if shipping_address_input := order_input["shipping_address"]:
            try:
                shipping_address = cls.validate_address(shipping_address_input)
            except:
                # TODO error
                pass


        order = Order()

        order_line = OrderLine(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            variant_name=variant.name,
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            quantity=order_line_input["quantity"],
            quantityFulfilled=order_line_input["quantity_fulfilled"],
        )

        order.number = order_input.get("number")
        order.external_reference = order_input.get("external_reference")
        order.channel = order_input.get("channel")
        order.created_at = order_input.get("created_at")
        order.status = order_input.get("status")
        order.user = user
        order.billing_address = billing_address if billing_address else None
        order.shipping_address = shipping_address if shipping_method else None
        order.language_code = order_input.get("language_code")
        order.display_gross_prices = order_input.get("display_gross_prices")
        order

        order.save()



        breakpoint()







