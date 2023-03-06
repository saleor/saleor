from typing import List, Tuple

import graphene

from .....attribute import models as attribute_models
from .....core.permissions import ProductPermissions
from .....core.tracing import traced_atomic_transaction
from .....product import models
from .....product.search import update_product_search_vector
from ....attribute.utils import AttributeAssignmentMixin, AttrValuesInput
from ....core.types.common import ProductError
from ....plugins.dataloaders import load_plugin_manager
from ...types import Product
from .product_create import ProductCreate, ProductInput

T_INPUT_MAP = List[Tuple[attribute_models.Attribute, AttrValuesInput]]


class ProductUpdate(ProductCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to update.")
        input = ProductInput(
            required=True, description="Fields required to update a product."
        )

    class Meta:
        description = "Updates an existing product."
        model = models.Product
        object_type = Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.product_attributes.all()
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, creation=False
        )
        return attributes

    @classmethod
    def save(cls, info, instance, cleaned_input):
        with traced_atomic_transaction():
            instance.save()
            attributes = cleaned_input.get("attributes")
            if attributes:
                AttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        product = models.Product.objects.prefetched_for_webhook().get(pk=instance.pk)
        update_product_search_vector(instance)
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.product_updated, product)
