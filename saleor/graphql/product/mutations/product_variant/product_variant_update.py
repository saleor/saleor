from collections import defaultdict
from typing import List, Tuple

import graphene
from django.utils.text import slugify

from .....attribute import AttributeInputType
from .....attribute import models as attribute_models
from .....core.permissions import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....attribute.utils import AttributeAssignmentMixin, AttrValuesInput
from ....core.descriptions import ADDED_IN_38
from ....core.types import ProductError
from ....core.validators import validate_one_of_args_is_in_mutation
from ...types import ProductVariant
from ...utils import get_used_attribute_values_for_variant
from .product_variant_create import ProductVariantCreate, ProductVariantInput

T_INPUT_MAP = List[Tuple[attribute_models.Attribute, AttrValuesInput]]


class ProductVariantUpdate(ProductVariantCreate):
    class Arguments:
        id = graphene.ID(
            required=False, description="ID of a product variant to update."
        )
        sku = graphene.String(
            required=False,
            description="SKU of a product variant to update." + ADDED_IN_38,
        )
        input = ProductVariantInput(
            required=True, description="Fields required to update a product variant."
        )

    class Meta:
        description = "Updates an existing variant for product."
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
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, creation=False
        )
        return attributes

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes_data, used_attribute_values, instance=None
    ):
        # Check if the variant is getting updated,
        # and the assigned attributes do not change
        if instance.product_id is not None:
            assigned_attributes = get_used_attribute_values_for_variant(instance)
            input_attribute_values = defaultdict(list)
            for attr, attr_data in attributes_data:
                if attr.input_type == AttributeInputType.FILE:
                    values = (
                        [slugify(attr_data.file_url.split("/")[-1])]
                        if attr_data.file_url
                        else []
                    )
                else:
                    values = attr_data.values
                input_attribute_values[attr_data.global_id].extend(values)
            if input_attribute_values == assigned_attributes:
                return
        # if assigned attributes is getting updated run duplicated attribute validation
        super().validate_duplicated_attribute_values(
            attributes_data, used_attribute_values
        )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        validate_one_of_args_is_in_mutation(
            ProductErrorCode, "sku", data.get("sku"), "id", data.get("id")
        )
        return super().perform_mutation(_root, info, **data)
