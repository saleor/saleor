from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import ProductPermissions
from ....product import models
from ....product.error_codes import ProductErrorCode
from ....product.tasks import update_product_minimal_variant_price_task
from ....product.utils import delete_categories
from ....product.utils.attributes import generate_name_for_variant
from ....warehouse import models as warehouse_models
from ....warehouse.error_codes import StockErrorCode
from ...core.mutations import (
    BaseBulkMutation,
    BaseMutation,
    ModelBulkDeleteMutation,
    ModelMutation,
)
from ...core.types.common import (
    BulkProductError,
    BulkStockError,
    ProductError,
    StockError,
)
from ...core.utils import get_duplicated_values
from ...utils import resolve_global_ids_to_primary_keys
from ...warehouse.types import Warehouse
from ..mutations.products import (
    AttributeAssignmentMixin,
    AttributeValueInput,
    ProductVariantCreate,
    ProductVariantInput,
    StockInput,
)
from ..types import ProductVariant
from ..utils import create_stocks, get_used_variants_attribute_values


class CategoryBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of category IDs to delete."
        )

    class Meta:
        description = "Deletes categories."
        model = models.Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def bulk_action(cls, queryset):
        delete_categories(queryset.values_list("pk", flat=True))


class CollectionBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of collection IDs to delete."
        )

    class Meta:
        description = "Deletes collections."
        model = models.Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class CollectionBulkPublish(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description="List of collections IDs to (un)publish.",
        )
        is_published = graphene.Boolean(
            required=True,
            description="Determine if collections will be published or not.",
        )

    class Meta:
        description = "Publish collections."
        model = models.Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def bulk_action(cls, queryset, is_published):
        queryset.update(is_published=is_published)


class ProductBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of product IDs to delete."
        )

    class Meta:
        description = "Deletes products."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductVariantBulkCreateInput(ProductVariantInput):
    attributes = graphene.List(
        AttributeValueInput,
        required=True,
        description="List of attributes specific to this variant.",
    )
    stocks = graphene.List(
        graphene.NonNull(StockInput),
        description=("Stocks of a product available for sale."),
        required=False,
    )
    sku = graphene.String(required=True, description="Stock keeping unit.")


class ProductVariantBulkCreate(BaseMutation):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were created.",
    )
    product_variants = graphene.List(
        graphene.NonNull(ProductVariant),
        required=True,
        default_value=[],
        description="List of the created variants.",
    )

    class Arguments:
        variants = graphene.List(
            ProductVariantBulkCreateInput,
            required=True,
            description="Input list of product variants to create.",
        )
        product_id = graphene.ID(
            description="ID of the product to create the variants for.",
            name="product",
            required=True,
        )

    class Meta:
        description = "Creates product variants for a given product."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkProductError
        error_type_field = "bulk_product_errors"

    @classmethod
    def clean_variant_input(
        cls,
        info,
        instance: models.ProductVariant,
        data: dict,
        errors: dict,
        variant_index: int,
    ):
        cleaned_input = ModelMutation.clean_input(
            info, instance, data, input_cls=ProductVariantBulkCreateInput
        )

        cost_price_amount = cleaned_input.pop("cost_price", None)
        if cost_price_amount is not None:
            if cost_price_amount < 0:
                errors["costPrice"] = ValidationError(
                    "Product price cannot be lower than 0.",
                    code=ProductErrorCode.INVALID.value,
                    params={"index": variant_index},
                )
            cleaned_input["cost_price_amount"] = cost_price_amount

        price_override_amount = cleaned_input.pop("price_override", None)
        if price_override_amount is not None:
            if price_override_amount < 0:
                errors["priceOverride"] = ValidationError(
                    "Product price cannot be lower than 0.",
                    code=ProductErrorCode.INVALID.value,
                    params={"index": variant_index},
                )
            cleaned_input["price_override_amount"] = price_override_amount

        attributes = cleaned_input.get("attributes")
        if attributes:
            try:
                cleaned_input["attributes"] = ProductVariantCreate.clean_attributes(
                    attributes, data["product_type"]
                )
            except ValidationError as exc:
                exc.params = {"index": variant_index}
                errors["attributes"] = exc

        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.clean_stocks(stocks, errors, variant_index)

        return cleaned_input

    @classmethod
    def clean_stocks(cls, stocks_data, errors, variant_index):
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]
        duplicates = get_duplicated_values(warehouse_ids)
        if duplicates:
            errors["stocks"] = ValidationError(
                "Duplicated warehouse ID.",
                code=ProductErrorCode.DUPLICATED_INPUT_ITEM,
                params={"warehouses": duplicates, "index": variant_index},
            )

    @classmethod
    def add_indexes_to_errors(cls, index, error, error_dict):
        """Append errors with index in params to mutation error dict."""
        for key, value in error.error_dict.items():
            for e in value:
                if e.params:
                    e.params["index"] = index
                else:
                    e.params = {"index": index}
            error_dict[key].extend(value)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)
            instance.name = generate_name_for_variant(instance)
            instance.save(update_fields=["name"])

    @classmethod
    def create_variants(cls, info, cleaned_inputs, product, errors):
        instances = []
        for index, cleaned_input in enumerate(cleaned_inputs):
            if not cleaned_input:
                continue
            try:
                instance = models.ProductVariant()
                cleaned_input["product"] = product
                instance = cls.construct_instance(instance, cleaned_input)
                cls.clean_instance(info, instance)
                instances.append(instance)
            except ValidationError as exc:
                cls.add_indexes_to_errors(index, exc, errors)
        return instances

    @classmethod
    def validate_duplicated_sku(cls, sku, index, sku_list, errors):
        if sku in sku_list:
            errors["sku"].append(
                ValidationError(
                    "Duplicated SKU.", ProductErrorCode.UNIQUE, params={"index": index}
                )
            )
        sku_list.append(sku)

    @classmethod
    def clean_variants(cls, info, variants, product, errors):
        cleaned_inputs = []
        sku_list = []
        used_attribute_values = get_used_variants_attribute_values(product)
        for index, variant_data in enumerate(variants):
            try:
                ProductVariantCreate.validate_duplicated_attribute_values(
                    variant_data.attributes, used_attribute_values
                )
            except ValidationError as exc:
                errors["attributes"].append(
                    ValidationError(exc.message, exc.code, params={"index": index})
                )

            cleaned_input = None
            variant_data["product_type"] = product.product_type
            cleaned_input = cls.clean_variant_input(
                info, None, variant_data, errors, index
            )

            cleaned_inputs.append(cleaned_input if cleaned_input else None)

            if not variant_data.sku:
                continue
            cls.validate_duplicated_sku(variant_data.sku, index, sku_list, errors)
        return cleaned_inputs

    @classmethod
    @transaction.atomic
    def save_variants(cls, info, instances, cleaned_inputs):
        assert len(instances) == len(
            cleaned_inputs
        ), "There should be the same number of instances and cleaned inputs."
        for instance, cleaned_input in zip(instances, cleaned_inputs):
            cls.save(info, instance, cleaned_input)
            cls.create_variant_stocks(instance, cleaned_input)

    @classmethod
    def create_variant_stocks(cls, variant, cleaned_input):
        stocks = cleaned_input.get("stocks")
        if not stocks:
            return
        warehouse_ids = [stock["warehouse"] for stock in stocks]
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        create_stocks(variant, stocks, warehouses)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        product = cls.get_node_or_error(info, data["product_id"], models.Product)
        errors = defaultdict(list)

        cleaned_inputs = cls.clean_variants(info, data["variants"], product, errors)
        instances = cls.create_variants(info, cleaned_inputs, product, errors)
        if errors:
            raise ValidationError(errors)
        cls.save_variants(info, instances, cleaned_inputs)

        # Recalculate the "minimal variant price" for the parent product
        update_product_minimal_variant_price_task.delay(product.pk)

        return ProductVariantBulkCreate(
            count=len(instances), product_variants=instances
        )


class ProductVariantBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description="List of product variant IDs to delete.",
        )

    class Meta:
        description = "Deletes product variants."
        model = models.ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductVariantStocksCreate(BaseMutation):
    product_variant = graphene.Field(
        ProductVariant, description="Updated product variant."
    )

    class Arguments:
        variant_id = graphene.ID(
            required=True,
            description="ID of a product variant for which stocks will be created.",
        )
        stocks = graphene.List(
            graphene.NonNull(StockInput),
            required=True,
            description="Input list of stocks to create.",
        )

    class Meta:
        description = "Creates stocks for product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkStockError
        error_type_field = "bulk_stock_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        errors = defaultdict(list)
        stocks = data["stocks"]
        variant = cls.get_node_or_error(
            info, data["variant_id"], only_type=ProductVariant
        )
        if stocks:
            warehouses = cls.clean_stocks_input(variant, stocks, errors)
            if errors:
                raise ValidationError(errors)
            create_stocks(variant, stocks, warehouses)
        return cls(product_variant=variant)

    @classmethod
    def clean_stocks_input(cls, variant, stocks_data, errors):
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]
        cls.check_for_duplicates(warehouse_ids, errors)
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        existing_stocks = variant.stocks.filter(warehouse__in=warehouses).values_list(
            "warehouse__pk", flat=True
        )
        error_msg = "Stock for this warehouse already exists for this product variant."
        indexes = []
        for warehouse_pk in existing_stocks:
            warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse_pk)
            indexes.extend(
                [i for i, id in enumerate(warehouse_ids) if id == warehouse_id]
            )
        cls.update_errors(
            errors, error_msg, "warehouse", StockErrorCode.UNIQUE, indexes
        )

        return warehouses

    @classmethod
    def check_for_duplicates(cls, warehouse_ids, errors):
        duplicates = {id for id in warehouse_ids if warehouse_ids.count(id) > 1}
        error_msg = "Duplicated warehouse ID."
        indexes = []
        for duplicated_id in duplicates:
            indexes.append(
                [i for i, id in enumerate(warehouse_ids) if id == duplicated_id][-1]
            )
        cls.update_errors(
            errors, error_msg, "warehouse", StockErrorCode.UNIQUE, indexes
        )

    @classmethod
    def update_errors(cls, errors, msg, field, code, indexes):
        for index in indexes:
            error = ValidationError(msg, code=code, params={"index": index})
            errors[field].append(error)


class ProductVariantStocksUpdate(ProductVariantStocksCreate):
    class Meta:
        description = "Update stocks for product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkStockError
        error_type_field = "bulk_stock_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        errors = defaultdict(list)
        stocks = data["stocks"]
        variant = cls.get_node_or_error(
            info, data["variant_id"], only_type=ProductVariant
        )
        warehouse_ids = [stock["warehouse"] for stock in stocks]
        cls.check_for_duplicates(warehouse_ids, errors)
        if errors:
            raise ValidationError(errors)
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        cls.update_or_create_variant_stocks(variant, stocks, warehouses)
        return cls(product_variant=variant)

    @classmethod
    @transaction.atomic
    def update_or_create_variant_stocks(cls, variant, stocks_data, warehouses):
        stocks = []
        for stock_data, warehouse in zip(stocks_data, warehouses):
            stock, _ = warehouse_models.Stock.objects.get_or_create(
                product_variant=variant, warehouse=warehouse
            )
            stock.quantity = stock_data["quantity"]
            stocks.append(stock)
        warehouse_models.Stock.objects.bulk_update(stocks, ["quantity"])


class ProductVariantStocksDelete(BaseMutation):
    product_variant = graphene.Field(
        ProductVariant, description="Updated product variant."
    )

    class Arguments:
        variant_id = graphene.ID(
            required=True,
            description="ID of product variant for which stocks will be deleted.",
        )
        warehouse_ids = graphene.List(graphene.NonNull(graphene.ID),)

    class Meta:
        description = "Delete stocks from product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = StockError
        error_type_field = "stock_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        variant = cls.get_node_or_error(
            info, data["variant_id"], only_type=ProductVariant
        )
        _, warehouses_pks = resolve_global_ids_to_primary_keys(
            data["warehouse_ids"], Warehouse
        )
        warehouse_models.Stock.objects.filter(
            product_variant=variant, warehouse__pk__in=warehouses_pks
        ).delete()
        return cls(product_variant=variant)


class ProductTypeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description="List of product type IDs to delete.",
        )

    class Meta:
        description = "Deletes product types."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductImageBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description="List of product image IDs to delete.",
        )

    class Meta:
        description = "Deletes product images."
        model = models.ProductImage
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductBulkPublish(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of products IDs to publish."
        )
        is_published = graphene.Boolean(
            required=True, description="Determine if products will be published or not."
        )

    class Meta:
        description = "Publish products."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def bulk_action(cls, queryset, is_published):
        queryset.update(is_published=is_published)
