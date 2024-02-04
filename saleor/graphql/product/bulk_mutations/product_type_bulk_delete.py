import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductTypePermissions
from ....product import models
from ...core import ResolveInfo
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, ProductError
from ..types import ProductType


class ProductTypeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of product type IDs to delete.",
        )

    class Meta:
        description = "Deletes product types."
        model = models.ProductType
        object_type = ProductType
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, ids
    ):
        try:
            pks = cls.get_global_ids_or_error(ids, ProductType)
        except ValidationError as error:
            return 0, error
        cls.delete_assigned_attribute_values(pks)
        return super().perform_mutation(_root, info, ids=ids)

    @staticmethod
    def delete_assigned_attribute_values(instance_pks):
        attributes = attribute_models.Attribute.objects.filter(
            input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES
        )
        assigned_values = attribute_models.AssignedProductAttributeValue.objects.filter(
            product__product_type_id__in=instance_pks
        )
        attribute_models.AttributeValue.objects.filter(
            Exists(attributes.filter(id=OuterRef("attribute_id"))),
            (
                Q(Exists(assigned_values.filter(value_id=OuterRef("id"))))
                | Q(variantassignments__assignment__product_type_id__in=instance_pks)
            ),
        ).delete()
