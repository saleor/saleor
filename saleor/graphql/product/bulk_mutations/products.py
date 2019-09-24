from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....product import models
from ....product.error_codes import ProductErrorCode
from ....product.tasks import update_product_minimal_variant_price_task
from ....product.utils.attributes import generate_name_for_variant
from ...core.mutations import BaseBulkMutation, ModelBulkDeleteMutation, ModelMutation
from ...core.types.common import ProductError
from ..mutations.products import (
    T_INPUT_MAP,
    AttributeAssignmentMixin,
    AttributeValueInput,
    ProductVariantInput,
)


class CategoryBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of category IDs to delete."
        )

    class Meta:
        description = "Deletes categories."
        model = models.Category
        permissions = ("product.manage_products",)
        error_type_class = ProductError
        error_type_field = "product_errors"


class CollectionBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of collection IDs to delete."
        )

    class Meta:
        description = "Deletes collections."
        model = models.Collection
        permissions = ("product.manage_products",)
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
        permissions = ("product.manage_products",)
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
        permissions = ("product.manage_products",)
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductVariantBulkCreateInput(ProductVariantInput):
    attributes = graphene.List(
        AttributeValueInput,
        required=True,
        description="List of attributes specific to this variant.",
    )


class ProductVariantBulkCreate(ModelMutation):
    count = graphene.Int(description="Returns how many objects were affected.")

    class Arguments:
        input = graphene.List(
            ProductVariantBulkCreateInput,
            required=True,
            description="Fields required to create a product variants.",
        )
        product_id = graphene.ID(
            description="Product ID of which type is the variant.",
            name="product",
            required=True,
        )

    class Meta:
        description = "Creates product variants."
        model = models.ProductVariant
        permissions = ("product.manage_products",)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.variant_attributes
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, is_variant=True
        )
        return attributes

    @classmethod
    def clean_input(cls, info, instance: models.ProductVariant, data: dict):
        cleaned_input = super().clean_input(
            info, instance, data, ProductVariantBulkCreateInput
        )

        cost_price_amount = cleaned_input.pop("cost_price", None)
        if cost_price_amount is not None:
            cleaned_input["cost_price_amount"] = cost_price_amount

        price_override_amount = cleaned_input.pop("price_override", None)
        if price_override_amount is not None:
            cleaned_input["price_override_amount"] = price_override_amount

        # Attributes are provided as list of `AttributeValueInput` objects.
        # We need to transform them into the format they're stored in the
        # `Product` model, which is HStore field that maps attribute's PK to
        # the value's PK.
        attributes = cleaned_input.get("attributes")
        if attributes:
            try:
                cleaned_input["attributes"] = cls.clean_attributes(
                    attributes, data["product_type"]
                )
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})

        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        # Recalculate the "minimal variant price" for the parent product
        update_product_minimal_variant_price_task.delay(instance.product_id)

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)
            instance.name = generate_name_for_variant(instance)
            instance.save(update_fields=["name"])

    @classmethod
    @transaction.atomic
    def save_instances(cls, info, instances, cleaned_inputs):
        for instance, cleaned_input in zip(instances, cleaned_inputs):
            cls.save(info, instance, cleaned_input)
            cls._save_m2m(info, instance, cleaned_input)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        product = cls.get_node_or_error(info, data.get("product_id"), models.Product)
        errors = defaultdict(list)
        instances = []
        cleaned_inputs = []
        sku_list = []
        product_type = product.product_type
        for variant_data in data.get("input"):
            try:
                instance = cls.get_instance(info, **variant_data)
                variant_data["product_type"] = product_type
                cleaned_input = cls.clean_input(info, instance, variant_data)
                cleaned_input["product"] = product
                instance = cls.construct_instance(instance, cleaned_input)
                cls.clean_instance(instance)
                instances.append(instance)
                cleaned_inputs.append(cleaned_input)
            except ValidationError as exc:
                for key, value in exc.error_dict.items():
                    errors[key].extend(value)
            sku = variant_data.get("sku")
            if sku:
                if sku not in sku_list:
                    sku_list.append(sku)
                else:
                    errors["sku"].append(
                        ValidationError(
                            "Duplicated SKU.", ProductErrorCode.ALREADY_EXISTS
                        )
                    )
        if not errors:
            cls.save_instances(info, instances, cleaned_inputs)
        else:
            raise ValidationError(errors)
        return ProductVariantBulkCreate(count=len(instances))


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
        permissions = ("product.manage_products",)
        error_type_class = ProductError
        error_type_field = "product_errors"


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
        permissions = ("product.manage_products",)
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
        permissions = ("product.manage_products",)
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
        permissions = ("product.manage_products",)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def bulk_action(cls, queryset, is_published):
        queryset.update(is_published=is_published)
