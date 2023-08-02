from collections import defaultdict
from typing import List, Tuple

import graphene
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .....attribute import AttributeInputType
from .....attribute import models as attribute_models
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from .....product.search import update_product_search_vector
from .....product.tasks import update_product_discounted_price_task
from .....product.utils.variants import generate_and_set_variant_name
from ....attribute.types import AttributeValueInput
from ....attribute.utils import AttributeAssignmentMixin, AttrValuesInput
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_31, ADDED_IN_38, ADDED_IN_310
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import ModelMutation
from ....core.scalars import WeightScalar
from ....core.types import BaseInputObjectType, NonNullList, ProductError
from ....core.utils import get_duplicated_values
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ....shop.utils import get_track_inventory_by_default
from ....warehouse.types import Warehouse
from ...types import ProductVariant
from ...utils import (
    clean_variant_sku,
    create_stocks,
    get_used_variants_attribute_values,
)
from ..product.product_create import StockInput

T_INPUT_MAP = List[Tuple[attribute_models.Attribute, AttrValuesInput]]


class PreorderSettingsInput(BaseInputObjectType):
    global_threshold = graphene.Int(
        description="The global threshold for preorder variant."
    )
    end_date = graphene.DateTime(description="The end date for preorder.")

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductVariantInput(BaseInputObjectType):
    attributes = NonNullList(
        AttributeValueInput,
        required=False,
        description="List of attributes specific to this variant.",
    )
    sku = graphene.String(description="Stock keeping unit.")
    name = graphene.String(description="Variant name.", required=False)
    track_inventory = graphene.Boolean(
        description=(
            "Determines if the inventory of this variant should be tracked. If false, "
            "the quantity won't change when customers buy this item. "
            "If the field is not provided, `Shop.trackInventoryByDefault` will be used."
        )
    )
    weight = WeightScalar(description="Weight of the Product Variant.", required=False)
    preorder = PreorderSettingsInput(
        description=("Determines if variant is in preorder." + ADDED_IN_31)
    )
    quantity_limit_per_customer = graphene.Int(
        required=False,
        description=(
            "Determines maximum quantity of `ProductVariant`,"
            "that can be bought in a single checkout." + ADDED_IN_31
        ),
    )
    metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the product variant metadata." + ADDED_IN_38
        ),
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the product variant private metadata."
            + ADDED_IN_38
        ),
        required=False,
    )
    external_reference = graphene.String(
        description="External ID of this product variant." + ADDED_IN_310,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductVariantCreateInput(ProductVariantInput):
    attributes = NonNullList(
        AttributeValueInput,
        required=True,
        description="List of attributes specific to this variant.",
    )
    product = graphene.ID(
        description="Product ID of which type is the variant.",
        name="product",
        required=True,
    )
    stocks = NonNullList(
        StockInput,
        description="Stocks of a product available for sale.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductVariantCreate(ModelMutation):
    class Arguments:
        input = ProductVariantCreateInput(
            required=True, description="Fields required to create a product variant."
        )

    class Meta:
        description = "Creates a new variant for a product."
        model = models.ProductVariant
        object_type = ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        errors_mapping = {"price_amount": "price"}
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.variant_attributes.all()
        attributes = AttributeAssignmentMixin.clean_input(attributes, attributes_qs)
        return attributes

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes_data, used_attribute_values, instance=None
    ):
        attribute_values = defaultdict(list)
        for attr, attr_data in attributes_data:
            if attr.input_type == AttributeInputType.FILE:
                values = (
                    [slugify(attr_data.file_url.split("/")[-1])]
                    if attr_data.file_url
                    else []
                )
            else:
                values = attr_data.values
            attribute_values[attr_data.global_id].extend(values)
        if attribute_values in used_attribute_values:
            raise ValidationError(
                "Duplicated attribute values for product variant.",
                code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                params={"attributes": attribute_values.keys()},
            )
        else:
            used_attribute_values.append(attribute_values)

    @classmethod
    def clean_input(
        cls,
        info: ResolveInfo,
        instance: models.ProductVariant,
        data: dict,
        **kwargs,
    ):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        weight = cleaned_input.get("weight")
        if weight and weight.value < 0:
            raise ValidationError(
                {
                    "weight": ValidationError(
                        "Product variant can't have negative weight.",
                        code=ProductErrorCode.INVALID.value,
                    )
                }
            )

        quantity_limit_per_customer = cleaned_input.get("quantity_limit_per_customer")
        if quantity_limit_per_customer is not None and quantity_limit_per_customer < 1:
            raise ValidationError(
                {
                    "quantity_limit_per_customer": ValidationError(
                        (
                            "Product variant can't have "
                            "quantity_limit_per_customer lower than 1."
                        ),
                        code=ProductErrorCode.INVALID.value,
                    )
                }
            )

        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.check_for_duplicates_in_stocks(stocks)

        if instance.pk:
            # If the variant is getting updated,
            # simply retrieve the associated product type
            product_type = instance.product.product_type
            used_attribute_values = get_used_variants_attribute_values(instance.product)
        else:
            # If the variant is getting created, no product type is associated yet,
            # retrieve it from the required "product" input field
            product_type = cleaned_input["product"].product_type
            used_attribute_values = get_used_variants_attribute_values(
                cleaned_input["product"]
            )

        variant_attributes_ids = {
            graphene.Node.to_global_id("Attribute", attr_id)
            for attr_id in list(
                product_type.variant_attributes.all().values_list("pk", flat=True)
            )
        }
        attributes = cleaned_input.get("attributes")
        attributes_ids = {attr["id"] for attr in attributes or []}
        invalid_attributes = attributes_ids - variant_attributes_ids
        if len(invalid_attributes) > 0:
            raise ValidationError(
                "Given attributes are not a variant attributes.",
                code=ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.value,
                params={"attributes": invalid_attributes},
            )

        # Run the validation only if product type is configurable
        if product_type.has_variants:
            # Attributes are provided as list of `AttributeValueInput` objects.
            # We need to transform them into the format they're stored in the
            # `Product` model, which is HStore field that maps attribute's PK to
            # the value's PK.
            try:
                if attributes:
                    cleaned_attributes = cls.clean_attributes(attributes, product_type)
                    cls.validate_duplicated_attribute_values(
                        cleaned_attributes, used_attribute_values, instance
                    )
                    cleaned_input["attributes"] = cleaned_attributes
                # elif not instance.pk and not attributes:
                elif not instance.pk and (
                    not attributes
                    and product_type.variant_attributes.filter(value_required=True)
                ):
                    # if attributes were not provided on creation
                    raise ValidationError(
                        "All required attributes must take a value.",
                        ProductErrorCode.REQUIRED.value,
                    )
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})
        else:
            if attributes:
                raise ValidationError(
                    "Cannot assign attributes for product type without variants",
                    ProductErrorCode.INVALID.value,
                )

        if "sku" in cleaned_input:
            cleaned_input["sku"] = clean_variant_sku(cleaned_input.get("sku"))

        preorder_settings = cleaned_input.get("preorder")
        if preorder_settings:
            cleaned_input["is_preorder"] = True
            cleaned_input["preorder_global_threshold"] = preorder_settings.get(
                "global_threshold"
            )
            cleaned_input["preorder_end_date"] = preorder_settings.get("end_date")

        return cleaned_input

    @classmethod
    def check_for_duplicates_in_stocks(cls, stocks_data):
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]
        duplicates = get_duplicated_values(warehouse_ids)
        if duplicates:
            error_msg = "Duplicated warehouse ID: {}".format(", ".join(duplicates))
            raise ValidationError(
                {
                    "stocks": ValidationError(
                        error_msg, code=ProductErrorCode.UNIQUE.value
                    )
                }
            )

    @classmethod
    def set_track_inventory(cls, _info, instance, cleaned_input):
        track_inventory_by_default = get_track_inventory_by_default(_info)
        track_inventory = cleaned_input.get("track_inventory")
        if track_inventory_by_default is not None:
            instance.track_inventory = (
                track_inventory_by_default
                if track_inventory is None
                else track_inventory
            )

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        new_variant = instance.pk is None
        cls.set_track_inventory(info, instance, cleaned_input)
        with traced_atomic_transaction():
            instance.save()
            if not instance.product.default_variant:
                instance.product.default_variant = instance
                instance.product.save(update_fields=["default_variant", "updated_at"])
            # Recalculate the "discounted price" for the parent product
            update_product_discounted_price_task.delay(instance.product_id)
            stocks = cleaned_input.get("stocks")
            if stocks:
                cls.create_variant_stocks(instance, stocks)
            attributes = cleaned_input.get("attributes")
            if attributes:
                AttributeAssignmentMixin.save(instance, attributes)

            if not instance.name:
                generate_and_set_variant_name(instance, cleaned_input.get("sku"))

            manager = get_plugin_manager_promise(info.context).get()
            update_product_search_vector(instance.product)
            event_to_call = (
                manager.product_variant_created
                if new_variant
                else manager.product_variant_updated
            )
            cls.call_event(event_to_call, instance)

    @classmethod
    def create_variant_stocks(cls, variant, stocks):
        warehouse_ids = [stock["warehouse"] for stock in stocks]
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        create_stocks(variant, stocks, warehouses)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)
