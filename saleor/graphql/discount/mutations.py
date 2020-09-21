from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Dict, List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ...core.permissions import DiscountPermissions
from ...core.utils.promo_code import generate_promo_code, is_available_promo_code
from ...discount import DiscountValueType, models
from ...discount.error_codes import DiscountErrorCode
from ...discount.models import SaleChannelListing
from ...product.tasks import (
    update_products_discounted_prices_of_catalogues_task,
    update_products_discounted_prices_of_discount_task,
)
from ...product.utils import get_products_ids_without_variants
from ..channel import ChannelContext
from ..channel.mutations import BaseChannelListingMutation
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.scalars import PositiveDecimal
from ..core.types.common import DiscountError
from ..core.validators import validate_price_precision
from ..product.types import Category, Collection, Product
from .enums import DiscountValueTypeEnum, VoucherTypeEnum
from .types import Sale, Voucher

if TYPE_CHECKING:
    from ...discount.models import Sale as SaleModel

ErrorType = DefaultDict[str, List[ValidationError]]


class CatalogueInput(graphene.InputObjectType):
    products = graphene.List(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    categories = graphene.List(
        graphene.ID,
        description="Categories related to the discount.",
        name="categories",
    )
    collections = graphene.List(
        graphene.ID,
        description="Collections related to the discount.",
        name="collections",
    )


class BaseDiscountCatalogueMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def recalculate_discounted_prices(cls, products, categories, collections):
        update_products_discounted_prices_of_catalogues_task.delay(
            product_ids=[p.pk for p in products],
            category_ids=[c.pk for c in categories],
            collection_ids=[c.pk for c in collections],
        )

    @classmethod
    def add_catalogues_to_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
            cls.clean_product(products)
            node.products.add(*products)
        categories = input.get("categories", [])
        if categories:
            categories = cls.get_nodes_or_error(categories, "categories", Category)
            node.categories.add(*categories)
        collections = input.get("collections", [])
        if collections:
            collections = cls.get_nodes_or_error(collections, "collections", Collection)
            node.collections.add(*collections)
        # Updated the db entries, recalculating discounts of affected products
        cls.recalculate_discounted_prices(products, categories, collections)

    @classmethod
    def clean_product(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT,
                        params={"products": products_ids_without_variants},
                    )
                }
            )

    @classmethod
    def remove_catalogues_from_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
            node.products.remove(*products)
        categories = input.get("categories", [])
        if categories:
            categories = cls.get_nodes_or_error(categories, "categories", Category)
            node.categories.remove(*categories)
        collections = input.get("collections", [])
        if collections:
            collections = cls.get_nodes_or_error(collections, "collections", Collection)
            node.collections.remove(*collections)
        # Updated the db entries, recalculating discounts of affected products
        cls.recalculate_discounted_prices(products, categories, collections)


class VoucherInput(graphene.InputObjectType):
    type = VoucherTypeEnum(
        description=("Voucher type: PRODUCT, CATEGORY SHIPPING or ENTIRE_ORDER.")
    )
    name = graphene.String(description="Voucher name.")
    code = graphene.String(description="Code to use the voucher.")
    start_date = graphene.types.datetime.DateTime(
        description="Start date of the voucher in ISO 8601 format."
    )
    end_date = graphene.types.datetime.DateTime(
        description="End date of the voucher in ISO 8601 format."
    )
    discount_value_type = DiscountValueTypeEnum(
        description="Choices: fixed or percentage."
    )
    discount_value = PositiveDecimal(description="Value of the voucher.")
    products = graphene.List(
        graphene.ID, description="Products discounted by the voucher.", name="products"
    )
    collections = graphene.List(
        graphene.ID,
        description="Collections discounted by the voucher.",
        name="collections",
    )
    categories = graphene.List(
        graphene.ID,
        description="Categories discounted by the voucher.",
        name="categories",
    )
    min_amount_spent = PositiveDecimal(
        description="Min purchase amount required to apply the voucher."
    )
    min_checkout_items_quantity = graphene.Int(
        description="Minimal quantity of checkout items required to apply the voucher."
    )
    countries = graphene.List(
        graphene.String,
        description="Country codes that can be used with the shipping voucher.",
    )
    apply_once_per_order = graphene.Boolean(
        description="Voucher should be applied to the cheapest item or entire order."
    )
    apply_once_per_customer = graphene.Boolean(
        description="Voucher should be applied once per customer."
    )
    usage_limit = graphene.Int(
        description="Limit number of times this voucher can be used in total."
    )


class VoucherCreate(ModelMutation):
    class Arguments:
        input = VoucherInput(
            required=True, description="Fields required to create a voucher."
        )

    class Meta:
        description = "Creates a new voucher."
        model = models.Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        code = data.get("code", None)
        if code == "":
            data["code"] = generate_promo_code()
        elif not is_available_promo_code(code):
            raise ValidationError(
                {
                    "code": ValidationError(
                        "Promo code already exists.",
                        code=DiscountErrorCode.ALREADY_EXISTS,
                    )
                }
            )
        cleaned_input = super().clean_input(info, instance, data)

        min_spent_amount = cleaned_input.pop("min_amount_spent", None)
        if min_spent_amount is not None:
            try:
                validate_price_precision(min_spent_amount, instance.currency)
            except ValidationError as error:
                error.code = DiscountErrorCode.INVALID.value
                raise ValidationError({"min_spent_amount": error})
            cleaned_input["min_spent_amount"] = min_spent_amount
        return cleaned_input


class VoucherUpdate(VoucherCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to update.")
        input = VoucherInput(
            required=True, description="Fields required to update a voucher."
        )

    class Meta:
        description = "Updates a voucher."
        model = models.Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"


class VoucherDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to delete.")

    class Meta:
        description = "Deletes a voucher."
        model = models.Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"


class VoucherBaseCatalogueMutation(BaseDiscountCatalogueMutation):
    voucher = graphene.Field(
        Voucher, description="Voucher of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher.")
        input = CatalogueInput(
            required=True,
            description=("Fields required to modify catalogue IDs of voucher."),
        )

    class Meta:
        abstract = True


class VoucherAddCatalogues(VoucherBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        voucher = cls.get_node_or_error(
            info, data.get("id"), only_type=Voucher, field="voucher_id"
        )
        cls.add_catalogues_to_node(voucher, data.get("input"))
        return VoucherAddCatalogues(voucher=voucher)


class VoucherRemoveCatalogues(VoucherBaseCatalogueMutation):
    class Meta:
        description = "Removes products, categories, collections from a voucher."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        voucher = cls.get_node_or_error(
            info, data.get("id"), only_type=Voucher, field="voucher_id"
        )
        cls.remove_catalogues_from_node(voucher, data.get("input"))
        return VoucherRemoveCatalogues(voucher=voucher)


class SaleInput(graphene.InputObjectType):
    name = graphene.String(description="Voucher name.")
    type = DiscountValueTypeEnum(description="Fixed or percentage.")
    value = PositiveDecimal(description="Value of the voucher.")
    products = graphene.List(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    categories = graphene.List(
        graphene.ID,
        description="Categories related to the discount.",
        name="categories",
    )
    collections = graphene.List(
        graphene.ID,
        description="Collections related to the discount.",
        name="collections",
    )
    start_date = graphene.types.datetime.DateTime(
        description="Start date of the voucher in ISO 8601 format."
    )
    end_date = graphene.types.datetime.DateTime(
        description="End date of the voucher in ISO 8601 format."
    )


class SaleUpdateDiscountedPriceMixin:
    @classmethod
    def success_response(cls, instance):
        # Update the "discounted_prices" of the associated, discounted
        # products (including collections and categories).
        update_products_discounted_prices_of_discount_task.delay(instance.pk)
        return super().success_response(
            ChannelContext(node=instance, channel_slug=None)
        )


class SaleCreate(SaleUpdateDiscountedPriceMixin, ModelMutation):
    class Arguments:
        input = SaleInput(
            required=True, description="Fields required to create a sale."
        )

    class Meta:
        description = "Creates a new sale."
        model = models.Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"


class SaleUpdate(SaleUpdateDiscountedPriceMixin, ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleInput(
            required=True, description="Fields required to update a sale."
        )

    class Meta:
        description = "Updates a sale."
        model = models.Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"


class SaleDelete(SaleUpdateDiscountedPriceMixin, ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to delete.")

    class Meta:
        description = "Deletes a sale."
        model = models.Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"


class SaleBaseCatalogueMutation(BaseDiscountCatalogueMutation):
    sale = graphene.Field(
        Sale, description="Sale of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale.")
        input = CatalogueInput(
            required=True,
            description="Fields required to modify catalogue IDs of sale.",
        )

    class Meta:
        abstract = True


class SaleAddCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        sale = cls.get_node_or_error(
            info, data.get("id"), only_type=Sale, field="sale_id"
        )
        cls.add_catalogues_to_node(sale, data.get("input"))
        return SaleAddCatalogues(sale=ChannelContext(node=sale, channel_slug=None))


class SaleRemoveCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = "Removes products, categories, collections from a sale."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        sale = cls.get_node_or_error(
            info, data.get("id"), only_type=Sale, field="sale_id"
        )
        cls.remove_catalogues_from_node(sale, data.get("input"))
        return SaleRemoveCatalogues(sale=ChannelContext(node=sale, channel_slug=None))


class SaleChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    discount_value = PositiveDecimal(
        required=True, description="The value of the discount."
    )


class SaleChannelListingInput(graphene.InputObjectType):
    add_channels = graphene.List(
        graphene.NonNull(SaleChannelListingAddInput),
        description="List of channels to which the sale should be assigned.",
        required=False,
    )
    remove_channels = graphene.List(
        graphene.NonNull(graphene.ID),
        description=("List of channels from which the sale should be unassigned."),
        required=False,
    )


class SaleChannelListingUpdate(BaseChannelListingMutation):
    sale = graphene.Field(Sale, description="An updated sale instance.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleChannelListingInput(
            required=True,
            description="Fields required to update sale channel listings.",
        )

    class Meta:
        description = "Manage sale's availability in channels."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def add_channels(cls, sale: "SaleModel", add_channels: List[Dict]):
        for add_channel in add_channels:
            defaults = {}
            discount_value = add_channel.get("discount_value")
            channel = add_channel["channel"]
            currency_code = channel.currency_code
            if discount_value:
                defaults["discount_value"] = discount_value
            SaleChannelListing.objects.update_or_create(
                sale=sale, channel=channel, currency=currency_code, defaults=defaults,
            )

    @classmethod
    def clean_prices(cls, cleaned_channels, sale_type, errors, error_code):
        if sale_type != DiscountValueType.FIXED:
            return cleaned_channels

        invalid_channels_ids = []
        error_message = None
        for cleaned_channel in cleaned_channels.get("add_channels", []):
            channel = cleaned_channel["channel"]
            currency_code = channel.currency_code
            discount_value = cleaned_channel.get("discount_value")
            if discount_value:
                try:
                    validate_price_precision(discount_value, currency_code)
                except ValidationError as error:
                    error_message = error.message
                    invalid_channels_ids.append(cleaned_channel["channel_id"])
        if invalid_channels_ids and error_message:
            errors["input"].append(
                ValidationError(
                    error_message,
                    code=error_code,
                    params={"channels": invalid_channels_ids},
                )
            )
        return cleaned_channels

    @classmethod
    def remove_channels(cls, sale: "SaleModel", remove_channels: List[int]):
        sale.channel_listing.filter(channel_id__in=remove_channels).delete()

    @classmethod
    @transaction.atomic()
    def save(cls, info, sale: "SaleModel", cleaned_input: Dict):
        cls.add_channels(sale, cleaned_input.get("add_channels", []))
        cls.remove_channels(sale, cleaned_input.get("remove_channels", []))
        update_products_discounted_prices_of_discount_task.delay(sale.pk)

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        sale = cls.get_node_or_error(info, id, only_type=Sale, field="id")
        errors = defaultdict(list)
        cleaned_channels = cls.clean_channels(
            info, input, errors, DiscountErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        cleaned_input = cls.clean_prices(
            cleaned_channels, sale.type, errors, DiscountErrorCode.INVALID.value
        )

        if errors:
            raise ValidationError(errors)

        cls.save(info, sale, cleaned_input)
        return SaleChannelListingUpdate(
            sale=ChannelContext(node=sale, channel_slug=None)
        )
