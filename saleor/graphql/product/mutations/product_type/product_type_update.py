import graphene

from .....core.permissions import ProductTypePermissions
from .....product import models
from .....product.tasks import update_variants_names
from ....core import ResolveInfo
from ....core.types import ProductError
from ...types import ProductType
from .product_type_create import ProductTypeCreate, ProductTypeInput


class ProductTypeUpdate(ProductTypeCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product type to update.")
        input = ProductTypeInput(
            required=True, description="Fields required to update a product type."
        )

    class Meta:
        description = "Updates an existing product type."
        model = models.ProductType
        object_type = ProductType
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_product_kind(cls, instance, data):
        return data.get("kind", instance.kind)

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        variant_attr = cleaned_input.get("variant_attributes")
        if variant_attr:
            variant_attr = set(variant_attr)
            variant_attr_ids = [attr.pk for attr in variant_attr]
            update_variants_names.delay(instance.pk, variant_attr_ids)
        super().save(info, instance, cleaned_input)

    @classmethod
    def post_save_action(cls, _info: ResolveInfo, instance, cleaned_input):
        if (
            "product_attributes" in cleaned_input
            or "variant_attributes" in cleaned_input
        ):
            models.Product.objects.filter(product_type=instance).update(
                search_index_dirty=True
            )
