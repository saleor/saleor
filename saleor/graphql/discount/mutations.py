import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import DiscountPermissions
from ...core.utils.promo_code import generate_promo_code, is_available_promo_code
from ...discount import models
from ...discount.error_codes import DiscountErrorCode
from ...product.tasks import (
    update_products_minimal_variant_prices_of_catalogues_task,
    update_products_minimal_variant_prices_of_discount_task,
)
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.scalars import Decimal
from ..core.types.common import DiscountError
from ..product.types import Category, Collection, Product
from .enums import DiscountValueTypeEnum, VoucherTypeEnum
from .types import Sale, Voucher


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
    def recalculate_minimal_prices(cls, products, categories, collections):
        update_products_minimal_variant_prices_of_catalogues_task.delay(
            product_ids=[p.pk for p in products],
            category_ids=[c.pk for c in categories],
            collection_ids=[c.pk for c in collections],
        )

    @classmethod
    def add_catalogues_to_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
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
        cls.recalculate_minimal_prices(products, categories, collections)

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
        cls.recalculate_minimal_prices(products, categories, collections)


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
    discount_value = Decimal(description="Value of the voucher.")
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
    min_amount_spent = Decimal(
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
    value = Decimal(description="Value of the voucher.")
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


class SaleUpdateMinimalVariantPriceMixin:
    @classmethod
    def success_response(cls, instance):
        # Update the "minimal_variant_prices" of the associated, discounted
        # products (including collections and categories).
        update_products_minimal_variant_prices_of_discount_task.delay(instance.pk)
        return super().success_response(instance)


class SaleCreate(SaleUpdateMinimalVariantPriceMixin, ModelMutation):
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


class SaleUpdate(SaleUpdateMinimalVariantPriceMixin, ModelMutation):
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


class SaleDelete(SaleUpdateMinimalVariantPriceMixin, ModelDeleteMutation):
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
        return SaleAddCatalogues(sale=sale)


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
        return SaleRemoveCatalogues(sale=sale)
