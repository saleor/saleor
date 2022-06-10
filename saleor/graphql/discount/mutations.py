from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Dict, List, Set

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ...core.permissions import DiscountPermissions
from ...core.tracing import traced_atomic_transaction
from ...core.utils.promo_code import generate_promo_code, is_available_promo_code
from ...discount import DiscountValueType, models
from ...discount.error_codes import DiscountErrorCode
from ...discount.models import SaleChannelListing
from ...discount.utils import CatalogueInfo, fetch_catalogue_info
from ...product.tasks import (
    update_products_discounted_prices_of_catalogues_task,
    update_products_discounted_prices_of_discount_task,
)
from ...product.utils import get_products_ids_without_variants
from ..channel import ChannelContext
from ..channel.mutations import BaseChannelListingMutation
from ..core.descriptions import ADDED_IN_31
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.scalars import PositiveDecimal
from ..core.types import DiscountError, NonNullList
from ..core.validators import validate_end_is_after_start, validate_price_precision
from ..discount.dataloaders import SaleChannelListingBySaleIdLoader
from ..product.types import Category, Collection, Product, ProductVariant
from .enums import DiscountValueTypeEnum, VoucherTypeEnum
from .types import Sale, Voucher

if TYPE_CHECKING:
    from ...discount.models import Sale as SaleModel

ErrorType = DefaultDict[str, List[ValidationError]]
NodeCatalogueInfo = DefaultDict[str, Set[str]]


def convert_catalogue_info_to_global_ids(
    catalogue_info: CatalogueInfo,
) -> NodeCatalogueInfo:
    catalogue_fields = ["categories", "collections", "products", "variants"]
    type_names = ["Category", "Collection", "Product", "ProductVariant"]
    converted_catalogue_info: NodeCatalogueInfo = defaultdict(set)

    for type_name, catalogue_field in zip(type_names, catalogue_fields):
        converted_catalogue_info[catalogue_field].update(
            graphene.Node.to_global_id(type_name, id_)
            for id_ in catalogue_info[catalogue_field]
        )
    return converted_catalogue_info


class CatalogueInput(graphene.InputObjectType):
    products = NonNullList(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    categories = NonNullList(
        graphene.ID,
        description="Categories related to the discount.",
        name="categories",
    )
    collections = NonNullList(
        graphene.ID,
        description="Collections related to the discount.",
        name="collections",
    )
    variants = NonNullList(
        graphene.ID,
        description="Product variant related to the discount." + ADDED_IN_31,
        name="variants",
    )


class BaseDiscountCatalogueMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def recalculate_discounted_prices(cls, products, categories, collections, variants):
        update_products_discounted_prices_of_catalogues_task.delay(
            product_ids=[p.pk for p in products],
            category_ids=[c.pk for c in categories],
            collection_ids=[c.pk for c in collections],
            variant_ids=[v.pk for v in variants],
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
        variants = input.get("variants", [])
        if variants:
            variants = cls.get_nodes_or_error(variants, "variants", ProductVariant)
            node.variants.add(*variants)
        # Updated the db entries, recalculating discounts of affected products
        cls.recalculate_discounted_prices(products, categories, collections, variants)

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
        variants = input.get("variants", [])
        if variants:
            variants = cls.get_nodes_or_error(variants, "variants", ProductVariant)
            node.variants.remove(*variants)
        # Updated the db entries, recalculating discounts of affected products
        cls.recalculate_discounted_prices(products, categories, collections, variants)


class VoucherInput(graphene.InputObjectType):
    type = VoucherTypeEnum(
        description="Voucher type: PRODUCT, CATEGORY SHIPPING or ENTIRE_ORDER."
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
    products = NonNullList(
        graphene.ID, description="Products discounted by the voucher.", name="products"
    )
    variants = NonNullList(
        graphene.ID,
        description="Variants discounted by the voucher." + ADDED_IN_31,
        name="variants",
    )
    collections = NonNullList(
        graphene.ID,
        description="Collections discounted by the voucher.",
        name="collections",
    )
    categories = NonNullList(
        graphene.ID,
        description="Categories discounted by the voucher.",
        name="categories",
    )
    min_checkout_items_quantity = graphene.Int(
        description="Minimal quantity of checkout items required to apply the voucher."
    )
    countries = NonNullList(
        graphene.String,
        description="Country codes that can be used with the shipping voucher.",
    )
    apply_once_per_order = graphene.Boolean(
        description="Voucher should be applied to the cheapest item or entire order."
    )
    apply_once_per_customer = graphene.Boolean(
        description="Voucher should be applied once per customer."
    )
    only_for_staff = graphene.Boolean(
        description="Voucher can be used only by staff user."
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
        object_type = Voucher
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

        return cleaned_input

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        start_date = instance.start_date
        end_date = instance.end_date
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = DiscountErrorCode.INVALID.value
            raise ValidationError({"end_date": error})

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.voucher_created(instance)


class VoucherUpdate(VoucherCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to update.")
        input = VoucherInput(
            required=True, description="Fields required to update a voucher."
        )

    class Meta:
        description = "Updates a voucher."
        model = models.Voucher
        object_type = Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.voucher_updated(instance)


class VoucherDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to delete.")

    class Meta:
        description = "Deletes a voucher."
        model = models.Voucher
        object_type = Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(instance)
        return response

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.voucher_deleted(instance)


class VoucherBaseCatalogueMutation(BaseDiscountCatalogueMutation):
    voucher = graphene.Field(
        Voucher, description="Voucher of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher.")
        input = CatalogueInput(
            required=True,
            description="Fields required to modify catalogue IDs of voucher.",
        )

    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info, **data):
        response = super().mutate(root, info, **data)
        if response.voucher:
            response.voucher = ChannelContext(node=response.voucher, channel_slug=None)
        return response


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
        input_data = data.get("input", {})
        cls.add_catalogues_to_node(voucher, input_data)

        if input_data:
            info.context.plugins.voucher_updated(voucher)

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
        input_data = data.get("input", {})
        cls.remove_catalogues_from_node(voucher, input_data)

        if input_data:
            info.context.plugins.voucher_updated(voucher)

        return VoucherRemoveCatalogues(voucher=voucher)


class VoucherChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    discount_value = PositiveDecimal(description="Value of the voucher.")
    min_amount_spent = PositiveDecimal(
        description="Min purchase amount required to apply the voucher."
    )


class VoucherChannelListingInput(graphene.InputObjectType):
    add_channels = NonNullList(
        VoucherChannelListingAddInput,
        description="List of channels to which the voucher should be assigned.",
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels from which the voucher should be unassigned.",
        required=False,
    )


class VoucherChannelListingUpdate(BaseChannelListingMutation):
    voucher = graphene.Field(Voucher, description="An updated voucher instance.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to update.")
        input = VoucherChannelListingInput(
            required=True,
            description="Fields required to update voucher channel listings.",
        )

    class Meta:
        description = "Manage voucher's availability in channels."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def clean_discount_values_per_channel(cls, cleaned_input, voucher, error_dict):
        channel_slugs_assigned_to_voucher = voucher.channel_listings.values_list(
            "channel__slug", flat=True
        )

        for cleaned_channel in cleaned_input.get("add_channels", []):
            channel = cleaned_channel.get("channel", None)
            if not channel:
                continue
            discount_value = cleaned_channel.get("discount_value", "")
            # New channel listing requires discout value. It raises validation error for
            # `discout_value` == `None`.
            # Updating channel listing doesn't require to pass `discout_value`.
            should_create = channel.slug not in channel_slugs_assigned_to_voucher
            missing_required_value = not discount_value and should_create
            if missing_required_value or discount_value is None:
                error_dict["channels_without_value"].append(
                    cleaned_channel["channel_id"]
                )
            # Validate value precision if it is fixed amount voucher
            if voucher.discount_value_type == DiscountValueType.FIXED:
                try:
                    validate_price_precision(discount_value, channel.currency_code)
                except ValidationError:
                    error_dict["channels_with_invalid_value_precision"].append(
                        cleaned_channel["channel_id"]
                    )
            elif voucher.discount_value_type == DiscountValueType.PERCENTAGE:
                if discount_value > 100:
                    error_dict["channels_with_invalid_percentage_value"].append(
                        cleaned_channel["channel_id"]
                    )

            min_amount_spent = cleaned_channel.get("min_amount_spent", None)
            if min_amount_spent:
                try:
                    validate_price_precision(min_amount_spent, channel.currency_code)
                except ValidationError:
                    error_dict[
                        "channels_with_invalid_min_amount_spent_precision"
                    ].append(cleaned_channel["channel_id"])

    @classmethod
    def clean_discount_values(cls, cleaned_input, voucher, errors):
        error_dict = {
            "channels_without_value": [],
            "channels_with_invalid_value_precision": [],
            "channels_with_invalid_percentage_value": [],
            "channels_with_invalid_min_amount_spent_precision": [],
        }
        cls.clean_discount_values_per_channel(
            cleaned_input,
            voucher,
            error_dict,
        )
        channels_without_value = error_dict["channels_without_value"]
        if channels_without_value:
            errors["discount_value"].append(
                ValidationError(
                    "Value is required for voucher.",
                    code=DiscountErrorCode.REQUIRED.value,
                    params={"channels": channels_without_value},
                )
            )

        channels_with_invalid_value_precision = error_dict[
            "channels_with_invalid_value_precision"
        ]
        if channels_with_invalid_value_precision:
            errors["discount_value"].append(
                ValidationError(
                    "Invalid amount precision.",
                    code=DiscountErrorCode.INVALID.value,
                    params={"channels": channels_with_invalid_value_precision},
                )
            )

        channels_with_invalid_percentage_value = error_dict[
            "channels_with_invalid_percentage_value"
        ]
        if channels_with_invalid_percentage_value:
            errors["discount_value"].append(
                ValidationError(
                    "Invalid percentage value.",
                    code=DiscountErrorCode.INVALID.value,
                    params={"channels": channels_with_invalid_percentage_value},
                )
            )

        channels_with_invalid_min_amount_spent_precision = error_dict[
            "channels_with_invalid_min_amount_spent_precision"
        ]
        if channels_with_invalid_min_amount_spent_precision:
            errors["min_amount_spent"].append(
                ValidationError(
                    "Invalid amount precision.",
                    code=DiscountErrorCode.INVALID.value,
                    params={
                        "channels": channels_with_invalid_min_amount_spent_precision
                    },
                )
            )
        return cleaned_input

    @classmethod
    def add_channels(cls, voucher, add_channels):
        for add_channel in add_channels:
            channel = add_channel["channel"]
            defaults = {"currency": channel.currency_code}
            if "discount_value" in add_channel.keys():
                defaults["discount_value"] = add_channel.get("discount_value")
            if "min_amount_spent" in add_channel.keys():
                defaults["min_spent_amount"] = add_channel.get("min_amount_spent", None)
            models.VoucherChannelListing.objects.update_or_create(
                voucher=voucher,
                channel=channel,
                defaults=defaults,
            )

    @classmethod
    def remove_channels(cls, voucher, remove_channels):
        voucher.channel_listings.filter(channel_id__in=remove_channels).delete()

    @classmethod
    @traced_atomic_transaction()
    def save(cls, voucher, cleaned_input):
        cls.add_channels(voucher, cleaned_input.get("add_channels", []))
        cls.remove_channels(voucher, cleaned_input.get("remove_channels", []))

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        voucher = cls.get_node_or_error(info, id, only_type=Voucher, field="id")
        errors = defaultdict(list)
        cleaned_input = cls.clean_channels(
            info, input, errors, DiscountErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        cleaned_input = cls.clean_discount_values(cleaned_input, voucher, errors)

        if errors:
            raise ValidationError(errors)

        cls.save(voucher, cleaned_input)
        info.context.plugins.voucher_updated(voucher)

        return VoucherChannelListingUpdate(
            voucher=ChannelContext(node=voucher, channel_slug=None)
        )


class SaleInput(graphene.InputObjectType):
    name = graphene.String(description="Voucher name.")
    type = DiscountValueTypeEnum(description="Fixed or percentage.")
    value = PositiveDecimal(description="Value of the voucher.")
    products = NonNullList(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    variants = NonNullList(
        graphene.ID,
        descriptions="Product variant related to the discount." + ADDED_IN_31,
        name="variants",
    )
    categories = NonNullList(
        graphene.ID,
        description="Categories related to the discount.",
        name="categories",
    )
    collections = NonNullList(
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
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        start_date = instance.start_date
        end_date = instance.end_date
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = DiscountErrorCode.INVALID.value
            raise ValidationError({"end_date": error})

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        instance = getattr(response, cls._meta.return_field_name).node
        current_catalogue = fetch_catalogue_info(instance)

        transaction.on_commit(
            lambda: info.context.plugins.sale_created(
                instance,
                convert_catalogue_info_to_global_ids(current_catalogue),
            )
        )
        return response


class SaleUpdate(SaleUpdateDiscountedPriceMixin, ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleInput(
            required=True, description="Fields required to update a sale."
        )

    class Meta:
        description = "Updates a sale."
        model = models.Sale
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=Sale)
        previous_catalogue = fetch_catalogue_info(instance)
        response = super().perform_mutation(_root, info, **data)
        current_catalogue = fetch_catalogue_info(instance)
        transaction.on_commit(
            lambda: info.context.plugins.sale_updated(
                instance,
                convert_catalogue_info_to_global_ids(previous_catalogue),
                convert_catalogue_info_to_global_ids(current_catalogue),
            )
        )
        return response


class SaleDelete(SaleUpdateDiscountedPriceMixin, ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to delete.")

    class Meta:
        description = "Deletes a sale."
        model = models.Sale
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=Sale)
        previous_catalogue = fetch_catalogue_info(instance)
        response = super().perform_mutation(_root, info, **data)

        transaction.on_commit(
            lambda: info.context.plugins.sale_deleted(
                instance, convert_catalogue_info_to_global_ids(previous_catalogue)
            )
        )
        return response


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
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        sale = cls.get_node_or_error(
            info, data.get("id"), only_type=Sale, field="sale_id"
        )
        previous_catalogue = fetch_catalogue_info(sale)
        cls.add_catalogues_to_node(sale, data.get("input"))
        current_catalogue = fetch_catalogue_info(sale)

        transaction.on_commit(
            lambda: info.context.plugins.sale_updated(
                sale,
                previous_catalogue=convert_catalogue_info_to_global_ids(
                    previous_catalogue
                ),
                current_catalogue=convert_catalogue_info_to_global_ids(
                    current_catalogue
                ),
            )
        )

        return SaleAddCatalogues(sale=ChannelContext(node=sale, channel_slug=None))


class SaleRemoveCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = "Removes products, categories, collections from a sale."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        sale = cls.get_node_or_error(
            info, data.get("id"), only_type=Sale, field="sale_id"
        )
        previous_catalogue = fetch_catalogue_info(sale)
        cls.remove_catalogues_from_node(sale, data.get("input"))
        current_catalogue = fetch_catalogue_info(sale)

        transaction.on_commit(
            lambda: info.context.plugins.sale_updated(
                sale,
                previous_catalogue=convert_catalogue_info_to_global_ids(
                    previous_catalogue
                ),
                current_catalogue=convert_catalogue_info_to_global_ids(
                    current_catalogue
                ),
            )
        )

        return SaleRemoveCatalogues(sale=ChannelContext(node=sale, channel_slug=None))


class SaleChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    discount_value = PositiveDecimal(
        required=True, description="The value of the discount."
    )


class SaleChannelListingInput(graphene.InputObjectType):
    add_channels = NonNullList(
        SaleChannelListingAddInput,
        description="List of channels to which the sale should be assigned.",
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
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
            channel = add_channel["channel"]
            defaults = {"currency": channel.currency_code}
            channel = add_channel["channel"]
            if "discount_value" in add_channel.keys():
                defaults["discount_value"] = add_channel.get("discount_value")
            SaleChannelListing.objects.update_or_create(
                sale=sale,
                channel=channel,
                defaults=defaults,
            )

    @classmethod
    def clean_discount_values(cls, cleaned_channels, sale_type, errors, error_code):
        channels_with_invalid_value_precision = []
        channels_with_invalid_percentage_value = []
        for cleaned_channel in cleaned_channels.get("add_channels", []):
            channel = cleaned_channel["channel"]
            currency_code = channel.currency_code
            discount_value = cleaned_channel.get("discount_value")
            if not discount_value:
                continue
            if sale_type == DiscountValueType.FIXED:
                try:
                    validate_price_precision(discount_value, currency_code)
                except ValidationError:
                    channels_with_invalid_value_precision.append(
                        cleaned_channel["channel_id"]
                    )
            elif sale_type == DiscountValueType.PERCENTAGE:
                if discount_value > 100:
                    channels_with_invalid_percentage_value.append(
                        cleaned_channel["channel_id"]
                    )

        if channels_with_invalid_value_precision:
            errors["input"].append(
                ValidationError(
                    "Invalid amount precision.",
                    code=error_code,
                    params={"channels": channels_with_invalid_value_precision},
                )
            )
        if channels_with_invalid_percentage_value:
            errors["input"].append(
                ValidationError(
                    "Invalid percentage value.",
                    code=error_code,
                    params={"channels": channels_with_invalid_percentage_value},
                )
            )
        return cleaned_channels

    @classmethod
    def remove_channels(cls, sale: "SaleModel", remove_channels: List[int]):
        sale.channel_listings.filter(channel_id__in=remove_channels).delete()

    @classmethod
    @traced_atomic_transaction()
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
        cleaned_input = cls.clean_discount_values(
            cleaned_channels, sale.type, errors, DiscountErrorCode.INVALID.value
        )

        if errors:
            raise ValidationError(errors)

        cls.save(info, sale, cleaned_input)

        # Invalidate dataloader for channel listings
        SaleChannelListingBySaleIdLoader(info.context).clear(sale.id)

        return SaleChannelListingUpdate(
            sale=ChannelContext(node=sale, channel_slug=None)
        )
