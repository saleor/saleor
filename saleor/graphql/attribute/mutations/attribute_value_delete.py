import graphene
from django.db.models import Exists, OuterRef, Q

from ....attribute import models as models
from ....core.permissions import ProductTypePermissions
from ....product import models as product_models
from ...core.mutations import ModelDeleteMutation
from ...core.types import AttributeError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Attribute, AttributeValue


class AttributeValueDelete(ModelDeleteMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a value to delete.")

    class Meta:
        model = models.AttributeValue
        object_type = AttributeValue
        description = "Deletes a value of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=AttributeValue)
        product_ids = cls.get_product_ids_to_update(instance)
        response = super().perform_mutation(_root, info, **data)
        product_models.Product.objects.filter(id__in=product_ids).update(
            search_index_dirty=True
        )
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.attribute_value_deleted, instance)
        cls.call_event(manager.attribute_updated, instance.attribute)
        return response

    @classmethod
    def get_product_ids_to_update(cls, instance):
        variants = product_models.ProductVariant.objects.filter(
            Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
        )
        product_ids = product_models.Product.objects.filter(
            Q(Exists(instance.productassignments.filter(product_id=OuterRef("id"))))
            | Q(Exists(variants.filter(product_id=OuterRef("id"))))
        ).values_list("id", flat=True)
        return list(product_ids)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response
